from __future__ import annotations

"""End-to-end test of the /authz-hunts API: create a hunt against a fake
vulnerable backend (via a monkeypatched httpx.Client), confirm a leak is
detected and persisted, and that it can be reviewed."""

import httpx
import pytest

from app import authz_hunter


def _fake_handler(request: httpx.Request) -> httpx.Response:
    role = request.headers.get("x-role", "")
    if request.url.path == "/profile/42":
        # Broken object-level authz: any authenticated role gets the data.
        if role:
            return httpx.Response(200, json={"id": "42", "email": "owner@test.sn"})
        return httpx.Response(401)
    return httpx.Response(404)


@pytest.fixture(autouse=True)
def fake_http(monkeypatch):
    real_client_cls = httpx.Client

    def _factory(*args, **kwargs):
        return real_client_cls(transport=httpx.MockTransport(_fake_handler))

    monkeypatch.setattr(authz_hunter.httpx, "Client", _factory)


def test_authz_hunt_confirms_leak_and_can_be_reviewed(client, sample_client):
    res = client.post(
        "/authz-hunts",
        json={
            "client_id": sample_client["id"],
            "base_url": "https://api.testbank.sn",
            "roles": [
                {"name": "customer-a", "headers": {"X-Role": "customer-a"}},
                {"name": "customer-b", "headers": {"X-Role": "customer-b"}},
            ],
            "probes": [
                {
                    "method": "GET",
                    "path": "/profile/{id}",
                    "id_param": "id",
                    "owner_role": "customer-a",
                    "owner_value": "42",
                }
            ],
        },
    )
    assert res.status_code == 200, res.text
    hunt = res.json()
    assert hunt["status"] == "completed"
    assert hunt["probes_run"] == 1
    assert hunt["confirmed_leaks"] == 1

    findings = client.get(f"/authz-hunts/{hunt['id']}/findings").json()
    assert len(findings) == 1
    finding = findings[0]
    assert finding["verdict"] == "confirmed_leak"
    assert finding["severity"] == "critical"
    assert finding["reviewed_by_id"] is None
    # Credentials never persist in evidence.
    assert "customer-a" == finding["evidence"]["baseline_request"]["headers"]["X-Role"] or \
        finding["evidence"]["baseline_request"]["headers"]["X-Role"] == "[REDACTED]"

    reviewed = client.post(f"/authz-findings/{finding['id']}/review", json={})
    assert reviewed.status_code == 200, reviewed.text

    findings_after = client.get(f"/authz-hunts/{hunt['id']}/findings").json()
    assert findings_after[0]["reviewed_by_id"] is not None


def test_suggest_probes_from_inline_spec(client):
    res = client.post(
        "/authz-hunts/suggest-probes",
        json={
            "spec": {
                "paths": {
                    "/orders/{orderId}": {
                        "get": {
                            "parameters": [
                                {"name": "orderId", "in": "path", "schema": {"type": "integer"}}
                            ]
                        }
                    }
                }
            }
        },
    )
    assert res.status_code == 200, res.text
    suggestions = res.json()["suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["path"] == "/orders/{orderId}"
    assert suggestions[0]["id_param"] == "orderId"


def test_suggest_probes_requires_spec_or_spec_url(client):
    res = client.post("/authz-hunts/suggest-probes", json={})
    assert res.status_code == 400


def test_suggest_probes_fetches_spec_url(client, monkeypatch):
    def fake_fetch(spec_url, timeout=10.0):
        assert spec_url == "https://api.testbank.sn/openapi.json"
        return {
            "paths": {
                "/accounts/{id}": {"get": {"parameters": [{"name": "id", "in": "path"}]}}
            }
        }

    monkeypatch.setattr(authz_hunter, "fetch_openapi_spec", fake_fetch)

    res = client.post(
        "/authz-hunts/suggest-probes",
        json={"spec_url": "https://api.testbank.sn/openapi.json"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["suggestions"][0]["path"] == "/accounts/{id}"


def test_authz_hunt_requires_at_least_two_roles(client, sample_client):
    res = client.post(
        "/authz-hunts",
        json={
            "client_id": sample_client["id"],
            "base_url": "https://api.testbank.sn",
            "roles": [{"name": "solo", "headers": {}}],
            "probes": [
                {"method": "GET", "path": "/x/{id}", "id_param": "id", "owner_role": "solo", "owner_value": "1"}
            ],
        },
    )
    assert res.status_code == 400


def test_client_role_cannot_see_other_clients_hunts(client, sample_client, db):
    from app import models, auth

    client.post(
        "/authz-hunts",
        json={
            "client_id": sample_client["id"],
            "base_url": "https://api.testbank.sn",
            "roles": [
                {"name": "a", "headers": {"X-Role": "a"}},
                {"name": "b", "headers": {"X-Role": "b"}},
            ],
            "probes": [
                {"method": "GET", "path": "/profile/{id}", "id_param": "id", "owner_role": "a", "owner_value": "42"}
            ],
        },
    )

    other_user = models.User(
        email="other-client@test.local",
        hashed_password=auth.get_password_hash("password123"),
        role=models.UserRole.client,
    )
    db.add(other_user)
    db.commit()
    token = auth.create_access_token(data={"sub": other_user.email})

    from fastapi.testclient import TestClient
    from app.main import app

    other_client_http = TestClient(app)
    other_client_http.headers.update({"Authorization": f"Bearer {token}"})

    res = other_client_http.get("/authz-hunts")
    assert res.status_code == 200
    assert res.json() == []
