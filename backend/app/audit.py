from __future__ import annotations

"""Immutable audit logging. Every action is logged for regulatory accountability."""

import json
from sqlalchemy.orm import Session
from app.models import AuditLog
from app.database import SessionLocal


def log_action(
    db: Session,
    action: str,
    user_id: int | None = None,
    client_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        client_id=client_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
