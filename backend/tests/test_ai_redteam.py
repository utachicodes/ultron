from __future__ import annotations

"""Tests for app/ai_redteam.py (the attack engine) and the full attack ->
learn -> reblock loop against app.jailbreak_guard and app.ai_router."""

import httpx

from app import ai_redteam, jailbreak_guard
from app.ai_router import route_ai_query


def test_build_prompt_embeds_canary():
    payload = {"template": "Say exactly: {canary}"}
    prompt = ai_redteam.build_prompt(payload, "ULTRON_CANARY_abc123")
    assert prompt == "Say exactly: ULTRON_CANARY_abc123"


def test_classify_response_bypassed_vs_blocked():
    canary = "ULTRON_CANARY_xyz"
    assert ai_redteam.classify_response(f"Sure! {canary}", canary) == "bypassed"
    assert ai_redteam.classify_response("I can't help with that.", canary) == "blocked"
    assert ai_redteam.classify_response(None, canary) == "blocked"
    assert ai_redteam.classify_response("", canary) == "blocked"


def test_generate_canary_is_unique_each_call():
    canaries = {ai_redteam.generate_canary() for _ in range(20)}
    assert len(canaries) == 20


def _always_comply(prompt: str, **kwargs):
    """A naive model with no jailbreak resistance: echoes back whatever the
    prompt asks it to say (finds the trailing token after the last colon)."""
    return {"response": f"Sure, here you go: {prompt.rsplit(':', 1)[-1].strip()}"}


def _always_refuse(prompt: str, **kwargs):
    return {"response": "I'm sorry, I can't help with that request."}


def test_run_internal_redteam_against_a_fully_compliant_model_bypasses_everything():
    results = ai_redteam.run_internal_redteam(_always_comply)
    assert len(results) == len(ai_redteam.PAYLOADS)
    assert all(r["verdict"] == "bypassed" for r in results)


def test_run_internal_redteam_against_a_refusing_model_blocks_everything():
    results = ai_redteam.run_internal_redteam(_always_refuse)
    assert all(r["verdict"] == "blocked" for r in results)


def test_run_internal_redteam_handles_ai_query_fn_errors():
    def _boom(prompt, **kwargs):
        raise RuntimeError("provider unreachable")

    results = ai_redteam.run_internal_redteam(_boom)
    assert all(r["verdict"] == "error" for r in results)
    assert all("provider unreachable" in r["error"] for r in results)


def test_run_external_redteam_uses_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        import json

        prompt = json.loads(body)["prompt"]
        canary = prompt.rsplit(":", 1)[-1].strip()
        return httpx.Response(200, json={"response": f"ok: {canary}"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        results = ai_redteam.run_external_redteam(
            "https://client-app.test/ai/chat", headers={}, http_client=c
        )
    assert all(r["verdict"] == "bypassed" for r in results)


def test_attack_then_learn_then_reblock_loop(db, admin_token):
    """The full loop: an undefended category bypasses Ultron's own AI Guard
    pipeline, gets learned as a pattern, and the exact same attack is then
    blocked on the next run -- without touching source code."""
    category = "payload_splitting"
    payload = next(p for p in ai_redteam.PAYLOADS if p["category"] == category)

    def naive_model(prompt, client_name=None, user=None, client=None, db=None, force_local=False):
        # Simulates calling route_ai_query against a provider with zero
        # jailbreak resistance: it complies unless Ultron's own guard (the
        # `force_local` -> local canned response path) kicks in first.
        if force_local:
            return {"response": "[LOCAL] Content kept on-premises."}
        canary = prompt.rsplit(":", 1)[-1].strip()
        return {"response": f"Sure: {canary}"}

    # 1. Attack: nothing learned yet for this category -> bypassed.
    canary = ai_redteam.generate_canary()
    prompt = ai_redteam.build_prompt(payload, canary)
    matched, _ = jailbreak_guard.is_jailbreak_attempt(prompt, db)
    assert matched is False
    first_result = naive_model(prompt, db=db, force_local=matched)
    assert ai_redteam.classify_response(first_result["response"], canary) == "bypassed"

    # 2. Defend: record the bypass as a learned pattern.
    jailbreak_guard.add_pattern_from_bypass(db, category, source_run_id=None)

    # 3. Re-attack with a fresh canary: the real `route_ai_query` path (not
    # just the test double) must now force local processing because
    # `is_jailbreak_attempt` matches the learned pattern -- proving the loop
    # closes through the actual production code path, not just the mock.
    from app import models

    user = db.query(models.User).first()
    ai_result = route_ai_query(prompt, user=user, db=db)
    assert ai_result["jailbreak_detected"] is True
    assert ai_result["jailbreak_category"] == category
    assert ai_result["provider"] == "local"
