from __future__ import annotations

import os
import tempfile


def _make_monitor(client, sample_client, target="http://127.0.0.1:9/nope"):
    res = client.post(
        "/monitors",
        json={
            "target": target,
            "monitor_type": "access_anomaly",
            "client_id": sample_client["id"],
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_create_and_list_monitors(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    assert monitor["is_active"] is True

    res = client.get("/monitors")
    assert res.status_code == 200
    assert any(m["id"] == monitor["id"] for m in res.json())


def test_check_unreachable_target_creates_alert(client, sample_client):
    monitor = _make_monitor(client, sample_client)

    res = client.post(f"/monitors/{monitor['id']}/check")
    assert res.status_code == 200, res.text
    assert res.json()["alerts_created"] == 1

    alerts = client.get(f"/monitors/{monitor['id']}/alerts")
    assert alerts.status_code == 200
    body = alerts.json()
    assert len(body) == 1
    assert body[0]["severity"] == "high"
    assert body[0]["status"] == "open"

    listed = client.get("/monitors").json()
    updated = next(m for m in listed if m["id"] == monitor["id"])
    assert updated["last_check"] is not None


def test_patch_monitor_toggles_active(client, sample_client):
    monitor = _make_monitor(client, sample_client)

    res = client.patch(f"/monitors/{monitor['id']}", json={"is_active": False})
    assert res.status_code == 200, res.text
    assert res.json()["is_active"] is False

    res = client.patch(f"/monitors/{monitor['id']}", json={"is_active": True})
    assert res.json()["is_active"] is True


def test_delete_monitor_removes_alerts(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    client.post(f"/monitors/{monitor['id']}/check")

    res = client.delete(f"/monitors/{monitor['id']}")
    assert res.status_code == 200
    assert res.json()["deleted"] is True

    assert client.get(f"/monitors/{monitor['id']}/alerts").status_code == 404


def test_code_scan_detects_planted_issues(client, sample_client):
    repo = tempfile.mkdtemp(prefix="ultorn-code-")
    with open(os.path.join(repo, "app.py"), "w") as fh:
        fh.write(
            'API_KEY = "sk-live-9f8a7b6c5d4e3f2a1b0c"\n'
            "def run(q):\n"
            "    return eval(q)\n"
            'requests.get("https://api.example.com", verify=False)\n'
        )

    res = client.post(
        "/code-scans",
        json={
            "client_id": sample_client["id"],
            "repository_url": repo,
            "branch": "main",
        },
    )
    assert res.status_code == 200, res.text
    scan = res.json()
    assert scan["status"] == "completed"
    assert scan["issues_found"] >= 3

    issues = client.get(f"/code-scans/{scan['id']}/issues")
    assert issues.status_code == 200
    kinds = {i["issue_type"] for i in issues.json()}
    assert "hardcoded_secret" in kinds
    assert "dangerous_eval" in kinds
    assert "ssl_verification_disabled" in kinds
