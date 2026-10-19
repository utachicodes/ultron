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


def execute_scan(db, scan, user_id: int | None = None) -> dict:
    """Execute a scan against every non-excluded scope and persist findings.

    Used by both the synchronous API endpoint and the scan scheduler.
    Returns a summary dict.
    """
    from app.scanner import run_scan

    scan.status = "running"
    db.commit()

    scopes = (
        db.query(models.ScanScope)
        .filter(
            models.ScanScope.client_id == scan.client_id,
            models.ScanScope.is_excluded == False,
        )
        .all()
    )

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
    scan.summary = json.dumps(
        {
            "total_findings": len(all_findings),
            "critical": len([f for f in all_findings if f.severity == "critical"]),
            "high": len([f for f in all_findings if f.severity == "high"]),
            "medium": len([f for f in all_findings if f.severity == "medium"]),
            "low": len([f for f in all_findings if f.severity == "low"]),
            "requires_human_review": len(critical_high),
        }
    )
    db.commit()
    db.refresh(scan)

    try:
        from app import audit

        audit.log_action(
            db,
            "complete_scan",
            user_id=user_id,
            client_id=scan.client_id,
            resource_type="scan",
            resource_id=str(scan.id),
            details=scan.summary,
        )
    except Exception:
        pass

    return {
        "status": "completed",
        "findings_count": len(all_findings),
        "requires_human_review": len(critical_high),
    }


def process_scheduled_scan(schedule_id: int) -> int:
    """Create and run a scan from a schedule row. Returns the new scan id (or 0)."""
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        sched = (
            db.query(models.ScanSchedule)
            .filter(models.ScanSchedule.id == schedule_id)
            .first()
        )
        if not sched or not sched.is_active:
            return 0

        scan = models.Scan(
            client_id=sched.client_id,
            requested_by_id=None,
            scan_type=sched.scan_type,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        execute_scan(db, scan, user_id=None)

        sched.last_run = datetime.utcnow()
        sched.next_run = datetime.utcnow() + timedelta(minutes=sched.interval_minutes)
        db.commit()
        return scan.id
    except Exception:
        db.rollback()
        return 0
    finally:
        db.close()


def process_monitor_check(monitor_id: int, force: bool = False):
    """Run one monitoring check and persist any alerts it produces.

    Shared by the scheduler and by ad-hoc calls so both paths behave
    identically (same evidence, same alert rows). `force=True` lets an
    operator run a check on a paused monitor.
    """
    from datetime import datetime, timedelta
    from app.monitor import run_monitoring_check

    db = SessionLocal()
    try:
        monitor = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
        if not monitor:
            return 0
        if not monitor.is_active and not force:
            return 0

        baseline = json.loads(monitor.baseline_config) if monitor.baseline_config else None
        alerts = run_monitoring_check(monitor.monitor_type, monitor.target, baseline)

        monitor.last_check = datetime.utcnow()
        monitor.next_check = datetime.utcnow() + timedelta(minutes=60)

        for alert_data in alerts:
            db.add(
                models.Alert(
                    monitor_id=monitor.id,
                    title=alert_data.get("title", "Alert"),
                    description=alert_data.get("description"),
                    severity=alert_data.get("severity", "medium"),
                    evidence=json.dumps(alert_data.get("evidence"))
                    if alert_data.get("evidence")
                    else None,
                    status="open",
                )
            )

        db.commit()
        return len(alerts)
    except Exception:
        db.rollback()
        return 0
    finally:
        db.close()
