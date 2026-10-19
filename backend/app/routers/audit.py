"""Immutable audit trail."""

from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter()

# ============================================================
# Audit
# ============================================================
@router.get("/audit", response_model=List[schemas.AuditLogOut])
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
