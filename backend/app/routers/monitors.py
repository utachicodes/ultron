"""Continuous monitoring and alerts."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import models, schemas, auth, audit, monitor, scheduler, worker

router = APIRouter()

# ============================================================
# Monitors (Continuous Monitoring)
# ============================================================
@router.post("/monitors", response_model=schemas.MonitorOut)
def create_monitor(
    monitor_in: schemas.MonitorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = db.query(models.Client).filter(models.Client.id == monitor_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if current_user.role == models.UserRole.client and client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    monitor = models.Monitor(
        client_id=monitor_in.client_id,
        target=monitor_in.target,
        monitor_type=monitor_in.monitor_type,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    scheduler.schedule_monitor(monitor.id)
    audit.log_action(db, "create_monitor", user_id=current_user.id, client_id=client.id,
                     resource_type="monitor", resource_id=str(monitor.id),
                     details={"target": monitor_in.target, "monitor_type": monitor_in.monitor_type})
    return monitor


@router.get("/monitors", response_model=List[schemas.MonitorOut])
def list_monitors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Monitor)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.all()


@router.patch("/monitors/{monitor_id}", response_model=schemas.MonitorOut)
def update_monitor(
    monitor_id: int,
    monitor_in: schemas.MonitorUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    monitor_obj = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
    if not monitor_obj:
        raise HTTPException(status_code=404, detail="Monitor not found")

    updates = monitor_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(monitor_obj, field, value)

    db.commit()
    db.refresh(monitor_obj)

    if monitor_obj.is_active:
        scheduler.schedule_monitor(monitor_obj.id)
    else:
        scheduler.unschedule_monitor(monitor_obj.id)

    audit.log_action(db, "update_monitor", user_id=current_user.id, client_id=monitor_obj.client_id,
                     resource_type="monitor", resource_id=str(monitor_obj.id), details=updates)
    return monitor_obj


@router.delete("/monitors/{monitor_id}")
def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    monitor_obj = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
    if not monitor_obj:
        raise HTTPException(status_code=404, detail="Monitor not found")

    client_id = monitor_obj.client_id
    db.query(models.Alert).filter(models.Alert.monitor_id == monitor_id).delete()
    db.delete(monitor_obj)
    db.commit()
    scheduler.unschedule_monitor(monitor_id)
    audit.log_action(db, "delete_monitor", user_id=current_user.id, client_id=client_id,
                     resource_type="monitor", resource_id=str(monitor_id), details={})
    return {"deleted": True}


@router.get("/monitors/{monitor_id}/alerts", response_model=List[schemas.AlertOut])
def get_monitor_alerts(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    monitor = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    if current_user.role == models.UserRole.client and monitor.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Alert).filter(models.Alert.monitor_id == monitor_id).all()


@router.get("/alerts", response_model=List[schemas.AlertOut])
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """All alerts across monitors, newest first, optionally filtered."""
    query = db.query(models.Alert).join(models.Monitor)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    if status:
        query = query.filter(models.Alert.status == status)
    if severity:
        query = query.filter(models.Alert.severity == severity)
    return query.order_by(models.Alert.created_at.desc(), models.Alert.id.desc()).all()


@router.patch("/alerts/{alert_id}", response_model=schemas.AlertOut)
def update_alert(
    alert_id: int,
    alert_in: schemas.AlertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    alert_obj = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert_obj:
        raise HTTPException(status_code=404, detail="Alert not found")

    valid = {"open", "acknowledged", "resolved", "false_positive"}
    if alert_in.status not in valid:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(valid)}")

    alert_obj.status = alert_in.status
    alert_obj.resolved_at = datetime.utcnow() if alert_in.status in ("resolved", "false_positive") else None
    db.commit()
    db.refresh(alert_obj)

    audit.log_action(db, "update_alert", user_id=current_user.id, client_id=alert_obj.monitor.client_id,
                     resource_type="alert", resource_id=str(alert_obj.id),
                     details={"status": alert_in.status, "note": alert_in.note})
    return alert_obj


@router.post("/monitors/{monitor_id}/check")
def run_monitor_check(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    monitor_obj = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
    if not monitor_obj:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Operator-initiated checks run even when a monitor is paused, but are
    # recorded in the same way as scheduled checks.
    alerts_created = worker.process_monitor_check(monitor_id, force=True)

    audited = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
    audit.log_action(db, "run_monitor_check", user_id=current_user.id,
                     client_id=audited.client_id if audited else None,
                     resource_type="monitor", resource_id=str(monitor_id),
                     details={"alerts_created": alerts_created})
    return {"alerts_created": alerts_created}
