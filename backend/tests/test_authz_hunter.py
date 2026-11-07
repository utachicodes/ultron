from __future__ import annotations

"""Tests for the autonomous IDOR/BOLA hunter engine (app/authz_hunter.py).

Uses httpx.MockTransport to simulate a tiny vulnerable API -- no network --
so the role-pair replay and verdict classification are fully deterministic.
"""

import httpx

from app.authz_hunter import run_authz_hunt, suggest_probes_from_spec


# A fake backend: /invoices/{id} returns the invoice body if the caller's
# X-Role header matches the invoice's owner; /profile/{id} is a BOLA bug
# that returns the same body regardless of who asks (as long as some role
# header is present); /admin/{id} always 403s for anyone but admin.
INVOICE_OWNERS = {"1024": "customer-a", "1025": "customer-b"}
PROFILE_OWNERS = {"42": "customer-a"}


def _fake_handler(request: httpx.Request) -> httpx.Response:
    role = request.headers.get("x-role", "")
    path = request.url.path

    if path.startswith("/invoices/"):
        invoice_id = path.rsplit("/", 1)[-1]
        owner = INVOICE_OWNERS.get(invoice_id)
        if role == owner:
            return httpx.Response(200, json={"id": invoice_id, "amount": 500, "owner": owner})
        return httpx.Response(403, json={"error": "forbidden"})

    if path.startswith("/profile/"):
        # Broken: returns the same data to any authenticated role.
        profile_id = path.rsplit("/", 1)[-1]
        owner = PROFILE_OWNERS.get(profile_id)
        if role:
            return httpx.Response(200, json={"id": profile_id, "owner": owner, "email": "a@test.sn"})
        return httpx.Response(401, json={"error": "unauthenticated"})

    if path.startswith("/admin/"):
        if role == "admin":
            return httpx.Response(200, json={"secret": "flag"})
        return httpx.Response(403, json={"error": "forbidden"})

    return httpx.Response(404)


def _client() -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(_fake_handler))


ROLES = [
    {"name": "customer-a", "headers": {"X-Role": "customer-a"}},
    {"name": "customer-b", "headers": {"X-Role": "customer-b"}},
]


def test_confirmed_leak_on_broken_object_level_authz():
    probes = [
        {
            "method": "GET",
            "path": "/profile/{id}",
            "id_param": "id",
            "owner_role": "customer-a",
            "owner_value": "42",
        }
    ]
    with _client() as c:
        results = run_authz_hunt("https://api.test", ROLES, probes, http_client=c)

    assert len(results) == 1
    r = results[0]
    assert r["owner_role"] == "customer-a"
    assert r["tested_role"] == "customer-b"
    assert r["verdict"] == "confirmed_leak"
    assert r["severity"] == "critical"
    assert r["confidence"] > 0.6
    # Credentials never leak into evidence.
    assert r["evidence"]["baseline_request"]["headers"]["X-Role"] == "[REDACTED]" or \
        r["evidence"]["baseline_request"]["headers"].get("X-Role") == "customer-a"


def test_no_leak_when_properly_scoped():
    probes = [
        {
            "method": "GET",
            "path": "/invoices/{id}",
            "id_param": "id",
            "owner_role": "customer-a",
            "owner_value": "1024",
        }
    ]
    with _client() as c:
        results = run_authz_hunt("https://api.test", ROLES, probes, http_client=c)

    assert len(results) == 1
    assert results[0]["verdict"] == "no_leak"
    assert results[0]["severity"] == "info"


def test_inconclusive_when_owner_baseline_fails():
    probes = [
        {
            # Neither role owns this id, so even the baseline is denied.
            "method": "GET",
            "path": "/invoices/{id}",
            "id_param": "id",
            "owner_role": "customer-a",
            "owner_value": "9999",
        }
    ]
    with _client() as c:
        results = run_authz_hunt("https://api.test", ROLES, probes, http_client=c)

    assert results[0]["verdict"] == "inconclusive"


def test_probe_error_for_unknown_owner_role():
    probes = [
        {
            "method": "GET",
            "path": "/profile/{id}",
            "id_param": "id",
            "owner_role": "nonexistent-role",
            "owner_value": "42",
        }
    ]
    with _client() as c:
        results = run_authz_hunt("https://api.test", ROLES, probes, http_client=c)

    assert len(results) == 1
    assert results[0]["verdict"] == "probe_error"


def test_redacts_sensitive_headers_in_evidence():
    roles = [
        {"name": "customer-a", "headers": {"X-Role": "customer-a", "Authorization": "Bearer secret-token"}},
        {"name": "customer-b", "headers": {"X-Role": "customer-b", "Authorization": "Bearer other-token"}},
    ]
    probes = [
        {
            "method": "GET",
            "path": "/profile/{id}",
            "id_param": "id",
            "owner_role": "customer-a",
            "owner_value": "42",
        }
    ]
    with _client() as c:
        results = run_authz_hunt("https://api.test", roles, probes, http_client=c)

    evidence = results[0]["evidence"]
    assert evidence["baseline_request"]["headers"]["Authorization"] == "[REDACTED]"
    assert evidence["attempt_request"]["headers"]["Authorization"] == "[REDACTED]"
    assert "secret-token" not in str(evidence)
    assert "other-token" not in str(evidence)


SAMPLE_SPEC = {
    "openapi": "3.0.0",
    "paths": {
        "/invoices/{id}": {
            "get": {
                "summary": "Get an invoice",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
            },
            "delete": {
                "summary": "Delete an invoice",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
            },
        },
        "/users/{userId}/profile": {
            "get": {
                "operationId": "getUserProfile",
                "parameters": [{"name": "userId", "in": "path", "schema": {"type": "string"}}],
            }
        },
        "/sessions/{token}": {
            # Path-level parameter (applies to all methods under it).
            "parameters": [
                {"name": "token", "in": "path", "schema": {"type": "string", "format": "uuid"}}
            ],
            "get": {"summary": "Get a session"},
        },
        "/health": {"get": {"summary": "Health check"}},
    },
}


def test_suggest_probes_from_spec_finds_id_shaped_get_endpoints():
    suggestions = suggest_probes_from_spec(SAMPLE_SPEC)
    paths = {(s["method"], s["path"], s["id_param"]) for s in suggestions}

    assert ("GET", "/invoices/{id}", "id") in paths
    assert ("GET", "/users/{userId}/profile", "userId") in paths
    assert ("GET", "/sessions/{token}", "token") in paths
    # DELETE is never suggested -- discovery is GET-only.
    assert not any(s["method"] == "DELETE" for s in suggestions)
    # No path parameter at all -- never suggested.
    assert not any(s["path"] == "/health" for s in suggestions)


def test_suggest_probes_from_spec_handles_empty_spec():
    assert suggest_probes_from_spec({}) == []
    assert suggest_probes_from_spec({"paths": {}}) == []
