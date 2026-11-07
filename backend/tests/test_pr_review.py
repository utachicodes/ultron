from __future__ import annotations

"""Tests for the PR review engine (app/pr_review.py) -- diff-aware pattern
detection and comment rendering, no GitHub API involved."""

from app.pr_review import _added_lines, analyze_pr_files, build_review_comment, build_review_diagram


SAMPLE_PATCH = (
    "@@ -1,4 +1,6 @@\n"
    " import os\n"
    "+import requests\n"
    "+API_KEY = \"sk-abcdef1234567890\"\n"
    " def handler():\n"
    "-    return old()\n"
    "+    return new()\n"
)


def test_added_lines_tracks_new_file_line_numbers():
    lines = _added_lines(SAMPLE_PATCH)
    # Hunk starts at new-file line 1; context line 1 is "import os" (unchanged,
    # not returned), then two added lines at 2 and 3, a context line at 4
    # ("def handler():"), then an added line replacing the removed one at 5.
    assert lines == [
        (2, "import requests"),
        (3, 'API_KEY = "sk-abcdef1234567890"'),
        (5, "    return new()"),
    ]


def test_added_lines_handles_empty_patch():
    assert _added_lines("") == []
    assert _added_lines(None or "") == []


def test_analyze_pr_files_flags_secret_and_ranks_by_severity():
    files = [{"filename": "app/config.py", "patch": SAMPLE_PATCH}]
    findings = analyze_pr_files(files)

    assert len(findings) == 1
    f = findings[0]
    assert f["file_path"] == "app/config.py"
    assert f["line_number"] == 3
    assert f["issue_type"] == "hardcoded_secret"
    assert f["severity"] == "high"
    assert "fix" in f["suggested_fix"].lower() or f["suggested_fix"]


def test_analyze_pr_files_ignores_removed_and_unchanged_lines():
    patch = (
        "@@ -1,2 +1,2 @@\n"
        "-API_KEY = \"sk-oldsecretvalue1\"\n"
        "+print('hello')\n"
    )
    files = [{"filename": "f.py", "patch": patch}]
    findings = analyze_pr_files(files)
    # The secret is on a removed line, not an added one -- not a PR-introduced risk.
    assert findings == []


def test_analyze_pr_files_multiple_files_ranked_most_severe_first():
    files = [
        {
            "filename": "a.py",
            "patch": "@@ -1,1 +1,2 @@\n import os\n+debug = True\n",
        },
        {
            "filename": "b.py",
            "patch": "@@ -1,1 +1,2 @@\n import os\n+API_KEY = \"sk-1234567890abcd\"\n",
        },
    ]
    findings = analyze_pr_files(files)
    assert len(findings) == 2
    # hardcoded_secret (high) ranks above debug_mode_enabled (medium).
    assert findings[0]["issue_type"] == "hardcoded_secret"
    assert findings[1]["issue_type"] == "debug_mode_enabled"


def test_build_review_comment_empty_and_nonempty():
    assert "no risk patterns" in build_review_comment("My PR", [])

    findings = [
        {
            "file_path": "a.py",
            "line_number": 3,
            "severity": "high",
            "summary": "Potential hardcoded secret",
            "suggested_fix": "Use environment variables.",
        }
    ]
    body = build_review_comment("My PR", findings)
    assert "My PR" in body
    assert "HIGH" in body
    assert "a.py:3" in body
    assert "Use environment variables." in body


def test_build_review_diagram_empty_without_files():
    assert build_review_diagram([], []) == ""


def test_build_review_diagram_includes_every_file_and_marks_severity():
    files = [{"filename": "a.py"}, {"filename": "b.py"}]
    findings = [
        {"file_path": "a.py", "severity": "critical"},
        {"file_path": "a.py", "severity": "low"},  # worst for a.py must still be critical
    ]
    diagram = build_review_diagram(files, findings)
    assert diagram.startswith("```mermaid")
    assert diagram.endswith("```")
    assert "a.py [CRITICAL]" in diagram
    assert "b.py" in diagram
    assert "fill:#f66" in diagram  # critical styling present
    assert "f66" not in diagram.split("b.py")[1].split("\n")[0]  # b.py (no findings) isn't styled red


def test_build_review_comment_includes_diagram_for_mermaid_providers_only():
    files = [{"filename": "a.py"}]
    findings = [
        {"file_path": "a.py", "line_number": 1, "severity": "high", "summary": "x", "suggested_fix": "y"}
    ]
    github_body = build_review_comment("My PR", findings, files=files, provider="github")
    assert "```mermaid" in github_body

    forgejo_body = build_review_comment("My PR", findings, files=files, provider="forgejo")
    assert "```mermaid" in forgejo_body

    bitbucket_body = build_review_comment("My PR", findings, files=files, provider="bitbucket")
    assert "```mermaid" not in bitbucket_body
    assert "My PR" in bitbucket_body  # findings text is still there


def test_build_review_comment_without_files_has_no_diagram():
    body = build_review_comment("My PR", [], files=None, provider="github")
    assert "```mermaid" not in body
