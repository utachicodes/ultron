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
