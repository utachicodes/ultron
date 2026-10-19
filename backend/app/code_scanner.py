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


def _scan_file_content(content: str, file_path: str) -> List[Dict[str, Any]]:
    """Scan a single file's content for AI-code failure patterns."""
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
    }
    return remediations.get(issue_type, "Review and remediate this issue.")


def scan_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Recursively scan a directory for AI-code failure patterns."""
    all_issues: List[Dict[str, Any]] = []
    root = Path(directory_path)

    if not root.exists():
        return [{"error": f"Directory not found: {directory_path}"}]

    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.suffix in {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rb", ".php"}:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                relative_path = str(file_path.relative_to(root))
                issues = _scan_file_content(content, relative_path)
                all_issues.extend(issues)
            except Exception:
                continue

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
