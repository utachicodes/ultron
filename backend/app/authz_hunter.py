from __future__ import annotations

"""Autonomous authorization (IDOR/BOLA) hunter.

Proves broken object-level authorization the way a human pentester (or
Wakefield's own blackbox agent) would: log in as two or more roles, take an
object id that belongs to one role, and replay the exact same request as
every other role to see whether the response leaks the same data. The
classic example this automates is `GET /api/invoices/1024` -> change the id
to `1025` and see if someone else's invoice comes back.

Scope and safety:
- Every request target is built from an operator-declared `base_url` plus
  operator-declared path templates and id values -- this module never
  crawls, never discovers resource ids on its own, and never issues
  mutating requests on its own initiative (callers choose the HTTP method,
  but the intended and only tested use is read methods against declared
  probes).
- Credentials (role headers) are redacted before being stored as evidence;
  only the request/response shape is kept.
- A `confirmed_leak` verdict is a strong automated signal, not a verified
  report -- the caller (see `app/routers/authz.py`) still requires a named
  human analyst to review each finding before it is shared with a client,
  the same gate already enforced on `Finding`.
"""

import difflib
from typing import Any, Dict, List, Optional

import httpx

SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "x-auth-token",
}

# Statuses that represent a believable "access denied" response. Anything
# else on a 200 needs a body-similarity check before it can be trusted.
DENY_STATUS_CODES = {400, 401, 403, 404}

SIMILARITY_LEAK_THRESHOLD = 0.6


def _redact_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    return {
        k: ("[REDACTED]" if k.lower() in SENSITIVE_HEADER_NAMES else v)
        for k, v in (headers or {}).items()
    }


def _build_url(base_url: str, path_template: str, id_param: str, value: str) -> str:
    path = path_template.replace("{" + id_param + "}", str(value))
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _request(
    http_client: httpx.Client, method: str, url: str, headers: Dict[str, str]
) -> Dict[str, Any]:
    try:
        resp = http_client.request(method.upper(), url, headers=headers)
        return {
            "status_code": resp.status_code,
            "body": resp.text[:4000],
            "error": None,
        }
    except Exception as exc:
        return {"status_code": None, "body": None, "error": str(exc)}


def _body_similarity(a: Optional[str], b: Optional[str]) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _classify(baseline: Dict[str, Any], attempt: Dict[str, Any]) -> Dict[str, Any]:
    if baseline.get("error") or attempt.get("error"):
        return {
            "verdict": "probe_error",
            "confidence": 0.0,
            "reason": f"request failed: {baseline.get('error') or attempt.get('error')}",
        }

    if baseline["status_code"] != 200:
        return {
            "verdict": "inconclusive",
            "confidence": 0.0,
            "reason": (
                f"owner baseline request returned HTTP {baseline['status_code']}, "
                "so ownership of this resource could not be established"
            ),
        }

    status = attempt["status_code"]
    if status in DENY_STATUS_CODES:
        return {
            "verdict": "no_leak",
            "confidence": 0.9,
            "reason": f"other role was denied access (HTTP {status})",
        }

    if status == 200:
        similarity = _body_similarity(baseline.get("body"), attempt.get("body"))
        if similarity >= SIMILARITY_LEAK_THRESHOLD:
            return {
                "verdict": "confirmed_leak",
                "confidence": round(similarity, 2),
                "reason": (
                    f"other role received HTTP 200 with a response body "
                    f"{round(similarity * 100)}% similar to the resource owner's own "
                    "response -- cross-tenant data appears accessible"
                ),
            }
        return {
            "verdict": "inconclusive",
            "confidence": round(similarity, 2),
            "reason": (
                "other role received HTTP 200 but the response body differs "
                "substantially from the owner's -- may be a different or empty "
                "resource; review the evidence manually"
            ),
        }

    return {
        "verdict": "inconclusive",
        "confidence": 0.0,
        "reason": f"unexpected status code {status} from the other role's request",
    }


def _severity_for(verdict: str) -> str:
    return {
        "confirmed_leak": "critical",
        "inconclusive": "medium",
        "no_leak": "info",
        "probe_error": "info",
    }.get(verdict, "info")


