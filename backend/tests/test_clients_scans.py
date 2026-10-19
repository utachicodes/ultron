from __future__ import annotations


def test_create_and_list_clients(client, sample_client):
    res = client.get("/clients")
    assert res.status_code == 200
    names = [c["name"] for c in res.json()]
    assert "Test Bank" in names


def test_client_scopes_crud(client, sample_client):
    res = client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "example.com", "target_type": "domain", "verification_method": "dns"},
    )
    assert res.status_code == 200, res.text
    scope = res.json()
    assert scope["target"] == "example.com"
    assert scope["verified"] is False

    listed = client.get(f"/clients/{sample_client['id']}/scopes")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_scan_runs_without_verification_gate(client, sample_client):
    client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "127.0.0.1", "target_type": "ip"},
    )
    res = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    )
    assert res.status_code == 200, res.text
    scan = res.json()

    run = client.post(f"/scans/{scan['id']}/run")
    assert run.status_code == 200, run.text
    assert run.json()["status"] in ("completed", "failed")

    findings = client.get(f"/scans/{scan['id']}/findings")
    assert findings.status_code == 200
    assert isinstance(findings.json(), list)


def test_finding_human_review(client, sample_client, db):
    from app import models

    client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "127.0.0.1", "target_type": "ip"},
    )
    scan = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    ).json()
    client.post(f"/scans/{scan['id']}/run")

    finding = models.Finding(
        scan_id=scan["id"],
        title="Test critical finding",
        severity="critical",
        target="127.0.0.1",
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)

    res = client.post(f"/findings/{finding.id}/review", json={"status": "fixed"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "fixed"
    assert body["reviewed_by"]


def test_scan_report_and_markdown(client, sample_client):
    client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "127.0.0.1", "target_type": "ip"},
    )
    scan = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    ).json()
    client.post(f"/scans/{scan['id']}/run")

    report = client.get(f"/scans/{scan['id']}/report")
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["scan_id"] == scan["id"]
    assert "overall_rating" in body
    assert isinstance(body["recommendations"], list)

    md = client.get(f"/scans/{scan['id']}/report/markdown")
    assert md.status_code == 200
    assert "# Security Assessment Report" in md.json()["markdown"]
