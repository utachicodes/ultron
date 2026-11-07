from __future__ import annotations

"""OpenGrep/Semgrep-based static analysis: custom AST-aware rules.

`code_scanner.py`'s regex rules are line-oriented and intentionally simple;
they can't reliably express "this FastAPI route has no Depends(...)
parameter" or "this f-string is passed straight into cursor.execute()"
without false positives/negatives, because those require understanding
code structure (function signatures, call arguments), not just matching a
line. This module runs the `semgrep` CLI (OpenGrep-rule-compatible syntax)
against a small set of custom rules bundled in `app/semgrep_rules/` to
cover exactly those cases -- verified against real sample code, not just
written and hoped to work.

Fully optional: `is_available()` returns False if the `semgrep` binary
isn't on PATH, and every caller falls back to the regex-based detectors in
`code_scanner.py` in that case rather than failing. No network calls are
made at scan time -- the ruleset is local, bundled with the app.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

RULES_DIR = Path(__file__).resolve().parent / "semgrep_rules"

_SEVERITY_MAP = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}


def is_available() -> bool:
    """Whether the `semgrep` CLI is installed and on PATH."""
    return shutil.which("semgrep") is not None


def _run_semgrep(target_path: str, timeout: int = 60) -> Dict[str, Any]:
    cmd = ["semgrep", "--config", str(RULES_DIR), "--json", "--quiet", "--no-git-ignore", target_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    # semgrep exits 1 when it successfully ran and found matches, not an error.
    if result.returncode not in (0, 1):
        raise RuntimeError(f"semgrep exited {result.returncode}: {result.stderr[:500]}")
    return json.loads(result.stdout or "{}")


def _normalize_result(r: Dict[str, Any]) -> Dict[str, Any]:
    extra = r.get("extra", {})
    metadata = extra.get("metadata", {})
    check_id = r.get("check_id", "")
    issue_type = check_id.rsplit(".", 1)[-1]  # drop the config-path prefix semgrep adds

    return {
        "file_path": r.get("path"),
        "line_number": r.get("start", {}).get("line"),
        "issue_type": issue_type,
        "severity": _SEVERITY_MAP.get(extra.get("severity", "WARNING"), "medium"),
        "description": extra.get("message", "").strip(),
        "remediation": metadata.get("remediation", "Review and remediate per the rule's guidance."),
        "code_snippet": (extra.get("lines") or "").strip(),
    }


def scan_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Scan a directory with the bundled custom rules. Returns `[{"error":
    ...}]` (matching code_scanner's error shape) if semgrep isn't
    available or the run fails, rather than raising."""
    if not is_available():
        return [{"error": "semgrep is not installed -- falling back to regex-based detectors only"}]
    try:
        data = _run_semgrep(directory_path)
    except Exception as exc:
        return [{"error": str(exc)}]

    return [_normalize_result(r) for r in data.get("results", [])]


def scan_content(content: str, file_name: str = "snippet.py") -> List[Dict[str, Any]]:
    """Scan inline content by writing it to a temp file -- semgrep operates
    on files/directories, not raw strings."""
    if not is_available():
        return [{"error": "semgrep is not installed -- falling back to regex-based detectors only"}]

    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        results = scan_directory(tmp)

    # Paths come back rooted in the temp dir; report the caller-given name instead.
    for r in results:
        if "file_path" in r:
            r["file_path"] = file_name
    return results
