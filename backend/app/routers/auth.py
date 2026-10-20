"""Authentication and registration."""

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas, auth, rate_limit, audit

router = APIRouter()

# ============================================================
# Auth
# ============================================================
@router.post("/auth/token", response_model=schemas.Token)
def login(form_data: dict, request: Request, db: Session = Depends(get_db)):
    rate_limit.check("login", rate_limit.client_ip(request), limit=10, window_seconds=60)
    user = auth.authenticate_user(db, form_data.get("email", ""), form_data.get("password", ""))
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.post("/auth/register", response_model=schemas.UserOut)
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


@router.post("/auth/change-password")
def change_password(
    payload: schemas.PasswordChange,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    rate_limit.check("change-password", str(current_user.id), limit=5, window_seconds=60)
    if not auth.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from the current password")

    current_user.hashed_password = auth.get_password_hash(payload.new_password)
    db.commit()
    audit.log_action(
        db,
        "change_password",
        user_id=current_user.id,
        resource_type="user",
        resource_id=str(current_user.id),
        ip_address=rate_limit.client_ip(request),
    )
    return {"changed": True}


# ============================================================
# Self-service forgot-password (no SMTP provider wired up yet: the
# reset link is logged server-side instead of emailed. Swap `_deliver_reset_link`
# for a real mail send once a provider is configured, without touching the
# token logic below).
# ============================================================
def _deliver_reset_link(user: models.User, raw_token: str) -> None:
    print(f"[password-reset] token for {user.email}: {raw_token} "
          f"(expires in {settings.password_reset_token_expire_minutes}m)")


@router.post("/auth/forgot-password")
def forgot_password(
    payload: schemas.ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit.check("forgot-password", rate_limit.client_ip(request), limit=5, window_seconds=300)

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    response: dict = {"detail": "If that account exists, a reset link has been sent."}

    if user and user.is_active:
        # Invalidate any outstanding tokens so only the newest link works.
        db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.user_id == user.id,
            models.PasswordResetToken.used_at.is_(None),
        ).update({"used_at": datetime.utcnow()})

        raw_token = secrets.token_urlsafe(32)
        reset_token = models.PasswordResetToken(
            user_id=user.id,
            token_hash=auth.hash_api_key(raw_token),
            expires_at=datetime.utcnow()
            + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
        db.add(reset_token)
        audit.log_action(
            db,
            "forgot_password_requested",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=rate_limit.client_ip(request),
        )
        db.commit()

        _deliver_reset_link(user, raw_token)
        if settings.debug:
            # Dev convenience only: never expose this once a real mail
            # provider replaces `_deliver_reset_link`.
            response["dev_reset_token"] = raw_token

    return response


@router.post("/auth/reset-password")
def reset_password(
    payload: schemas.ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit.check("reset-password", rate_limit.client_ip(request), limit=10, window_seconds=300)

    token_hash = auth.hash_api_key(payload.token)
    reset_token = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token_hash == token_hash)
        .first()
    )
    now = datetime.utcnow()
    if (
        not reset_token
        or reset_token.used_at is not None
        or reset_token.expires_at < now
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(models.User).filter(models.User.id == reset_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = auth.get_password_hash(payload.new_password)
    reset_token.used_at = now
    db.commit()

    audit.log_action(
        db,
        "reset_password",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=rate_limit.client_ip(request),
    )
    return {"reset": True}
