"""Report generation (JSON and Markdown)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app import models, auth, reports

router = APIRouter()

# ============================================================
# Reports
# ============================================================
@router.get("/scans/{scan_id}/report")
def get_scan_report(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    findings = db.query(models.Finding).filter(models.Finding.scan_id == scan_id).all()
    findings_list = [
        {
            "id": f.id,
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "target": f.target,
            "evidence": f.evidence,
            "remediation": f.remediation,
            "status": f.status,
        }
        for f in findings
    ]

    summary = json.loads(scan.summary) if scan.summary else {}
    client = scan.client

    report = reports.generate_report(
        scan_id=scan.id,
        scan_type=scan.scan_type,
        findings=findings_list,
        summary=summary,
        client_name=client.name,
        client_sector=getattr(client, 'sector', None),
    )

    return report


@router.get("/scans/{scan_id}/report/markdown")
def get_scan_report_markdown(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    findings = db.query(models.Finding).filter(models.Finding.scan_id == scan_id).all()
    findings_list = [
        {
            "id": f.id,
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "target": f.target,
            "evidence": f.evidence,
            "remediation": f.remediation,
            "status": f.status,
        }
        for f in findings
    ]

    summary = json.loads(scan.summary) if scan.summary else {}
    client = scan.client

    report = reports.generate_report(
        scan_id=scan.id,
        scan_type=scan.scan_type,
        findings=findings_list,
        summary=summary,
        client_name=client.name,
        client_sector=getattr(client, 'sector', None),
    )

    md = reports.report_to_markdown(report)
    return {"markdown": md}
