from __future__ import annotations

"""Tests for app/scope_guard.py and its enforcement in /authz-hunts and
/ai-redteam/runs (external mode) -- confirming a client's explicitly
excluded scope is actually honored by the newer engines, not just the
passive scanner."""

import httpx
import pytest

from app import authz_hunter, scope_guard


def test_extract_host_handles_urls_and_bare_hosts():
    assert scope_guard.extract_host("https://api.example.sn/path") == "api.example.sn"
    assert scope_guard.extract_host("http://example.sn:8443") == "example.sn"
    assert scope_guard.extract_host("example.sn") == "example.sn"
    assert scope_guard.extract_host("") is None


def test_is_excluded_matches_exact_and_subdomain(db):
    from app import models

    client_obj = models.Client(name="Scope Test Co", owner_id=None)
    db.add(client_obj)
    db.commit()
    db.refresh(client_obj)

    db.add(
        models.ScanScope(
            client_id=client_obj.id,
            target="excluded.example.sn",
            target_type="domain",
            is_excluded=True,
        )
    )
    db.add(
        models.ScanScope(
            client_id=client_obj.id,
            target="allowed.example.sn",
            target_type="domain",
            is_excluded=False,
        )
    )
    db.commit()

    assert scope_guard.is_excluded("excluded.example.sn", client_obj.id, db) is True
    # Subdomain of an excluded target is also excluded.
    assert scope_guard.is_excluded("api.excluded.example.sn", client_obj.id, db) is True
    # A scope that exists but isn't marked excluded doesn't block anything.
    assert scope_guard.is_excluded("allowed.example.sn", client_obj.id, db) is False
    # A host with no scope record at all is allowed by default.
    assert scope_guard.is_excluded("unregistered.example.sn", client_obj.id, db) is False


def test_enforce_scope_raises_on_excluded_host(db):
    from app import models

    client_obj = models.Client(name="Enforce Test Co", owner_id=None)
    db.add(client_obj)
    db.commit()
    db.refresh(client_obj)
    db.add(
        models.ScanScope(
            client_id=client_obj.id, target="blocked.test", target_type="domain", is_excluded=True
        )
    )
    db.commit()

    with pytest.raises(scope_guard.ScopeViolation):
        scope_guard.enforce_scope("https://blocked.test/api", client_obj, db)

    # Does not raise for an unrelated host.
    scope_guard.enforce_scope("https://fine.test/api", client_obj, db)


def _fake_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"id": "1"})


def test_authz_hunt_endpoint_refuses_excluded_base_url(client, sample_client, monkeypatch):
    real_client_cls = httpx.Client

    def _factory(*args, **kwargs):
        return real_client_cls(transport=httpx.MockTransport(_fake_handler))

    monkeypatch.setattr(authz_hunter.httpx, "Client", _factory)

    exclude = client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "blocked.testbank.sn", "target_type": "domain", "is_excluded": True},
    )
    assert exclude.status_code == 200, exclude.text

    res = client.post(
        "/authz-hunts",
        json={
            "client_id": sample_client["id"],
            "base_url": "https://blocked.testbank.sn",
            "roles": [
                {"name": "a", "headers": {"X-Role": "a"}},
                {"name": "b", "headers": {"X-Role": "b"}},
            ],
            "probes": [
                {"method": "GET", "path": "/x/{id}", "id_param": "id", "owner_role": "a", "owner_value": "1"}
            ],
        },
    )
    assert res.status_code == 403
    assert "excluded" in res.json()["detail"]


def test_ai_redteam_external_refuses_excluded_url(client, sample_client):
    exclude = client.post(
        f"/clients/{sample_client['id']}/scopes",
        json={"target": "blocked-ai.testbank.sn", "target_type": "domain", "is_excluded": True},
    )
    assert exclude.status_code == 200, exclude.text

    res = client.post(
        "/ai-redteam/runs",
        json={
            "client_id": sample_client["id"],
            "mode": "external",
            "external": {"url": "https://blocked-ai.testbank.sn/ai/chat"},
        },
    )
    assert res.status_code == 403
    assert "excluded" in res.json()["detail"]
