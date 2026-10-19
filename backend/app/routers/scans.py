"""Security assessments and recurring scan schedules."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app import models, schemas, auth, audit, scheduler, worker

router = APIRouter()

# ============================================================
# Scans: NO verification gate, runs on all scopes
# ============================================================
@router.post("/scans", response_model=schemas.ScanOut)
def start_scan(
    scan_in: schemas.ScanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = db.query(models.Client).filter(models.Client.id == scan_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    scan = models.Scan(
        client_id=scan_in.client_id,
        requested_by_id=current_user.id,
        scan_type=scan_in.scan_type,
        status="running",
        configuration=json.dumps(scan_in.configuration) if scan_in.configuration else None,
    )
    from sqlalchemy.sql import func
    scan.started_at = func.now()
    db.add(scan)
    db.commit()
    db.refresh(scan)

    audit.log_action(
        db, "start_scan", user_id=current_user.id, client_id=scan_in.client_id,
        resource_type="scan", resource_id=str(scan.id),
        details={"scan_type": scan_in.scan_type},
    )
    return scan


@router.get("/scans", response_model=List[schemas.ScanOut])
def list_scans(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Scan)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.Scan.id.desc()).offset(offset).limit(min(limit, 500)).all()


@router.get("/scans/{scan_id}", response_model=schemas.ScanOut)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return scan


@router.post("/scans/{scan_id}/run")
def run_scan_endpoint(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # NO verification gate: runs on all non-excluded scopes
    return worker.execute_scan(db, scan, user_id=current_user.id)

# ============================================================
# Scan Schedules (recurring vulnerability scans)
# ============================================================
@router.post("/scan-schedules", response_model=schemas.ScanScheduleOut)
def create_scan_schedule(
    schedule_in: schemas.ScanScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client_obj = db.query(models.Client).filter(models.Client.id == schedule_in.client_id).first()
    if not client_obj:
        raise HTTPException(status_code=404, detail="Client not found")
    if schedule_in.interval_minutes < 1:
        raise HTTPException(status_code=400, detail="interval_minutes must be >= 1")

    schedule_obj = models.ScanSchedule(
        client_id=schedule_in.client_id,
        scan_type=schedule_in.scan_type,
        interval_minutes=schedule_in.interval_minutes,
    )
    db.add(schedule_obj)
    db.commit()
    db.refresh(schedule_obj)
    scheduler.schedule_scan(schedule_obj.id, schedule_obj.interval_minutes)

    audit.log_action(db, "create_scan_schedule", user_id=current_user.id, client_id=client_obj.id,
                     resource_type="scan_schedule", resource_id=str(schedule_obj.id),
                     details={"scan_type": schedule_obj.scan_type,
                              "interval_minutes": schedule_obj.interval_minutes})
    return schedule_obj


@router.get("/scan-schedules", response_model=List[schemas.ScanScheduleOut])
def list_scan_schedules(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.ScanSchedule)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.ScanSchedule.id.desc()).all()


@router.patch("/scan-schedules/{schedule_id}", response_model=schemas.ScanScheduleOut)
def update_scan_schedule(
    schedule_id: int,
    schedule_in: schemas.ScanScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    schedule_obj = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule_obj:
        raise HTTPException(status_code=404, detail="Scan schedule not found")

    updates = schedule_in.model_dump(exclude_unset=True)
    if "interval_minutes" in updates and updates["interval_minutes"] < 1:
        raise HTTPException(status_code=400, detail="interval_minutes must be >= 1")
    for field, value in updates.items():
        setattr(schedule_obj, field, value)

    db.commit()
    db.refresh(schedule_obj)

    if schedule_obj.is_active:
        scheduler.schedule_scan(schedule_obj.id, schedule_obj.interval_minutes)
    else:
        scheduler.unschedule_scan(schedule_obj.id)

    audit.log_action(db, "update_scan_schedule", user_id=current_user.id,
                     client_id=schedule_obj.client_id, resource_type="scan_schedule",
                     resource_id=str(schedule_obj.id), details=updates)
    return schedule_obj


@router.delete("/scan-schedules/{schedule_id}")
def delete_scan_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    schedule_obj = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule_obj:
        raise HTTPException(status_code=404, detail="Scan schedule not found")

    client_id = schedule_obj.client_id
    db.delete(schedule_obj)
    db.commit()
    scheduler.unschedule_scan(schedule_id)
    audit.log_action(db, "delete_scan_schedule", user_id=current_user.id, client_id=client_id,
                     resource_type="scan_schedule", resource_id=str(schedule_id), details={})
    return {"deleted": True}


@router.post("/scan-schedules/{schedule_id}/run")
def run_scan_schedule_now(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    schedule_obj = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule_obj:
        raise HTTPException(status_code=404, detail="Scan schedule not found")

    scan_id = worker.process_scheduled_scan(schedule_id)
    if not scan_id:
        raise HTTPException(status_code=400, detail="Schedule is inactive or scan failed")

    audit.log_action(db, "run_scan_schedule", user_id=current_user.id,
                     client_id=schedule_obj.client_id, resource_type="scan_schedule",
                     resource_id=str(schedule_id), details={"scan_id": scan_id})
    return {"scan_id": scan_id}
