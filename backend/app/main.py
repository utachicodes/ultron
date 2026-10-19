from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

from app.config import settings
from app.database import Base, engine, SessionLocal, get_db
from app import models, schemas, auth, scanner, ai_router, audit, code_scanner, monitor, compliance, reports, rate_limit, scheduler, worker
from app.sanitizer import sanitize_text

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup seed: default admin user
# ============================================================
@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        admin = db.query(models.User).filter(models.User.email == "admin@ultorn.local").first()
        if not admin:
            admin = models.User(
                email="admin@ultorn.local",
                hashed_password=auth.get_password_hash("admin123"),
                full_name="Platform Admin",
                role=models.UserRole.admin,
            )
            db.add(admin)
            db.commit()
            print("Seeded admin user: admin@ultorn.local / admin123")
    finally:
        db.close()

    # Continuous monitoring. Disable with ENABLE_SCHEDULER=false (e.g. when
    # running multiple API replicas so only one process schedules jobs).
    import os

    if os.getenv("ENABLE_SCHEDULER", "true").lower() not in ("0", "false", "no"):
        try:
            scheduled = scheduler.bootstrap()
            scheduler.start()
            print(
                f"Scheduler started: {len(scheduled['monitors'])} monitor(s), "
                f"{len(scheduled['scan_schedules'])} scan schedule(s)"
            )
        except Exception as exc:  # pragma: no cover - startup must not crash
            print(f"Scheduler failed to start: {exc}")


# ============================================================
# Auth
# ============================================================
@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: dict, request: Request, db: Session = Depends(get_db)):
    rate_limit.check("login", rate_limit.client_ip(request), limit=10, window_seconds=60)
    user = auth.authenticate_user(db, form_data.get("email", ""), form_data.get("password", ""))
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.RegisterCreate, request: Request, db: Session = Depends(get_db)):
    rate_limit.check("register", rate_limit.client_ip(request), limit=5, window_seconds=300)
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=user_in.email,
        hashed_password=auth.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=models.UserRole.client,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# Clients
