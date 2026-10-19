"""Senegal Cyber Law 2026 mapping."""

from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth, compliance

router = APIRouter()

# ============================================================
# Compliance
# ============================================================
@router.post("/compliance/map")
def map_compliance(
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    findings = request.get("findings", [])
    client_sector = request.get("client_sector")
    mappings = compliance.map_findings_to_compliance(findings, client_sector)
    return {"mappings": mappings}


@router.get("/compliance/summary")
def compliance_summary(
    total_findings: int = 0,
    critical: int = 0,
    high: int = 0,
    medium: int = 0,
    client_sector: Optional[str] = None,
):
    return compliance.get_compliance_summary(total_findings, critical, high, medium, client_sector)
