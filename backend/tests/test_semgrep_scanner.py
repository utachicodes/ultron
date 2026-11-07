from __future__ import annotations

"""Tests for app/semgrep_scanner.py and its integration into
app.code_scanner.scan_directory.

These run for real against the actual `semgrep` CLI (not mocked) when it's
installed, and skip gracefully otherwise -- semgrep is an optional
dependency (see README/TODO), and a missing optional dependency should
never fail the suite.
"""

import tempfile
from pathlib import Path

import pytest

from app import code_scanner, semgrep_scanner

requires_semgrep = pytest.mark.skipif(
    not semgrep_scanner.is_available(), reason="semgrep is not installed in this environment"
)

FASTAPI_SAMPLE = (
    "from fastapi import APIRouter, Depends\n\n"
    "router = APIRouter()\n\n"
    "@router.get('/admin/users')\n"
    "def list_users():\n"
    "    return db.query(User).all()\n\n"
    "@router.get('/me')\n"
    "def get_me(current_user = Depends(get_current_user)):\n"
    "    return current_user\n"
)

SQL_INJECTION_SAMPLE = (
    "def get_user(conn, user_id):\n"
    "    cursor = conn.cursor()\n"
    '    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n'
    "    return cursor.fetchone()\n\n"
    "def get_user_safe(conn, user_id):\n"
    "    cursor = conn.cursor()\n"
    '    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
    "    return cursor.fetchone()\n"
)


def test_is_available_returns_a_bool():
    assert isinstance(semgrep_scanner.is_available(), bool)


@requires_semgrep
def test_flags_fastapi_route_missing_depends_only():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "views.py").write_text(FASTAPI_SAMPLE)
        issues = semgrep_scanner.scan_directory(tmp)

    assert len(issues) == 1
    assert issues[0]["issue_type"] == "fastapi-route-missing-authz-dependency"
    assert issues[0]["line_number"] == 5
    assert issues[0]["severity"] == "medium"


@requires_semgrep
def test_flags_sql_injection_fstring_only():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "db.py").write_text(SQL_INJECTION_SAMPLE)
        issues = semgrep_scanner.scan_directory(tmp)

    assert len(issues) == 1
    assert issues[0]["issue_type"] == "sql-injection-fstring-execute"
    assert issues[0]["line_number"] == 3
    assert issues[0]["severity"] == "high"


def test_scan_directory_falls_back_gracefully_when_unavailable(monkeypatch):
    monkeypatch.setattr(semgrep_scanner, "is_available", lambda: False)
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "views.py").write_text(FASTAPI_SAMPLE)
        issues = semgrep_scanner.scan_directory(tmp)
    assert issues == [{"error": "semgrep is not installed -- falling back to regex-based detectors only"}]


@requires_semgrep
def test_code_scanner_scan_directory_merges_semgrep_and_skips_duplicate_heuristic():
    """With semgrep available, a Python file's missing-authz route should be
    flagged exactly once (by semgrep's precise rule), not twice (heuristic
    + semgrep)."""
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "views.py").write_text(FASTAPI_SAMPLE)
        issues = code_scanner.scan_directory(tmp)

    missing_authz_issues = [
        i for i in issues if i["issue_type"] in ("missing_authz_check", "fastapi-route-missing-authz-dependency")
    ]
    assert len(missing_authz_issues) == 1
    assert missing_authz_issues[0]["issue_type"] == "fastapi-route-missing-authz-dependency"
    assert missing_authz_issues[0]["file_path"] == "views.py"


def test_code_scanner_scan_directory_uses_heuristic_when_semgrep_unavailable(monkeypatch):
    import app.semgrep_scanner as sg

    monkeypatch.setattr(sg, "is_available", lambda: False)
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "views.py").write_text(FASTAPI_SAMPLE)
        issues = code_scanner.scan_directory(tmp)

    missing_authz_issues = [i for i in issues if i["issue_type"] == "missing_authz_check"]
    assert len(missing_authz_issues) == 1
