from __future__ import annotations

"""AI-generated code scanning engine.

Detects patterns common in AI-assisted code: hardcoded secrets, insecure
defaults, vulnerable dependencies, logic flaws. Can scan a directory or
process uploaded code content.
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Any
from pathlib import Path


# --- Detection rules ---

SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|password|passwd|pwd|token|auth[_-]?)\s*[:=]\s*[\'"][^\'"]{8,}[\'"]'), "hardcoded_secret"),
    (re.compile(r'\b(sk|pk|wh|ghp|gho|xoxb|xoxp|xoxc)-[A-Za-z0-9]{12,}\b'), "hardcoded_api_key"),
    (re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----'), "private_key_exposed"),
    (re.compile(r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]'), "aws_credential"),
]

INSECURE_DEFAULT_PATTERNS = [
    (re.compile(r'(?i)debug\s*=\s*true'), "debug_mode_enabled"),
    (re.compile(r'(?i)verify\s*=\s*false'), "ssl_verification_disabled"),
    (re.compile(r'(?i)cors\s*\*\s*'), "wildcard_cors"),
    (re.compile(r'(?i)0\.0\.0\.0/\d+'), "open_network_access"),
    (re.compile(r'(?i)allow_all\s*=\s*true'), "permissive_access_control"),
]

VULNERABLE_DEP_PATTERNS = [
    (re.compile(r'(?i)requests\s*[<>=!]+\s*2\.[0-2]\.'), "outdated_requests_library"),
    (re.compile(r'(?i)django\s*[<>=!]+\s*3\.[01]\.'), "outdated_django"),
    (re.compile(r'(?i)flask\s*[<>=!]+\s*2\.[0-2]\.'), "outdated_flask"),
    (re.compile(r'(?i)yaml\.load\('), "unsafe_yaml_load"),
    (re.compile(r'(?i)pickle\.loads\('), "unsafe_pickle_load"),
    (re.compile(r'(?i)eval\('), "dangerous_eval"),
    (re.compile(r'(?i)exec\('), "dangerous_exec"),
    (re.compile(r'(?i)os\.system\('), "command_injection_risk"),
    (re.compile(r'(?i)subprocess\.call\(.*shell\s*=\s*true'), "shell_injection_risk"),
]

LOGIC_FLAW_PATTERNS = [
    (re.compile(r'(?i)if\s+True\s*:'), "always_true_condition"),
    (re.compile(r'(?i)except\s+Exception\s*:\s*pass'), "silent_exception_swallowing"),
    (re.compile(r'(?i)#\s*TODO.*security|#\s*FIXME.*security|#\s*HACK.*security'), "security_todo_comment"),
]

# Missing-authorization-check detection. This is a heuristic signal, not a
# proof (unlike authz_hunter's role-replay findings): it flags a route
# definition that has no visible auth check within a short window of its
# own definition, which is a reasonable first-pass signal but not
# conclusive -- the check could live in shared middleware the window
# doesn't see. Severity is "medium" for exactly that reason; a human should
# confirm before treating it as a real gap.
#
# Framework coverage is deliberately broad rather than deep: FastAPI/Flask-
# style route decorators (Python), Express-style route calls (JS/TS), and
# Spring MVC mapping annotations (Java) cover the stacks Ultron's own code
# scanner and PR reviewer already see in practice.
ROUTE_DEFINITION_PATTERNS = [
    re.compile(r'^\s*@(?:\w+\.)?(?:get|post|put|patch|delete)\s*\('),  # FastAPI/Flask decorators
    re.compile(r'^\s*(?:app|router)\.(?:get|post|put|patch|delete)\s*\('),  # Express-style
    re.compile(r'^\s*@(?:Get|Post|Put|Patch|Delete|Request)Mapping\s*\('),  # Spring MVC
]

AUTH_CHECK_KEYWORDS_PATTERN = re.compile(
    r'(?i)depends\(\s*(get_current_user|require_role|auth)|'
    r'login_required|is_authenticated|requires_auth|'
    r'permission_classes|preauthorize|current_user\s*:|'
    r'authorization|authenticate|jwt_required|@auth\.|'
    r'auth'  # catches requireAuth, authMiddleware, AuthGuard, etc. (substring, case-insensitive)
)

# How many lines after a route definition to look for an auth check before
# concluding there isn't one nearby -- covers the decorator line itself,
# the function signature (where a FastAPI `Depends(...)` parameter lives),
# and the first few lines of the handler body. Also looks a few lines
# *before* the route definition, since a stacked security annotation
# (e.g. Spring's @PreAuthorize above @GetMapping) commonly precedes it.
_AUTHZ_LOOKAHEAD_LINES = 12
_AUTHZ_LOOKBEHIND_LINES = 3


def _detect_missing_authz_checks(lines: List[str]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    route_indices = [
        i for i, line in enumerate(lines) if any(p.match(line) for p in ROUTE_DEFINITION_PATTERNS)
    ]

    for idx, i in enumerate(route_indices):
        # Clip the window at the previous/next route definition so an
        # adjacent route's own auth check (or lack of one) never leaks into
        # this route's result -- routes sitting a few lines apart in the
        # same file are common and must be judged independently.
        prev_route_end = route_indices[idx - 1] + 1 if idx > 0 else 0
        next_route_start = route_indices[idx + 1] if idx + 1 < len(route_indices) else len(lines)

        backward_start = max(i - _AUTHZ_LOOKBEHIND_LINES, prev_route_end)
        forward_end = min(i + _AUTHZ_LOOKAHEAD_LINES, next_route_start)

        window = lines[backward_start:forward_end]
        if AUTH_CHECK_KEYWORDS_PATTERN.search("\n".join(window)):
            continue

        issues.append(
            {
                "line_number": i + 1,
                "issue_type": "missing_authz_check",
                "severity": "medium",
                "description": (
                    f"Route definition on line {i + 1} has no visible authorization/"
                    "authentication check within its own definition -- may allow "
                    "unauthenticated or unauthorized access if one isn't enforced "
                    "elsewhere (e.g. shared middleware)."
                ),
                "remediation": _get_remediation("missing_authz_check"),
                "code_snippet": lines[i].strip(),
            }
        )

    return issues


def _scan_file_content(
    content: str, file_path: str, skip_missing_authz_heuristic: bool = False
) -> List[Dict[str, Any]]:
    """Scan a single file's content for AI-code failure patterns.

    `skip_missing_authz_heuristic` is set by `scan_directory` for Python
    files when `semgrep_scanner` is available: its AST-aware
    `fastapi-route-missing-authz-dependency` rule supersedes the line-window
    heuristic here for that language, and running both would just double-
    report the same route.
    """
    issues: List[Dict[str, Any]] = []
    lines = content.splitlines()

    all_patterns = []
    all_patterns.extend([(p, t, "high") for p, t in SECRET_PATTERNS])
    all_patterns.extend([(p, t, "medium") for p, t in INSECURE_DEFAULT_PATTERNS])
    all_patterns.extend([(p, t, "high") for p, t in VULNERABLE_DEP_PATTERNS])
    all_patterns.extend([(p, t, "medium") for p, t in LOGIC_FLAW_PATTERNS])

    for i, line in enumerate(lines, start=1):
        for pattern, issue_type, default_severity in all_patterns:
            if pattern.search(line):
                issues.append({
                    "file_path": file_path,
                    "line_number": i,
                    "issue_type": issue_type,
                    "severity": default_severity,
                    "description": f"Potential {issue_type.replace('_', ' ')} detected on line {i}",
                    "remediation": _get_remediation(issue_type),
                    "code_snippet": line.strip(),
                })
                break  # One issue per line per pattern type

    if not skip_missing_authz_heuristic:
        for issue in _detect_missing_authz_checks(lines):
            issues.append({**issue, "file_path": file_path})

    return issues


def _get_remediation(issue_type: str) -> str:
    remediations = {
        "hardcoded_secret": "Move secrets to environment variables or a secrets manager.",
        "hardcoded_api_key": "Rotate the exposed key and store it in environment variables.",
        "private_key_exposed": "Remove private keys from source code; use secure key storage.",
        "aws_credential": "Use IAM roles or environment variables instead of hardcoded AWS keys.",
        "debug_mode_enabled": "Disable debug mode in production environments.",
        "ssl_verification_disabled": "Enable SSL/TLS certificate verification.",
        "wildcard_cors": "Restrict CORS to specific trusted origins.",
        "open_network_access": "Bind services to specific interfaces, not 0.0.0.0.",
        "permissive_access_control": "Implement principle of least privilege.",
        "outdated_requests_library": "Update the requests library to a patched version.",
        "outdated_django": "Update Django to a supported security release.",
        "outdated_flask": "Update Flask to a supported security release.",
        "unsafe_yaml_load": "Use yaml.safe_load() instead of yaml.load().",
        "unsafe_pickle_load": "Avoid pickle for untrusted data; use JSON or MessagePack.",
        "dangerous_eval": "Remove eval(); use ast.literal_eval() or a safe parser.",
        "dangerous_exec": "Remove exec(); use importlib or a safe module loader.",
        "command_injection_risk": "Avoid os.system(); use subprocess with argument lists.",
        "shell_injection_risk": "Avoid shell=True; pass commands as argument lists.",
        "always_true_condition": "Review and fix always-true conditional logic.",
        "silent_exception_swallowing": "Log exceptions instead of silently swallowing them.",
        "security_todo_comment": "Address the security TODO/FIXME comment before shipping.",
        "missing_authz_check": "Add an explicit authorization check (e.g. Depends(get_current_user)/@login_required/a permission check) to this route, or confirm it is intentionally public.",
    }
    return remediations.get(issue_type, "Review and remediate this issue.")


def scan_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Recursively scan a directory for AI-code failure patterns.

    Also runs `semgrep_scanner`'s bundled, AST-aware custom rules when
    semgrep is installed, merging its findings in alongside the regex ones
    (and skipping the regex missing-authz heuristic for Python files, since
    semgrep's version of that check is more precise for that language).
    Falls back to regex-only detection when semgrep isn't available --
    never fails the scan over a missing optional dependency.
    """
    from app import semgrep_scanner

    all_issues: List[Dict[str, Any]] = []
    root = Path(directory_path)

    if not root.exists():
        return [{"error": f"Directory not found: {directory_path}"}]

    semgrep_ready = semgrep_scanner.is_available()

    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.suffix in {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rb", ".php"}:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                relative_path = str(file_path.relative_to(root))
                issues = _scan_file_content(
                    content,
                    relative_path,
                    skip_missing_authz_heuristic=semgrep_ready and file_path.suffix == ".py",
                )
                all_issues.extend(issues)
            except Exception:
                continue

    if semgrep_ready:
        semgrep_issues = semgrep_scanner.scan_directory(directory_path)
        for issue in semgrep_issues:
            if "error" in issue:
                continue
            try:
                issue["file_path"] = str(Path(issue["file_path"]).resolve().relative_to(root.resolve()))
            except (ValueError, TypeError, KeyError):
                pass  # keep whatever path semgrep gave us rather than drop the finding
            all_issues.append(issue)

    return all_issues


def scan_content(content: str, file_name: str = "uploaded_file") -> List[Dict[str, Any]]:
    """Scan inline code content."""
    return _scan_file_content(content, file_name)


def run_code_scan(target: str, scan_type: str = "code") -> List[Dict[str, Any]]:
    """Dispatch code scanning. target can be a directory path or raw content."""
    if scan_type != "code":
        return [{"error": f"code_scanner only handles 'code' scan type, got: {scan_type}"}]

    # Check if target is a directory path
    if os.path.isdir(target):
        return scan_directory(target)

    # Otherwise treat as inline content
    return scan_content(target, file_name=target[:100] if len(target) > 100 else target)