def fetch_openapi_spec(spec_url: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Fetch and parse an OpenAPI/Swagger spec from a URL (JSON only)."""
    resp = httpx.get(spec_url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _looks_like_id_param(name: str, schema: Optional[Dict[str, Any]]) -> bool:
    lname = name.lower()
    if lname == "id" or lname.endswith("_id") or lname.endswith("id"):
        return True
    if schema and schema.get("format") == "uuid":
        return True
    return False


def suggest_probes_from_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scan an OpenAPI spec for GET endpoints with an id-shaped path
    parameter and return probe skeletons an operator can fill in with real
    `owner_role`/`owner_value` data.

    Deliberately GET-only and read-only: this is discovery, not execution --
    it never issues a single HTTP request itself. The operator still has to
    supply real ids before `run_authz_hunt` can replay anything.
    """
    suggestions: List[Dict[str, Any]] = []
    paths = spec.get("paths") or {}

    for path, path_item in paths.items():
        if "{" not in path or not isinstance(path_item, dict):
            continue

        path_level_params = path_item.get("parameters") or []

        for method, operation in path_item.items():
            if method.lower() != "get" or not isinstance(operation, dict):
                continue

            op_params = operation.get("parameters") or []
            seen_names = set()

            for param in list(op_params) + list(path_level_params):
                if not isinstance(param, dict) or param.get("in") != "path":
                    continue
                name = param.get("name", "")
                if not name or name in seen_names:
                    continue
                seen_names.add(name)

                if _looks_like_id_param(name, param.get("schema")):
                    suggestions.append(
                        {
                            "method": "GET",
                            "path": path,
                            "id_param": name,
                            "description": (
                                operation.get("summary")
                                or operation.get("operationId")
                                or f"GET {path}"
                            ),
                        }
                    )

    return suggestions


def run_authz_hunt(
    base_url: str,
    roles: List[Dict[str, Any]],
    probes: List[Dict[str, Any]],
    http_client: Optional[httpx.Client] = None,
) -> List[Dict[str, Any]]:
    """Replay each probe as its owning role (baseline), then as every other
    declared role, and classify whether cross-role access leaks the same
    resource.

    Returns one result dict per (probe, other role) pair:
    {method, path, owner_role, tested_role, verdict, confidence, severity,
     reason, evidence}.

    `http_client` lets callers (tests) inject an `httpx.Client` backed by a
    mock transport; by default a real client is created and closed here.
    """
    role_headers = {r["name"]: (r.get("headers") or {}) for r in roles}
    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=10.0)
    results: List[Dict[str, Any]] = []

    try:
        for probe in probes:
            method = probe.get("method", "GET")
            path = probe["path"]
            id_param = probe["id_param"]
            owner_role = probe["owner_role"]
            owner_value = probe["owner_value"]

            if owner_role not in role_headers:
                results.append(
                    {
                        "method": method,
                        "path": path,
                        "owner_role": owner_role,
                        "tested_role": owner_role,
                        "verdict": "probe_error",
                        "confidence": 0.0,
                        "severity": "info",
                        "reason": f"owner_role '{owner_role}' is not among the declared roles",
                        "evidence": {},
                    }
                )
                continue

            url = _build_url(base_url, path, id_param, owner_value)
            baseline = _request(client, method, url, role_headers[owner_role])

            for role_name, headers in role_headers.items():
                if role_name == owner_role:
                    continue

                attempt = _request(client, method, url, headers)
                verdict_info = _classify(baseline, attempt)

                results.append(
                    {
                        "method": method,
                        "path": path,
                        "owner_role": owner_role,
                        "tested_role": role_name,
                        "verdict": verdict_info["verdict"],
                        "confidence": verdict_info["confidence"],
                        "severity": _severity_for(verdict_info["verdict"]),
                        "reason": verdict_info["reason"],
                        "evidence": {
                            "url": url,
                            "baseline_request": {
                                "role": owner_role,
                                "headers": _redact_headers(role_headers[owner_role]),
                            },
                            "baseline_response": {
                                "status_code": baseline["status_code"],
                                "body_preview": baseline.get("body"),
                            },
                            "attempt_request": {
                                "role": role_name,
                                "headers": _redact_headers(headers),
                            },
                            "attempt_response": {
                                "status_code": attempt["status_code"],
                                "body_preview": attempt.get("body"),
                            },
                        },
                    }
                )
    finally:
        if owns_client:
            client.close()

    return results
