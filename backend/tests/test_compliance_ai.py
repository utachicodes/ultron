from __future__ import annotations


def test_compliance_summary_banking(client):
    res = client.get(
        "/compliance/summary",
        params={
            "total_findings": 5,
            "critical": 1,
            "high": 2,
            "medium": 1,
            "client_sector": "banking",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["framework"] == "Senegal Cybersecurity Law 2026"
    assert body["reporting_required"] is True
    assert body["cert_notification_window_hours"] > 0
    assert body["next_steps"]


def test_compliance_map(client):
    res = client.post(
        "/compliance/map",
        json={
            "findings": [
                {"title": "Hardcoded API key", "severity": "critical", "id": 1},
                {"title": "Open SSH port", "severity": "high", "id": 2},
            ],
            "client_sector": "banking",
        },
    )
    assert res.status_code == 200, res.text
    mappings = res.json()["mappings"]
    assert mappings
    assert all("law_article" in m for m in mappings)
    assert all("priority" in m for m in mappings)


def test_sanitizer_removes_pii_and_secrets(client):
    res = client.post(
        "/sanitize",
        json={
            "text": "Client Acme at IP 10.0.0.5 used key sk-1234567890abcdef and email a@b.com",
            "client_name": "Acme",
        },
    )
    assert res.status_code == 200, res.text
    sanitized = res.json()["sanitized"]
    assert "10.0.0.5" not in sanitized
    assert "sk-1234567890abcdef" not in sanitized
    assert "a@b.com" not in sanitized


def test_ai_query_local_stays_local(client):
    res = client.post(
        "/ai/query",
        json={"prompt": "Summarize this vulnerability", "force_local": True},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["response"]
    assert body["provider"] == "local"
    assert body["model"] == "local-rule-based"
    assert body["query_id"]


def test_ai_audit_records_queries(client):
    client.post("/ai/query", json={"prompt": "hello", "force_local": True})
    res = client.get("/ai/audit")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_audit_log_records_actions(client, sample_client):
    client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "example.org", "target_type": "domain"},
    )
    res = client.get("/audit")
    assert res.status_code == 200
    actions = [a["action"] for a in res.json()]
    assert any("scope" in a for a in actions)
