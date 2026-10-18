from __future__ import annotations

"""Data sanitization layer — sovereignty control.

Strips client names, IPs, credentials, API keys, JWTs, emails, phones,
SSNs, and credit cards before any data reaches an external AI model.
"""

import re
import hashlib
from typing import Tuple, Dict, Any


JWT_PATTERN = re.compile(
    r"\b[A-Za-z0-9\-_]*[A-Za-z][A-Za-z0-9\-_]*\.[A-Za-z0-9\-_]*[A-Za-z][A-Za-z0-9\-_]*\.[A-Za-z0-9\-_]*[A-Za-z][A-Za-z0-9\-_]*\b"
)
API_KEY_PATTERN = re.compile(r"\b(sk|pk|wh|ghp|gho|xoxb|xoxp|xoxc)-[A-Za-z0-9]{12,}\b")
IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CIDR_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CREDENTIAL_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|password|passwd|pwd|token|auth[_-]?)\s*[:=]\s*['\"]?([^\s'\"&]+)",
    re.IGNORECASE,
)
BEARER_TOKEN_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")


def hash_value(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def sanitize_text(text: str, client_name: str | None = None) -> Tuple[str, Dict[str, int]]:
    if not text:
        return text, {}

    stats: Dict[str, int] = {}
    result = text

    # IPs and CIDRs first (prevents JWT pattern from matching IP octets)
    def repl_ip(m):
        stats["ip_addresses"] = stats.get("ip_addresses", 0) + 1
        return "[IP_REDACTED]"

    result = CIDR_PATTERN.sub(repl_ip, result)
    result = IP_PATTERN.sub(repl_ip, result)

    # Credentials (key=value / key:value)
    def repl_cred(m):
        stats["credentials"] = stats.get("credentials", 0) + 1
        return f"{m.group(1)[:1]}***REDACTED***"

    result = CREDENTIAL_PATTERN.sub(repl_cred, result)

    # Bare API keys
    result = API_KEY_PATTERN.sub("[API_KEY_REDACTED]", result)
    stats["api_keys"] = stats.get("api_keys", 0) + len(API_KEY_PATTERN.findall(text))

    # Bearer tokens and JWTs
    result = BEARER_TOKEN_PATTERN.sub("[TOKEN_REDACTED]", result)
    result = JWT_PATTERN.sub("[JWT_REDACTED]", result)

    # Emails
    def repl_email(m):
        stats["emails"] = stats.get("emails", 0) + 1
        local, domain = m.group(0).split("@")
        return f"{local[:2]}***@{domain}"

    result = EMAIL_PATTERN.sub(repl_email, result)

    # Phone numbers
    result = PHONE_PATTERN.sub("[PHONE_REDACTED]", result)
    stats["phone_numbers"] = stats.get("phone_numbers", 0) + len(PHONE_PATTERN.findall(text))

    # SSNs and credit cards
    result = SSN_PATTERN.sub("[SSN_REDACTED]", result)
    result = CREDIT_CARD_PATTERN.sub("[CARD_REDACTED]", result)

    # Client name
    if client_name:
        result = result.replace(client_name, "[CLIENT_NAME_REDACTED]")
        stats["client_names"] = stats.get("client_names", 0) + result.count(
            "[CLIENT_NAME_REDACTED]"
        )

    return result, stats


def sanitize_dict(data: Dict[str, Any], client_name: str | None = None) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            clean_text, _ = sanitize_text(value, client_name)
            sanitized[key] = clean_text
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, client_name)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, client_name) if isinstance(item, dict)
                else sanitize_text(item, client_name)[0] if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def is_sanitized(text: str) -> bool:
    return not bool(
        CREDENTIAL_PATTERN.search(text)
        or BEARER_TOKEN_PATTERN.search(text)
        or IP_PATTERN.search(text)
    )
