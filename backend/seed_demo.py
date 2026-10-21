from __future__ import annotations

"""Seed the database with a realistic demo tenant.

Usage:
    cd backend
    python seed_demo.py [--reset]

Idempotent: running it twice will not duplicate the demo clients, because it
keys off the client names. `--reset` deletes the demo clients (and their
scans, findings, monitors, alerts and code scans) first.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

from app import models
from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine


DEMO_CLIENTS = ["Sahel Bank", "Sonatel Mobile"]

# One-click "try it" personas for the login screen's demo buttons. Like the
# rest of this script, they only exist if an operator explicitly runs
# `python seed_demo.py` -- a real deployment that never runs it never has them.
DEMO_ACCOUNTS = [
    {
        "email": "admin@ultorn.local",
        "password": "admin123",
        "full_name": "Platform Admin",
        "role": "admin",
    },
    {
        "email": "analyst-demo@ultorn.local",
        "password": "demo-analyst-123",
        "full_name": "Demo Analyst",
        "role": "analyst",
    },
    {
        "email": "client-demo@sahelbank.sn",
        "password": "demo-client-123",
        "full_name": "Sahel Bank Security Team",
        "role": "client",
    },
]


def _findings_for(bank: bool):
    if bank:
        return [
            ("TLS certificate expires in 9 days", "high", "9.1", "A02:2021",
             "bank.sn", "Expiry: 2026-10-28. Issuer: Let's Encrypt R3.", "Renew and automate certificate rotation."),
            ("Exposed .git directory", "critical", "9.8", "A05:2021",
             "bank.sn", "GET /.git/config -> HTTP 200, repository metadata readable.", "Block dotfiles at the edge and purge the directory."),
            ("Missing HSTS header", "medium", "5.3", "A05:2021",
             "bank.sn", "Strict-Transport-Security absent on the login response.", "Send max-age=31536000; includeSubDomains."),
            ("Outdated jQuery 1.12.4", "medium", "6.1", "A06:2021",
             "bank.sn", "Detected jquery-1.12.4.min.js on the portal.", "Upgrade to a supported release."),
            ("Verbose server banner", "low", "3.1", "A05:2021",
             "bank.sn", "Server: nginx/1.18.0 exposes the exact version.", "Suppress version tokens."),
        ]
    return [
        ("API key committed to public repository", "critical", "9.6", "A02:2021",
         "api.sonatel.sn", "Pattern sk-live-… found in a public GitHub mirror.", "Rotate the key and purge git history."),
        ("Admin panel reachable without MFA", "high", "8.2", "A07:2021",
         "admin.sonatel.sn", "Password-only login accepted from a new ASN.", "Enforce MFA for all privileged accounts."),
        ("Open Redis port 6379", "high", "7.5", "A05:2021",
         "10.20.0.14", "Redis responded to PING without authentication.", "Bind to localhost and require AUTH."),
        ("Cookie missing Secure flag", "low", "3.7", "A05:2021",
         "api.sonatel.sn", "Set-Cookie: session=… without Secure.", "Add Secure; HttpOnly; SameSite=Lax."),
    ]


def _seed_findings(db, scan, rows):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for title, severity, cvss, owasp, target, evidence, remediation in rows:
        db.add(
            models.Finding(
                scan_id=scan.id,
                title=title,
                description=f"{title}. Detected during automated assessment of {target}.",
                severity=severity,
                cvss_score=cvss,
                owasp_category=owasp,
                target=target,
                evidence=json.dumps({"raw": evidence}),
                remediation=remediation,
                status="open",
            )
        )
        counts[severity] += 1
    scan.summary = json.dumps(
        {
            "total_findings": len(rows),
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
            "requires_human_review": counts["critical"] + counts["high"],
        }
    )


def _delete_demo(db):
    for name in DEMO_CLIENTS:
        client = db.query(models.Client).filter(models.Client.name == name).first()
        if not client:
            continue
        scans = db.query(models.Scan).filter(models.Scan.client_id == client.id).all()
        for scan in scans:
            db.query(models.Finding).filter(models.Finding.scan_id == scan.id).delete()
            db.delete(scan)
        monitors = db.query(models.Monitor).filter(models.Monitor.client_id == client.id).all()
        for monitor in monitors:
            db.query(models.Alert).filter(models.Alert.monitor_id == monitor.id).delete()
            db.delete(monitor)
        db.query(models.CodeScan).filter(models.CodeScan.client_id == client.id).delete()
        db.query(models.ScanSchedule).filter(models.ScanSchedule.client_id == client.id).delete()
        db.query(models.ScanScope).filter(models.ScanScope.client_id == client.id).delete()
        db.delete(client)
    db.commit()


def _ensure_demo_accounts(db) -> dict:
    """Create (or update the role of) each one-click demo persona. Idempotent
    and run on every invocation -- independent of whether the demo clients
    below already exist, so re-running the script after an upgrade still
    backfills any new persona."""
    users = {}
    for account in DEMO_ACCOUNTS:
        user = db.query(models.User).filter(models.User.email == account["email"]).first()
        if not user:
            user = models.User(
                email=account["email"],
                hashed_password=get_password_hash(account["password"]),
                full_name=account["full_name"],
                role=models.UserRole(account["role"]),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        users[account["email"]] = user
    return users


def seed(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo_users = _ensure_demo_accounts(db)
        admin = demo_users["admin@ultorn.local"]
        client_demo_user = demo_users["client-demo@sahelbank.sn"]

        if reset:
            _delete_demo(db)

        existing = {c.name for c in db.query(models.Client).filter(models.Client.name.in_(DEMO_CLIENTS)).all()}
        if len(existing) == len(DEMO_CLIENTS):
            # Backfill: an older demo DB may still have Sahel Bank owned by
            # admin from before the client-demo persona existed.
            bank = db.query(models.Client).filter(models.Client.name == "Sahel Bank").first()
            if bank and bank.owner_id != client_demo_user.id:
                bank.owner_id = client_demo_user.id
                db.commit()
            print("Demo data already present. Use --reset to rebuild it.")
            return

        bank = None
        if "Sahel Bank" not in existing:
            bank = models.Client(
                name="Sahel Bank",
                legal_name="Sahel Bank SA",
                contact_email="security@sahelbank.sn",
                contact_phone="+221 33 000 0000",
                sector="banking",
                owner_id=client_demo_user.id,
            )
            db.add(bank)
            db.flush()
            for target, target_type in [
                ("bank.sn", "domain"),
                ("https://portal.bank.sn", "url"),
                ("196.207.0.10", "ip"),
            ]:
                db.add(models.ScanScope(client_id=bank.id, target=target, target_type=target_type, verified=True))

            scan = models.Scan(
                client_id=bank.id,
                requested_by_id=admin.id,
                scan_type="vulnerability",
                status="completed",
                started_at=datetime.utcnow() - timedelta(hours=3),
                completed_at=datetime.utcnow() - timedelta(hours=2, minutes=40),
            )
            db.add(scan)
            db.flush()
            _seed_findings(db, scan, _findings_for(True))

            monitor = models.Monitor(
                client_id=bank.id,
                target="https://bank.sn",
                monitor_type="config_drift",
                baseline_config=json.dumps({"server": "nginx/1.24.0"}),
                last_check=datetime.utcnow() - timedelta(minutes=12),
                next_check=datetime.utcnow() + timedelta(minutes=48),
            )
            db.add(monitor)
            db.flush()
            db.add_all(
                [
                    models.Alert(
                        monitor_id=monitor.id,
                        title="Server header changed on bank.sn",
                        description="Baseline nginx/1.24.0, observed nginx/1.18.0.",
                        severity="medium",
                        evidence=json.dumps({"baseline": "nginx/1.24.0", "current": "nginx/1.18.0"}),
                        status="open",
                    ),
                    models.Alert(
                        monitor_id=monitor.id,
                        title="TLS certificate expiring in 9 days",
                        description="Automatic renewal appears to have failed.",
                        severity="high",
                        evidence=json.dumps({"expires": "2026-10-28"}),
                        status="acknowledged",
                    ),
                ]
            )

            db.add(models.ScanSchedule(
                client_id=bank.id,
                scan_type="vulnerability",
                interval_minutes=1440,
                last_run=datetime.utcnow() - timedelta(hours=3),
                next_run=datetime.utcnow() + timedelta(hours=21),
            ))

            code = models.CodeScan(
                client_id=bank.id,
                repository_url="github.com/sahel-bank/mobile-api",
                branch="main",
                status="completed",
                total_files=184,
                issues_found=3,
            )
            db.add(code)
            db.flush()
            db.add_all(
                [
                    models.CodeScanIssue(
                        code_scan_id=code.id,
                        file_path="app/config.py",
                        line_number=14,
                        issue_type="hardcoded_secret",
                        severity="high",
                        description="API key literal assigned in source.",
                    ),
                    models.CodeScanIssue(
                        code_scan_id=code.id,
                        file_path="app/utils.py",
                        line_number=52,
                        issue_type="dangerous_eval",
                        severity="high",
                        description="eval() applied to request data.",
                    ),
                    models.CodeScanIssue(
                        code_scan_id=code.id,
                        file_path="app/http.py",
                        line_number=31,
                        issue_type="ssl_verification_disabled",
                        severity="medium",
                        description="TLS verification turned off.",
                    ),
                ]
            )

        if "Sonatel Mobile" not in existing:
            telco = models.Client(
                name="Sonatel Mobile",
                legal_name="Sonatel SA",
                contact_email="soc@sonatel.sn",
                contact_phone="+221 33 111 1111",
                sector="telecom",
                owner_id=admin.id,
            )
            db.add(telco)
            db.flush()
            for target, target_type in [("api.sonatel.sn", "domain"), ("10.20.0.14", "ip")]:
                db.add(models.ScanScope(client_id=telco.id, target=target, target_type=target_type, verified=True))

            scan = models.Scan(
                client_id=telco.id,
                requested_by_id=admin.id,
                scan_type="vulnerability",
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=1),
                completed_at=datetime.utcnow() - timedelta(days=1) + timedelta(minutes=25),
            )
            db.add(scan)
            db.flush()
            _seed_findings(db, scan, _findings_for(False))

            monitor = models.Monitor(
                client_id=telco.id,
                target="api.sonatel.sn",
                monitor_type="leaked_cred",
                last_check=datetime.utcnow() - timedelta(minutes=5),
                next_check=datetime.utcnow() + timedelta(minutes=55),
            )
            db.add(monitor)
            db.flush()
            db.add(
                models.Alert(
                    monitor_id=monitor.id,
                    title="Leaked credential detected on api.sonatel.sn",
                    description="Public mirror contains a live-looking sk-live key.",
                    severity="critical",
                    evidence=json.dumps({"issue_type": "exposed_secret_key", "source": "github mirror"}),
                    status="open",
                )
            )

        db.commit()
        print("Seeded demo clients:", ", ".join(DEMO_CLIENTS))
        print("Demo accounts (also usable from the console login screen's 'Try a demo' buttons):")
        for account in DEMO_ACCOUNTS:
            print(f"  {account['role']:<8} {account['email']} / {account['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Ultorn demo data")
    parser.add_argument("--reset", action="store_true", help="delete and rebuild demo clients")
    args = parser.parse_args()
    seed(reset=args.reset)
