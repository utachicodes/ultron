"""AI sovereignty layer: sanitized prompts and query log."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, ai_router
from app.sanitizer import sanitize_text

router = APIRouter()

# ============================================================
# AI / Sovereignty
# ============================================================
@router.post("/ai/query")
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


@router.get("/ai/audit", response_model=List[schemas.AIQueryOut])
def ai_audit_log(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    return db.query(models.AIQueryLog).order_by(models.AIQueryLog.created_at.desc()).all()

# ============================================================
# Sanitize (demo endpoint)
# ============================================================
@router.post("/sanitize")
def sanitize_endpoint(
    request: dict,
    current_user: models.User = Depends(auth.get_current_user),
):
    text = request.get("text", "")
    client_name = request.get("client_name")
    clean, stats = sanitize_text(text, client_name)
    return {"sanitized": clean, "stats": stats}
