from __future__ import annotations

"""Background worker for running scans asynchronously."""

import time
import json
import hashlib
from app.scanner import run_scan
from app.database import SessionLocal
from app import models
from sqlalchemy.sql import func


def _compute_fingerprint(client_id: int, result: dict) -> str:
    """Stable identity for "the same underlying issue" across recurring scans.

    We intentionally hash a small, normalized set of fields (client, title,
    target, severity) rather than the full result -- evidence/description
    text (response bodies, banners, timestamps...) can legitimately vary
    scan-to-scan for what is really the same vulnerability, and we don't
    want that noise to defeat dedup.
    """
    title = (result.get("title") or "unknown").strip().lower()
    target = (result.get("target") or "").strip().lower()
    severity = (result.get("severity") or "info").strip().lower()
    raw = f"{client_id}:{title}:{target}:{severity}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def process_scan(scan_id: int):
    """Run a scan in the background.

    NOTE: dead code. Nothing in the app calls this anymore (the API endpoint
    and the scheduler both go through `execute_scan` below, which is the
    version that does finding dedup). Left in place only for reference;
    do not wire this one up without adding the same dedup logic.
    """
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
    print("Ultorn worker ready. Run with: celery -A app.celery_app worker --loglevel=info")


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

    all_findings = []  # new Finding rows actually inserted by this scan run
    # Severities of every issue that is "new or still open" as of this run --
    # i.e. newly created findings plus pre-existing open findings that this
    # run re-detected (and merely bumped occurrence_count on, with no new
    # row). This is what the scan summary is built from: for a recurring
    # scan where most results are repeats of still-open issues, a summary
    # that only counted brand-new rows would make the scan look falsely
    # clean. The summary should describe "what's wrong right now", not
    # "what rows did this particular run insert".
    counted_severities = []
    # Findings created earlier in *this* run, keyed by fingerprint. The
    # session uses autoflush=False, so a plain query wouldn't see rows
    # added-but-not-flushed by an earlier iteration of this same loop --
    # this local cache catches duplicates within a single scan/scope list
    # too, not just duplicates across separate scan runs.
    created_in_this_run = {}

    for scope in scopes:
        results = run_scan(scope.target, scan.scan_type)
        for r in results:
            if "error" in r:
                continue
            severity = r.get("severity", "info")
            fingerprint = _compute_fingerprint(scan.client_id, r)

            if fingerprint in created_in_this_run:
                created_in_this_run[fingerprint].occurrence_count = (
                    created_in_this_run[fingerprint].occurrence_count or 1
                ) + 1
                counted_severities.append(severity)
                continue

            # Look for the same issue already on record for this client.
            # Dedup is scoped to the client (any of its scans), not just
            # this scan, since a recurring schedule re-runs the same scope
            # under a brand new Scan row every time.
            existing = (
                db.query(models.Finding)
                .join(models.Scan, models.Finding.scan_id == models.Scan.id)
                .filter(
                    models.Scan.client_id == scan.client_id,
                    models.Finding.fingerprint == fingerprint,
                    models.Finding.status == "open",
                )
                .order_by(models.Finding.id.desc())
                .first()
            )

            if existing is not None:
                # Judgment call: we only dedup against findings still in the
                # default "open" state. If a human reviewer already marked
                # this fingerprint "fixed"/"false_positive"/anything else,
                # we deliberately do NOT touch that row -- silently bumping
                # its counter (or flipping it back open) would erase the
                # reviewer's decision. A rescan that still finds the issue
                # instead falls through and gets its own fresh row below,
                # which is the honest signal that it has recurred/regressed
                # since being closed.
                existing.occurrence_count = (existing.occurrence_count or 1) + 1
                created_in_this_run[fingerprint] = existing
                counted_severities.append(severity)
                continue

            finding = models.Finding(
                scan_id=scan.id,
                title=r.get("title", "Unknown"),
                description=r.get("description"),
                severity=severity,
                cvss_score=r.get("cvss_score"),
                owasp_category=None,
                target=r.get("target"),
                evidence=json.dumps(r.get("evidence")) if r.get("evidence") else None,
                remediation=r.get("remediation"),
                fingerprint=fingerprint,
                first_seen_scan_id=scan.id,
            )
            db.add(finding)
            all_findings.append(finding)
            created_in_this_run[fingerprint] = finding
            counted_severities.append(severity)

    critical_high = [s for s in counted_severities if s in ("critical", "high")]

    scan.status = "completed"
    scan.completed_at = func.now()
    scan.summary = json.dumps(
        {
            "total_findings": len(counted_severities),
            "critical": counted_severities.count("critical"),
            "high": counted_severities.count("high"),
            "medium": counted_severities.count("medium"),
            "low": counted_severities.count("low"),
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
        "findings_count": len(counted_severities),
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

        created_alerts = []
        for alert_data in alerts:
            alert = models.Alert(
                monitor_id=monitor.id,
                title=alert_data.get("title", "Alert"),
                description=alert_data.get("description"),
                severity=alert_data.get("severity", "medium"),
                evidence=json.dumps(alert_data.get("evidence"))
                if alert_data.get("evidence")
                else None,
                status="open",
            )
            db.add(alert)
            created_alerts.append(alert)

        db.commit()

        # Deliver after commit so each payload has a real id.
        try:
            from app.notify import dispatch_alert

            for alert in created_alerts:
                db.refresh(alert)
                dispatch_alert(
                    {
                        "id": alert.id,
                        "monitor_id": alert.monitor_id,
                        "target": monitor.target,
                        "monitor_type": monitor.monitor_type,
                        "client_id": monitor.client_id,
                        "title": alert.title,
                        "description": alert.description,
                        "severity": alert.severity,
                        "status": alert.status,
                        "evidence": json.loads(alert.evidence) if alert.evidence else None,
                        "created_at": alert.created_at,
                    }
                )
        except Exception:
            pass

        return len(alerts)
    except Exception:
        db.rollback()
        return 0
    finally:
        db.close()
