from __future__ import annotations

"""Tests for finding dedup across recurring scans.

`execute_scan` is monkeypatched via `app.scanner.run_scan` (it is imported
locally inside `execute_scan`, so patching the scanner module's attribute,
not `app.worker.run_scan`, is what actually takes effect -- same pattern
used in tests/test_scanner.py).
"""

from app import models, scanner


FAKE_RESULTS = [
    {
        "title": "Outdated TLS version",
        "description": "Server supports TLS 1.0",
        "severity": "high",
        "target": "127.0.0.1",
        "evidence": {"detail": "tls1.0"},
        "remediation": "Disable TLS 1.0",
    }
]


def _stub_scan(monkeypatch, results=None):
    monkeypatch.setattr(scanner, "run_scan", lambda target, scan_type="vulnerability": results or FAKE_RESULTS)


def _make_scope_and_scan(client, sample_client):
    client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "127.0.0.1", "target_type": "ip"},
    )
    scan = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    ).json()
    return scan


def test_first_run_creates_finding_with_occurrence_one(client, sample_client, db, monkeypatch):
    _stub_scan(monkeypatch)
    scan = _make_scope_and_scan(client, sample_client)

    run = client.post(f"/scans/{scan['id']}/run")
    assert run.status_code == 200, run.text

    findings = client.get(f"/scans/{scan['id']}/findings").json()
    assert len(findings) == 1
    f = findings[0]
    assert f["occurrence_count"] == 1
    assert f["first_seen_scan_id"] == scan["id"]
    assert f["fingerprint"]
    assert f["status"] == "open"


def test_second_run_dedups_instead_of_duplicating(client, sample_client, db, monkeypatch):
    _stub_scan(monkeypatch)
    scan1 = _make_scope_and_scan(client, sample_client)
    run1 = client.post(f"/scans/{scan1['id']}/run")
    assert run1.status_code == 200, run1.text

    # A second, independent scan run against the same scope/client -- this
    # mimics what a recurring ScanSchedule does: a brand new Scan row each
    # time, same underlying target/issue.
    scan2 = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    ).json()
    run2 = client.post(f"/scans/{scan2['id']}/run")
    assert run2.status_code == 200, run2.text

    # No new Finding row was created under scan2 for the repeated issue.
    findings_scan2 = client.get(f"/scans/{scan2['id']}/findings").json()
    assert findings_scan2 == []

    # The original finding (owned by scan1) had its occurrence bumped, and
    # still points at scan1 as its first-seen scan.
    findings_scan1 = client.get(f"/scans/{scan1['id']}/findings").json()
    assert len(findings_scan1) == 1
    f = findings_scan1[0]
    assert f["occurrence_count"] == 2
    assert f["first_seen_scan_id"] == scan1["id"]

    # Total rows for this fingerprint across the whole client: still just one.
    all_findings = db.query(models.Finding).filter(models.Finding.scan_id.in_([scan1["id"], scan2["id"]])).all()
    assert len(all_findings) == 1

    # Scan2's summary reflects the still-open issue it re-detected, even
    # though it didn't insert a new row for it.
    scan2_obj = db.query(models.Scan).filter(models.Scan.id == scan2["id"]).first()
    import json

    summary = json.loads(scan2_obj.summary)
    assert summary["total_findings"] == 1
    assert summary["high"] == 1


def test_resolved_finding_is_not_silently_reopened(client, sample_client, db, monkeypatch):
    """A finding a human reviewer closed must not be silently bumped/reopened.

    We chose: a rescan that still detects the same issue creates a NEW
    finding row (instead of touching the reviewed one), so the resolved
    finding's status/history stays intact and the recurrence is visible as
    its own fresh entry rather than a surprise reopen.
    """
    _stub_scan(monkeypatch)
    scan1 = _make_scope_and_scan(client, sample_client)
    client.post(f"/scans/{scan1['id']}/run")

    findings_scan1 = client.get(f"/scans/{scan1['id']}/findings").json()
    assert len(findings_scan1) == 1
    finding_id = findings_scan1[0]["id"]

    review = client.post(f"/findings/{finding_id}/review", json={"status": "fixed"})
    assert review.status_code == 200, review.text

    scan2 = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    ).json()
    run2 = client.post(f"/scans/{scan2['id']}/run")
    assert run2.status_code == 200, run2.text

    # The reviewed finding keeps its reviewed status and original occurrence
    # count -- it was not touched by the rescan.
    reviewed = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    assert reviewed.status == "fixed"
    assert reviewed.occurrence_count == 1

    # The rescan recorded the recurrence as its own new row under scan2.
    findings_scan2 = client.get(f"/scans/{scan2['id']}/findings").json()
    assert len(findings_scan2) == 1
    assert findings_scan2[0]["id"] != finding_id
    assert findings_scan2[0]["occurrence_count"] == 1
    assert findings_scan2[0]["first_seen_scan_id"] == scan2["id"]
    assert findings_scan2[0]["fingerprint"] == reviewed.fingerprint


def test_duplicate_results_within_a_single_run_are_merged(client, sample_client, db, monkeypatch):
    """Two identical results returned by the same run_scan() call shouldn't
    create two rows either (autoflush is off, so this exercises the
    in-memory cache rather than a DB round trip)."""
    _stub_scan(monkeypatch, results=FAKE_RESULTS + FAKE_RESULTS)
    scan = _make_scope_and_scan(client, sample_client)
    run = client.post(f"/scans/{scan['id']}/run")
    assert run.status_code == 200, run.text

    findings = client.get(f"/scans/{scan['id']}/findings").json()
    assert len(findings) == 1
    assert findings[0]["occurrence_count"] == 2
