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


DEMO_CLIENTS = ["Sahel Bank", "Sonatel Mobile", "Dakar United FC"]

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
    {
        "email": "client-demo@dakarunitedfc.sn",
        "password": "demo-club-123",
        "full_name": "Dakar United FC Operations",
        "role": "client",
    },
]


def _findings_for(kind: str):
    if kind == "bank":
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
    if kind == "telecom":
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
    # Sports demo tenant. Findings are deliberately spread across the systems
    # a club actually runs: ticketing, payments, academy, stadium gateway,
    # membership, and the public site.
    return [
        ("Exposed ticketing admin panel", "critical", "9.4", "A01:2021",
         "tickets.dakarunitedfc.sn", "GET /admin returned HTTP 200 with a public login form.",
         "Restrict the panel to the club VPN, enforce MFA, and remove public exposure."),
        ("Payment API key committed to fan-app repository", "critical", "9.1", "A02:2021",
         "api.dakarunitedfc.sn", "sk-live-… found in src/config.ts of the public fan-app repo.",
         "Rotate the key with the payment provider and purge it from git history."),
        ("Academy portal allows password-only staff login", "high", "8.0", "A07:2021",
         "academy.dakarunitedfc.sn", "Back-office login accepted without MFA from a new ASN.",
         "Require MFA for staff and guardian accounts and review session lifetime."),
        ("Open HTTP admin console on stadium gateway", "high", "7.8", "A05:2021",
         "196.207.10.20", "Port 8080 returned a POS gateway login page over plain HTTP.",
         "Move management to the club VPN and terminate TLS at the edge."),
        ("Outdated WordPress plugin on club site", "high", "7.4", "A06:2021",
         "dakarunitedfc.sn", "Plugin version known vulnerable; the footer discloses it.",
         "Update the plugin, remove unused extensions, and schedule a maintenance window."),
        ("Missing HSTS on membership login", "medium", "5.3", "A05:2021",
         "members.dakarunitedfc.sn", "Strict-Transport-Security absent on the login response.",
         "Send max-age=31536000; includeSubDomains."),
        ("Verbose server banner", "low", "3.1", "A05:2021",
         "dakarunitedfc.sn", "Server: nginx/1.18.0 exposes the exact version.",
         "Suppress version tokens at the edge."),
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
        code_scans = db.query(models.CodeScan).filter(models.CodeScan.client_id == client.id).all()
        for code_scan in code_scans:
            db.query(models.CodeScanIssue).filter(
                models.CodeScanIssue.code_scan_id == code_scan.id
            ).delete()
            db.delete(code_scan)
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
        sports_demo_user = demo_users["client-demo@dakarunitedfc.sn"]

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
            _seed_findings(db, scan, _findings_for("bank"))

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
            _seed_findings(db, scan, _findings_for("telecom"))

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

        if "Dakar United FC" not in existing:
            club = models.Client(
                name="Dakar United FC",
                legal_name="Dakar United Football Club SUARL",
                contact_email="operations@dakarunitedfc.sn",
                contact_phone="+221 33 222 2222",
                sector="sports",
                owner_id=sports_demo_user.id,
            )
            db.add(club)
            db.flush()
            for target, target_type in [
                ("dakarunitedfc.sn", "domain"),
                ("https://tickets.dakarunitedfc.sn", "url"),
                ("https://academy.dakarunitedfc.sn", "url"),
                ("196.207.10.20", "ip"),
            ]:
                db.add(models.ScanScope(
                    client_id=club.id,
                    target=target,
                    target_type=target_type,
                    verified=True,
                ))
            # An explicitly excluded legacy fan site demonstrates that the
            # scope is a contract: not everything the club owns is in play.
            db.add(models.ScanScope(
                client_id=club.id,
                target="https://legacy-fans.dakarunitedfc.sn",
                target_type="url",
                is_excluded=True,
            ))

            scan = models.Scan(
                client_id=club.id,
                requested_by_id=admin.id,
                scan_type="vulnerability",
                status="completed",
                started_at=datetime.utcnow() - timedelta(hours=2),
                completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            )
            db.add(scan)
            db.flush()
            _seed_findings(db, scan, _findings_for("sports"))

            ticketing_monitor = models.Monitor(
                client_id=club.id,
                target="https://tickets.dakarunitedfc.sn",
                monitor_type="access_anomaly",
                baseline_config=json.dumps({"status_code": 200}),
                last_check=datetime.utcnow() - timedelta(minutes=6),
                next_check=datetime.utcnow() + timedelta(minutes=54),
            )
            leak_monitor = models.Monitor(
                client_id=club.id,
                target="https://dakarunitedfc.sn",
                monitor_type="leaked_cred",
                last_check=datetime.utcnow() - timedelta(minutes=15),
                next_check=datetime.utcnow() + timedelta(minutes=45),
            )
            stream_monitor = models.Monitor(
                client_id=club.id,
                target="https://stream.dakarunitedfc.sn",
                monitor_type="config_drift",
                baseline_config=json.dumps({"server": "nginx/1.24.0"}),
                last_check=datetime.utcnow() - timedelta(minutes=9),
                next_check=datetime.utcnow() + timedelta(minutes=51),
            )
            db.add_all([ticketing_monitor, leak_monitor, stream_monitor])
            db.flush()
            db.add_all([
                models.Alert(
                    monitor_id=ticketing_monitor.id,
                    title="Ticketing endpoint returned HTTP 503",
                    description="tickets.dakarunitedfc.sn failed two checks in a row, 36 hours before kickoff.",
                    severity="high",
                    evidence=json.dumps({"status_code": 503, "consecutive_failures": 2}),
                    status="open",
                ),
                models.Alert(
                    monitor_id=leak_monitor.id,
                    title="Leaked payment key on public fan-app repository",
                    description="A live-looking sk-live key was found in the club's public fan-app repo.",
                    severity="critical",
                    evidence=json.dumps({"issue_type": "exposed_secret_key", "source": "github"}),
                    status="open",
                ),
                models.Alert(
                    monitor_id=stream_monitor.id,
                    title="Server header changed on stream.dakarunitedfc.sn",
                    description="Baseline nginx/1.24.0, observed nginx/1.18.0.",
                    severity="medium",
                    evidence=json.dumps({"baseline": "nginx/1.24.0", "current": "nginx/1.18.0"}),
                    status="acknowledged",
                ),
            ])

            db.add(models.ScanSchedule(
                client_id=club.id,
                scan_type="vulnerability",
                interval_minutes=1440,
                last_run=datetime.utcnow() - timedelta(hours=2),
                next_run=datetime.utcnow() + timedelta(hours=22),
            ))

            code = models.CodeScan(
                client_id=club.id,
                repository_url="github.com/dakar-united/fan-app",
                branch="main",
                status="completed",
                total_files=96,
                issues_found=4,
            )
            db.add(code)
            db.flush()
            db.add_all([
                models.CodeScanIssue(
                    code_scan_id=code.id,
                    file_path="src/config.ts",
                    line_number=12,
                    issue_type="hardcoded_secret",
                    severity="high",
                    description="Payment provider key literal assigned in source.",
                ),
                models.CodeScanIssue(
                    code_scan_id=code.id,
                    file_path="src/api.ts",
                    line_number=28,
                    issue_type="ssl_verification_disabled",
                    severity="medium",
                    description="TLS verification turned off for ticket API calls.",
                ),
                models.CodeScanIssue(
                    code_scan_id=code.id,
                    file_path="server/index.ts",
                    line_number=41,
                    issue_type="wildcard_cors",
                    severity="medium",
                    description="CORS allows any origin on the membership API.",
                ),
                models.CodeScanIssue(
                    code_scan_id=code.id,
                    file_path="src/tickets.ts",
                    line_number=77,
                    issue_type="dangerous_eval",
                    severity="high",
                    description="eval() applied to a query parameter from the ticket scanner.",
                ),
            ])

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
