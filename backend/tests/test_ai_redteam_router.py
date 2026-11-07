from __future__ import annotations

"""End-to-end test of /ai-redteam/runs: internal mode against a naive
test-only AI provider with zero jailbreak resistance, confirming the first
run bypasses an undefended category, learns a pattern, and a second run on
the same category is blocked -- entirely through the API."""

import httpx
import pytest

from app import ai_router as ai_router_module


@pytest.fixture(autouse=True)
def naive_external_provider(monkeypatch):
    """Make the 'anthropic' provider path behave like a naive external model
    with zero jailbreak resistance of its own, instead of hitting a real
    API (which isn't configured in tests). `route_ai_query` will still call
    `app.jailbreak_guard.is_jailbreak_attempt` first and force this to never
    be reached once a pattern is learned."""

    def _naive_call(prompt: str) -> str:
        return f"Sure, here you go: {prompt.rsplit(':', 1)[-1].strip()}"

    monkeypatch.setattr(ai_router_module, "_call_anthropic", _naive_call)


def test_redteam_run_bypasses_then_learns_then_reblocks(client, sample_client):
    # First run: payload_splitting has no pre-armed detector -- it should bypass.
    first = client.post(
        "/ai-redteam/runs",
        json={"client_id": sample_client["id"], "mode": "internal"},
    )
    assert first.status_code == 200, first.text
    run1 = first.json()
    assert run1["status"] == "completed"
    assert run1["payloads_run"] == 8

    results1 = {r["category"]: r for r in run1["results"]}
    assert results1["payload_splitting"]["verdict"] == "bypassed"
    assert results1["payload_splitting"]["pattern_learned"] is True
    # The 5 well-known categories are pre-armed and blocked from the start.
    assert results1["instruction_override"]["verdict"] == "blocked"

    patterns = client.get("/jailbreak-patterns").json()
    assert any(p["category"] == "payload_splitting" for p in patterns)

    # Second run: the exact same category must now be blocked.
    second = client.post(
        "/ai-redteam/runs",
        json={"client_id": sample_client["id"], "mode": "internal"},
    )
    run2 = second.json()
    results2 = {r["category"]: r for r in run2["results"]}
    assert results2["payload_splitting"]["verdict"] == "blocked"
    assert run2["bypassed_count"] < run1["bypassed_count"]


def test_redteam_run_requires_valid_client(client):
    res = client.post("/ai-redteam/runs", json={"client_id": 999999, "mode": "internal"})
    assert res.status_code == 404


def test_redteam_external_mode_requires_config(client, sample_client):
    res = client.post(
        "/ai-redteam/runs", json={"client_id": sample_client["id"], "mode": "external"}
    )
    assert res.status_code == 400


def test_redteam_external_mode_against_mocked_endpoint(client, sample_client, monkeypatch):
    import app.ai_redteam as ai_redteam_module

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "I can't help with that."})

    real_client_cls = httpx.Client

    def _factory(*args, **kwargs):
        return real_client_cls(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(ai_redteam_module.httpx, "Client", _factory)

    res = client.post(
        "/ai-redteam/runs",
        json={
            "client_id": sample_client["id"],
            "mode": "external",
            "external": {"url": "https://client-app.test/ai/chat"},
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["target_summary"] == "https://client-app.test/ai/chat"
    assert body["bypassed_count"] == 0