# ============================================================
@app.post("/clients", response_model=schemas.ClientOut)
def create_client(
    client_in: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = models.Client(**client_in.model_dump(), owner_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    audit.log_action(db, "create_client", user_id=current_user.id, client_id=client.id, details={"name": client_in.name})
    return client


@app.get("/clients", response_model=List[schemas.ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Client)
    if current_user.role == models.UserRole.client:
        query = query.filter(models.Client.owner_id == current_user.id)
    return query.all()


@app.get("/clients/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if current_user.role == models.UserRole.client and client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return client


# ============================================================
# Scan Scopes
# ============================================================
@app.post("/clients/{client_id}/scopes", response_model=schemas.ScanScopeOut)
def add_scope(
    client_id: int,
    scope_in: schemas.ScanScopeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    token = str(uuid.uuid4())
    scope = models.ScanScope(
        client_id=client_id,
        target=scope_in.target,
        target_type=scope_in.target_type,
        is_excluded=scope_in.is_excluded,
        verification_method=scope_in.verification_method,
        verification_token=token,
    )
    db.add(scope)
    db.commit()
    db.refresh(scope)
    audit.log_action(
        db, "add_scan_scope", user_id=current_user.id, client_id=client_id,
        resource_type="scan_scope", resource_id=str(scope.id),
        details={"target": scope_in.target, "verification_token": token},
    )
    return scope


@app.get("/clients/{client_id}/scopes", response_model=List[schemas.ScanScopeOut])
def list_scopes(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if current_user.role == models.UserRole.client and client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.ScanScope).filter(models.ScanScope.client_id == client_id).all()


@app.post("/scopes/{scope_id}/verify")
def verify_scope(
    scope_id: int,
    verification: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scope = db.query(models.ScanScope).filter(models.ScanScope.id == scope_id).first()
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")
    token = verification.get("token", "")
    if token != scope.verification_token:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    scope.verified = True
    from sqlalchemy.sql import func
    scope.verified_at = func.now()
    db.commit()
    audit.log_action(
        db, "verify_scan_scope", user_id=current_user.id, client_id=scope.client_id,
        resource_type="scan_scope", resource_id=str(scope_id),
    )
    return {"verified": True}


# ============================================================
# Scans: NO verification gate, runs on all scopes
# ============================================================
@app.post("/scans", response_model=schemas.ScanOut)
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


@app.get("/scans", response_model=List[schemas.ScanOut])
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


@app.get("/scans/{scan_id}", response_model=schemas.ScanOut)
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


@app.post("/scans/{scan_id}/run")
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
@app.post("/scan-schedules", response_model=schemas.ScanScheduleOut)
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


@app.get("/scan-schedules", response_model=List[schemas.ScanScheduleOut])
def list_scan_schedules(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.ScanSchedule)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.ScanSchedule.id.desc()).all()


@app.patch("/scan-schedules/{schedule_id}", response_model=schemas.ScanScheduleOut)
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


@app.delete("/scan-schedules/{schedule_id}")
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


@app.post("/scan-schedules/{schedule_id}/run")
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


# ============================================================
# Findings
# ============================================================
@app.get("/scans/{scan_id}/findings", response_model=List[schemas.FindingOut])
def get_findings(
    scan_id: int,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return (
        db.query(models.Finding)
        .filter(models.Finding.scan_id == scan_id)
        .order_by(models.Finding.id)
        .offset(offset)
        .limit(min(limit, 1000))
        .all()
    )


@app.post("/findings/{finding_id}/review")
def review_finding(
    finding_id: int,
    review: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.status = review.get("status", finding.status)
    finding.reviewed_by_id = current_user.id
    from sqlalchemy.sql import func
    finding.reviewed_at = func.now()
    db.commit()
    audit.log_action(
        db, "review_finding", user_id=current_user.id, client_id=finding.scan.client_id,
        resource_type="finding", resource_id=str(finding_id),
        details={"status": finding.status},
    )
    return {"status": finding.status, "reviewed_by": current_user.email}


# ============================================================
# AI / Sovereignty
# ============================================================
@app.post("/ai/query")
def ai_query(
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    prompt = request.get("prompt", "")
    client_name = request.get("client_name")
    force_local = request.get("force_local", False)

    client_obj = None
    if request.get("client_id"):
        client_obj = db.query(models.Client).filter(models.Client.id == request["client_id"]).first()
        if client_obj and current_user.role == models.UserRole.client and client_obj.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    response = ai_router.route_ai_query(
        prompt=prompt,
        client_name=client_name,
        user=current_user,
        client=client_obj,
        db=db,
        force_local=force_local,
    )
    return response


@app.get("/ai/audit", response_model=List[schemas.AIQueryOut])
def ai_audit_log(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    return db.query(models.AIQueryLog).order_by(models.AIQueryLog.created_at.desc()).all()


# ============================================================
# Audit
# ============================================================
@app.get("/audit", response_model=List[schemas.AuditLogOut])
def get_audit_log(
    limit: int = 200,
    offset: int = 0,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    query = db.query(models.AuditLog)
    if action:
        query = query.filter(models.AuditLog.action == action)
    entries = (
        query.order_by(models.AuditLog.created_at.desc(), models.AuditLog.id.desc())
        .offset(offset)
        .limit(min(limit, 1000))
        .all()
    )
    results = []
    for entry in entries:
        out = schemas.AuditLogOut.model_validate(entry)
        out.user_email = entry.user.email if entry.user else None
        results.append(out)
    return results


# ============================================================
# Sanitize (demo endpoint)
# ============================================================
@app.post("/sanitize")
def sanitize_endpoint(
    request: dict,
    current_user: models.User = Depends(auth.get_current_user),
):
    text = request.get("text", "")
    client_name = request.get("client_name")
    clean, stats = sanitize_text(text, client_name)
    return {"sanitized": clean, "stats": stats}


# ============================================================
# Admin: user management
# ============================================================
@app.get("/admin/users", response_model=List[schemas.UserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@app.patch("/admin/users/{user_id}", response_model=schemas.UserOut)
def admin_update_user(
    user_id: int,
    update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    changes = update.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    audit.log_action(
        db, "admin_update_user", user_id=current_user.id,
        resource_type="user", resource_id=str(user_id), details=changes,
    )
    return user


# ============================================================
# Admin: API key management
# ============================================================
@app.get("/admin/api-keys", response_model=List[schemas.APIKeyOut])
def admin_list_api_keys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    return db.query(models.APIKey).order_by(models.APIKey.created_at.desc()).all()


@app.post("/admin/api-keys", response_model=schemas.APIKeyCreated)
def admin_create_api_key(
    key_in: schemas.APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    raw_key, prefix, key_hash = auth.generate_api_key()
    key = models.APIKey(
        name=key_in.name,
        owner_id=current_user.id,
        key_prefix=prefix,
        key_hash=key_hash,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    audit.log_action(
        db, "admin_create_api_key", user_id=current_user.id,
        resource_type="api_key", resource_id=str(key.id),
        details={"name": key_in.name, "prefix": prefix},
    )
    return schemas.APIKeyCreated(**schemas.APIKeyOut.model_validate(key).model_dump(), api_key=raw_key)


@app.delete("/admin/api-keys/{key_id}")
def admin_revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    key = db.query(models.APIKey).filter(models.APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    from sqlalchemy.sql import func
    key.revoked_at = func.now()
    db.commit()
    audit.log_action(
        db, "admin_revoke_api_key", user_id=current_user.id,
        resource_type="api_key", resource_id=str(key_id),
    )
    return {"revoked": True}


# ============================================================
# Monitors (Continuous Monitoring)
# ============================================================
@app.post("/monitors", response_model=schemas.MonitorOut)
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


@app.get("/monitors", response_model=List[schemas.MonitorOut])
def list_monitors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Monitor)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.all()


@app.patch("/monitors/{monitor_id}", response_model=schemas.MonitorOut)
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


@app.delete("/monitors/{monitor_id}")
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


@app.get("/monitors/{monitor_id}/alerts", response_model=List[schemas.AlertOut])
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


@app.get("/alerts", response_model=List[schemas.AlertOut])
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


@app.patch("/alerts/{alert_id}", response_model=schemas.AlertOut)
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


@app.post("/monitors/{monitor_id}/check")
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


# ============================================================
# Code Scans
# ============================================================
@app.post("/code-scans", response_model=schemas.CodeScanOut)
def create_code_scan(
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client_id = request.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")

    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    code_scan = models.CodeScan(
        client_id=client_id,
        repository_url=request.get("repository_url"),
        branch=request.get("branch", "main"),
        status="pending",
    )
    db.add(code_scan)
    db.commit()
    db.refresh(code_scan)

    # Run synchronously for MVP
    results = code_scanner.run_code_scan(request.get("repository_url", ""), "code")

    issues_found = 0
    for r in results:
        if "error" in r:
            continue
        issue = models.CodeScanIssue(
            code_scan_id=code_scan.id,
            file_path=r.get("file_path"),
            line_number=r.get("line_number"),
            issue_type=r.get("issue_type"),
            severity=r.get("severity"),
            description=r.get("description"),
            remediation=r.get("remediation"),
        )
        db.add(issue)
        issues_found += 1

    code_scan.status = "completed"
    code_scan.total_files = len(set(r.get("file_path", "") for r in results if "error" not in r))
    code_scan.issues_found = issues_found
    db.commit()
    db.refresh(code_scan)

    return code_scan


@app.get("/code-scans", response_model=List[schemas.CodeScanOut])
def list_code_scans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.CodeScan)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.all()


@app.get("/code-scans/{code_scan_id}/issues", response_model=List[schemas.CodeScanIssueOut])
def get_code_scan_issues(
    code_scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    code_scan = db.query(models.CodeScan).filter(models.CodeScan.id == code_scan_id).first()
    if not code_scan:
        raise HTTPException(status_code=404, detail="Code scan not found")
    if current_user.role == models.UserRole.client and code_scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.CodeScanIssue).filter(models.CodeScanIssue.code_scan_id == code_scan_id).all()


# ============================================================
# Reports
# ============================================================
@app.get("/scans/{scan_id}/report")
def get_scan_report(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    findings = db.query(models.Finding).filter(models.Finding.scan_id == scan_id).all()
    findings_list = [
        {
            "id": f.id,
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "target": f.target,
            "evidence": f.evidence,
            "remediation": f.remediation,
            "status": f.status,
        }
        for f in findings
    ]

    summary = json.loads(scan.summary) if scan.summary else {}
    client = scan.client

    report = reports.generate_report(
        scan_id=scan.id,
        scan_type=scan.scan_type,
        findings=findings_list,
        summary=summary,
        client_name=client.name,
        client_sector=getattr(client, 'sector', None),
    )

    return report


@app.get("/scans/{scan_id}/report/markdown")
def get_scan_report_markdown(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    findings = db.query(models.Finding).filter(models.Finding.scan_id == scan_id).all()
    findings_list = [
        {
            "id": f.id,
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "target": f.target,
            "evidence": f.evidence,
            "remediation": f.remediation,
            "status": f.status,
        }
        for f in findings
    ]

    summary = json.loads(scan.summary) if scan.summary else {}
    client = scan.client

    report = reports.generate_report(
        scan_id=scan.id,
        scan_type=scan.scan_type,
        findings=findings_list,
        summary=summary,
        client_name=client.name,
        client_sector=getattr(client, 'sector', None),
    )

    md = reports.report_to_markdown(report)
    return {"markdown": md}


# ============================================================
# Compliance
# ============================================================
@app.post("/compliance/map")
def map_compliance(
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    findings = request.get("findings", [])
    client_sector = request.get("client_sector")
    mappings = compliance.map_findings_to_compliance(findings, client_sector)
    return {"mappings": mappings}


@app.get("/compliance/summary")
def compliance_summary(
    total_findings: int = 0,
    critical: int = 0,
    high: int = 0,
    medium: int = 0,
    client_sector: Optional[str] = None,
):
    return compliance.get_compliance_summary(total_findings, critical, high, medium, client_sector)


# ============================================================
# Health
# ============================================================
@app.get("/health")
def health():
    """Liveness/readiness probe. Does not require auth."""
    from sqlalchemy import text
    from app.database import SessionLocal

    db_status = "ok"
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    finally:
        db.close()

    jobs = scheduler.job_count()
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "database": db_status,
        "scheduler": {"running": scheduler.is_running(), "jobs": jobs},
    }
