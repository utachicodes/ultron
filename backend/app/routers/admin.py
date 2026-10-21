"""Admin: users and API keys."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, audit

router = APIRouter()

# ============================================================
# Admin: user management
# ============================================================
@router.get("/admin/users", response_model=List[schemas.UserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.post("/admin/users", response_model=schemas.UserOut)
def admin_create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    """Admin-provisioned account, role chosen up front. Unlike the public
    POST /auth/register (always role=client), this is the only way to hand
    someone analyst or admin access without them self-registering first and
    an admin promoting them afterwards."""
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=user_in.email,
        hashed_password=auth.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit.log_action(
        db, "admin_create_user", user_id=current_user.id,
        resource_type="user", resource_id=str(user.id),
        details={"email": user.email, "role": user.role.value},
    )
    return user


@router.patch("/admin/users/{user_id}", response_model=schemas.UserOut)
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


@router.post("/admin/users/{user_id}/reset-password", response_model=schemas.TemporaryPasswordOut)
def admin_reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    """Generate a one-time password for a user who cannot sign in.

    The password is returned exactly once and never written to the audit log.
    The user should rotate it after signing in.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    temporary_password = auth.generate_temporary_password()
    user.hashed_password = auth.get_password_hash(temporary_password)
    db.commit()
    audit.log_action(
        db, "admin_reset_password", user_id=current_user.id,
        resource_type="user", resource_id=str(user_id),
        details={"email": user.email},
    )
    return {
        "user_id": user.id,
        "email": user.email,
        "temporary_password": temporary_password,
    }

# ============================================================
# Admin: API key management
# ============================================================
@router.get("/admin/api-keys", response_model=List[schemas.APIKeyOut])
def admin_list_api_keys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    return db.query(models.APIKey).order_by(models.APIKey.created_at.desc()).all()


@router.post("/admin/api-keys", response_model=schemas.APIKeyCreated)
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


@router.delete("/admin/api-keys/{key_id}")
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
