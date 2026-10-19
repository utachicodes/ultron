from __future__ import annotations


def _make_monitor(client, sample_client, target="http://127.0.0.1:9/nope"):
    return client.post(
        "/monitors",
        json={"target": target, "monitor_type": "access_anomaly", "client_id": sample_client["id"]},
    ).json()


def test_alerts_endpoint_lists_across_monitors(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    client.post(f"/monitors/{monitor['id']}/check")

    res = client.get("/alerts")
    assert res.status_code == 200, res.text
    alerts = res.json()
    assert len(alerts) == 1
    assert alerts[0]["monitor_id"] == monitor["id"]


def test_alert_filters(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    client.post(f"/monitors/{monitor['id']}/check")

    assert len(client.get("/alerts", params={"severity": "high"}).json()) == 1
    assert len(client.get("/alerts", params={"severity": "low"}).json()) == 0
    assert len(client.get("/alerts", params={"status": "open"}).json()) == 1
    assert len(client.get("/alerts", params={"status": "resolved"}).json()) == 0


def test_acknowledge_and_resolve_alert(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    client.post(f"/monitors/{monitor['id']}/check")
    alert = client.get("/alerts").json()[0]

    res = client.patch(f"/alerts/{alert['id']}", json={"status": "acknowledged"})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "acknowledged"
    assert res.json()["resolved_at"] is None

    res = client.patch(f"/alerts/{alert['id']}", json={"status": "resolved"})
    assert res.json()["status"] == "resolved"
    assert res.json()["resolved_at"] is not None


def test_alert_rejects_unknown_status(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    client.post(f"/monitors/{monitor['id']}/check")
    alert = client.get("/alerts").json()[0]

    res = client.patch(f"/alerts/{alert['id']}", json={"status": "banana"})
    assert res.status_code == 400


def test_update_and_delete_are_audited(client, sample_client):
    monitor = _make_monitor(client, sample_client)
    client.patch(f"/monitors/{monitor['id']}", json={"is_active": False})
    client.delete(f"/monitors/{monitor['id']}")

    actions = [a["action"] for a in client.get("/audit").json()]
    assert "update_monitor" in actions
    assert "delete_monitor" in actions
