"""Clients and scan scopes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app import models, schemas, auth, audit

router = APIRouter()

# ============================================================
# Clients
# ============================================================
@router.post("/clients", response_model=schemas.ClientOut)
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


@router.get("/clients", response_model=List[schemas.ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Client)
    if current_user.role == models.UserRole.client:
        query = query.filter(models.Client.owner_id == current_user.id)
    return query.all()


@router.get("/clients/{client_id}", response_model=schemas.ClientOut)
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


@router.patch("/clients/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    client_in: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    updates = client_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)

    audit.log_action(
        db, "update_client", user_id=current_user.id, client_id=client.id,
        resource_type="client", resource_id=str(client.id), details=updates,
    )
    return client


@router.delete("/clients/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    """Admin-only: a client deletion cascades through every scan, finding,
    monitor, alert, schedule, and code scan scoped to it -- a much larger
    blast radius than any other delete in the console, so it is restricted
    beyond the usual admin/analyst "can manage" line analysts get elsewhere.
    """
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    name = client.name
    scans = db.query(models.Scan).filter(models.Scan.client_id == client_id).all()
    for scan in scans:
        db.query(models.Finding).filter(models.Finding.scan_id == scan.id).delete()
        db.delete(scan)

    monitors = db.query(models.Monitor).filter(models.Monitor.client_id == client_id).all()
    for monitor in monitors:
        db.query(models.Alert).filter(models.Alert.monitor_id == monitor.id).delete()
        db.delete(monitor)

    code_scans = db.query(models.CodeScan).filter(models.CodeScan.client_id == client_id).all()
    for code_scan in code_scans:
        db.query(models.CodeScanIssue).filter(models.CodeScanIssue.code_scan_id == code_scan.id).delete()
        db.delete(code_scan)

    db.query(models.ScanSchedule).filter(models.ScanSchedule.client_id == client_id).delete()
    db.query(models.ScanScope).filter(models.ScanScope.client_id == client_id).delete()
    db.delete(client)
    db.commit()

    audit.log_action(
        db, "delete_client", user_id=current_user.id, client_id=None,
        resource_type="client", resource_id=str(client_id), details={"name": name},
    )
    return {"deleted": True}

# ============================================================
# Scan Scopes
# ============================================================
@router.post("/clients/{client_id}/scopes", response_model=schemas.ScanScopeOut)
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


@router.get("/clients/{client_id}/scopes", response_model=List[schemas.ScanScopeOut])
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


@router.patch("/clients/{client_id}/scopes/{scope_id}", response_model=schemas.ScanScopeOut)
def update_scope(
    client_id: int,
    scope_id: int,
    scope_in: schemas.ScanScopeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    scope = (
        db.query(models.ScanScope)
        .filter(models.ScanScope.id == scope_id, models.ScanScope.client_id == client_id)
        .first()
    )
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")

    updates = scope_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(scope, field, value)
    db.commit()
    db.refresh(scope)

    audit.log_action(
        db, "update_scan_scope", user_id=current_user.id, client_id=client_id,
        resource_type="scan_scope", resource_id=str(scope_id), details=updates,
    )
    return scope


@router.delete("/clients/{client_id}/scopes/{scope_id}")
def delete_scope(
    client_id: int,
    scope_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    scope = (
        db.query(models.ScanScope)
        .filter(models.ScanScope.id == scope_id, models.ScanScope.client_id == client_id)
        .first()
    )
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")

    target = scope.target
    db.delete(scope)
    db.commit()

    audit.log_action(
        db, "delete_scan_scope", user_id=current_user.id, client_id=client_id,
        resource_type="scan_scope", resource_id=str(scope_id), details={"target": target},
    )
    return {"deleted": True}


@router.post("/scopes/{scope_id}/verify")
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
