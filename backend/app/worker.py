from __future__ import annotations

"""Background worker for running scans asynchronously."""

import time
import json
from app.scanner import run_scan
from app.database import SessionLocal
from app import models
from sqlalchemy.sql import func


def process_scan(scan_id: int):
    """Run a scan in the background."""
    db = SessionLocal()
    try:
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if not scan:
            return

        scan.status = "running"
        db.commit()

        scopes = db.query(models.ScanScope).filter(
            models.ScanScope.client_id == scan.client_id,
            models.ScanScope.is_excluded == False,
        ).all()

        all_findings = []
        for scope in scopes:
            results = run_scan(scope.target, scan.scan_type)
            for r in results:
                if "error" in r:
                    continue
                finding = models.Finding(
                    scan_id=scan.id,
                    title=r.get("title", "Unknown"),
                    description=r.get("description"),
                    severity=r.get("severity", "info"),
                    cvss_score=r.get("cvss_score"),
                    owasp_category=None,
                    target=r.get("target"),
                    evidence=json.dumps(r.get("evidence")) if r.get("evidence") else None,
                    remediation=r.get("remediation"),
                )
                db.add(finding)
                all_findings.append(finding)

        critical_high = [f for f in all_findings if f.severity in ("critical", "high")]

        scan.status = "completed"
        scan.completed_at = func.now()
        scan.summary = json.dumps({
            "total_findings": len(all_findings),
            "critical": len([f for f in all_findings if f.severity == "critical"]),
            "high": len([f for f in all_findings if f.severity == "high"]),
            "medium": len([f for f in all_findings if f.severity == "medium"]),
            "low": len([f for f in all_findings if f.severity == "low"]),
            "requires_human_review": len(critical_high),
        })
        db.commit()
    except Exception as e:
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if scan:
            scan.status = "failed"
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    print("Ultorn worker ready. Run with: celery -A app.worker worker --loglevel=info")
