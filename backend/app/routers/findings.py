"""Findings and human analyst review."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, audit

router = APIRouter()

# ============================================================
# Findings
# ============================================================
@router.get("/scans/{scan_id}/findings", response_model=List[schemas.FindingOut])
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


@router.post("/findings/{finding_id}/review")
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
