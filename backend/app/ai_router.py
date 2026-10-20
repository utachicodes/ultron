from __future__ import annotations

"""AI routing layer with sovereignty controls.

Sanitizes prompts before sending to external models. Falls back to local
processing for sensitive data. Every query and response is immutably logged.
"""

import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import AIQueryLog, User, Client
from app.sanitizer import sanitize_text


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def route_ai_query(
    prompt: str,
    client_name: str | None = None,
    user: User | None = None,
    client: Client | None = None,
    db: Session | None = None,
    force_local: bool = False,
) -> str:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        sanitized_prompt, stats = sanitize_text(prompt, client_name)
        prompt_sanitized = stats.get("credentials", 0) > 0 or stats.get("ip_addresses", 0) > 0
        prompt_hash = _hash_text(sanitized_prompt)

        sensitive = not _is_sanitized(sanitized_prompt) or force_local

        if sensitive or settings.ai_provider == "local":
            response = _local_process(sanitized_prompt)
            provider = "local"
            model = "local-rule-based"
        elif settings.ai_provider == "anthropic":
            response = _call_anthropic(sanitized_prompt)
            provider = "anthropic"
            model = "claude-3-haiku"
        elif settings.ai_provider == "openai":
            response = _call_openai(sanitized_prompt)
            provider = "openai"
            model = "gpt-4o-mini"
        elif settings.ai_provider == "ollama":
            response = _call_ollama(sanitized_prompt)
            provider = "ollama"
            model = settings.ollama_model
        else:
            response = _call_anthropic(sanitized_prompt)
            provider = "anthropic"
            model = "claude-3-haiku"

        response_hash = _hash_text(response)
        log_entry = AIQueryLog(
            user_id=user.id if user else None,
            client_id=client.id if client else None,
            provider=provider,
            model=model,
            prompt_sanitized=prompt_sanitized,
            prompt_hash=prompt_hash,
            response_hash=response_hash,
            tokens_in=len(sanitized_prompt.split()),
            tokens_out=len(response.split()),
        )
        db.add(log_entry)
        db.commit()

        return {
            "response": response,
            "provider": provider,
            "model": model,
            "prompt_sanitized": prompt_sanitized,
            "query_id": log_entry.id,
        }
    finally:
        if close_db:
            db.close()


def _is_sanitized(text: str) -> bool:
    from app.sanitizer import CREDENTIAL_PATTERN, BEARER_TOKEN_PATTERN, IP_PATTERN
    return not bool(
        CREDENTIAL_PATTERN.search(text)
        or BEARER_TOKEN_PATTERN.search(text)
        or IP_PATTERN.search(text)
    )


def _call_anthropic(prompt: str) -> str:
    if not settings.anthropic_api_key:
        return "[AI_PROVIDER_NOT_CONFIGURED] Anthropic API key missing. Local response only."
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return "\n".join(block.text for block in msg.content if hasattr(block, "text"))
    except Exception as e:
        return f"[AI_ERROR] Anthropic call failed: {str(e)}"


def _call_openai(prompt: str) -> str:
    if not settings.openai_api_key:
        return "[AI_PROVIDER_NOT_CONFIGURED] OpenAI API key missing. Local response only."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"[AI_ERROR] OpenAI call failed: {str(e)}"


def _call_ollama(prompt: str) -> str:
    """Call a local Ollama server (https://ollama.com) running an open-source
    model -- no API key, no external network call, so it stays true to the
    sovereignty pitch while still giving a real model response to test
    against (unlike `_local_process`, which is pattern matching, not a
    model). Requires `ollama pull <model>` and `ollama serve` beforehand.
    """
    import httpx

    try:
        resp = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except httpx.ConnectError:
        return (
            f"[AI_PROVIDER_NOT_CONFIGURED] Could not reach Ollama at {settings.ollama_base_url}. "
            f"Run `ollama serve` and `ollama pull {settings.ollama_model}` first."
        )
    except Exception as e:
        return f"[AI_ERROR] Ollama call failed: {str(e)}"


def _local_process(prompt: str) -> str:
    lower = prompt.lower()
    if "vulnerab" in lower or "cve" in lower:
        return "[LOCAL] Vulnerability pattern detected. Recommend: patch immediately, restrict network access, and review with a human analyst before acting."
    if "secret" in lower or "key" in lower or "token" in lower:
        return "[LOCAL] Credential pattern detected. Recommend: rotate credentials, restrict access, and audit logs."
    if "scan" in lower or "assess" in lower:
        return "[LOCAL] Scan context detected. Recommend: prioritize high-severity findings, verify with manual testing."
    return "[LOCAL] Content kept on-premises. No external model was consulted. Review with human analyst for security decisions."
