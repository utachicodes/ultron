"""Bill No. 25/2026 draft compliance mapping, SOC 2, and ISO 27001 readiness."""

from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth, compliance, soc2, iso27001

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


# ============================================================
# SOC 2 readiness (AICPA Trust Services Criteria) -- a readiness signal
# built from findings, not an audit or attestation.
# ============================================================
@router.post("/compliance/soc2")
def soc2_readiness(
    request: dict,
    current_user: models.User = Depends(auth.get_current_user),
):
    findings = request.get("findings", [])
    authz_findings = request.get("authz_findings", [])
    report_type = request.get("report_type", "type2")
    return soc2.get_soc2_readiness(findings, authz_findings, report_type)


# ============================================================
# ISO/IEC 27001:2022 readiness (Annex A) -- a readiness signal built from
# findings, not a certification or Statement of Applicability.
# ============================================================
@router.post("/compliance/iso27001")
def iso27001_readiness(
    request: dict,
    current_user: models.User = Depends(auth.get_current_user),
):
    findings = request.get("findings", [])
    authz_findings = request.get("authz_findings", [])
    return iso27001.get_iso27001_readiness(findings, authz_findings)
