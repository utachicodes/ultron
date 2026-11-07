from __future__ import annotations

"""Whitebox pull-request review: risk-ranked findings posted on the PR.

Fetches a pull request's diff, flags risky patterns introduced by its added
lines (reusing the same detectors as `app.code_scanner`: hardcoded secrets,
insecure defaults, vulnerable/dangerous calls, logic flaws), ranks them by
severity, and can post the result back to the PR as a single comment that
updates on re-run -- the "risk-ranked findings with a suggested fix, posted
inline on the PR" idea, without the animated diagram layer (a separate,
much larger investment) that a tool like prlens.dev adds on top.

Three providers are supported (`provider="github"` default, `"bitbucket"`,
or `"forgejo"`), since `repo` is `owner/name` on all three: GitHub and
Bitbucket Cloud are hosted at a fixed domain, Forgejo is normally
self-hosted so it additionally takes `host` (e.g.
"https://forgejo.example.sn"). GitHub goes through PyGithub; Bitbucket and
Forgejo go through their plain REST APIs via httpx, parsing the raw unified
diff they return into the same {filename, patch} shape GitHub's API gives
natively, so `analyze_pr_files` doesn't need to know which provider it came
from.

Only the PR's diff (added lines) is scanned, not the whole repository: a
pre-existing issue the PR doesn't touch is out of scope for a PR review.
Mutating the PR (posting a comment) only ever happens when the caller
explicitly asks for it -- `analyze_pull_request` never does so on its own.
An access token is only ever held in memory for the duration of one call;
it is never written to the database or the audit log.
"""

import re
from typing import Any, Dict, List, Optional

import httpx
from github import Github

from app.code_scanner import (
    INSECURE_DEFAULT_PATTERNS,
    LOGIC_FLAW_PATTERNS,
    SECRET_PATTERNS,
    VULNERABLE_DEP_PATTERNS,
    _get_remediation,
)

_ALL_PATTERNS = (
    [(p, t, "high") for p, t in SECRET_PATTERNS]
    + [(p, t, "medium") for p, t in INSECURE_DEFAULT_PATTERNS]
    + [(p, t, "high") for p, t in VULNERABLE_DEP_PATTERNS]
    + [(p, t, "medium") for p, t in LOGIC_FLAW_PATTERNS]
)

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")


def fetch_github_pull_request(repo_full_name: str, pr_number: int, token: str) -> Dict[str, Any]:
    """Fetch a PR's metadata and per-file unified diffs via the GitHub API."""
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    files = [
        {"filename": f.filename, "patch": getattr(f, "patch", None) or "", "status": f.status}
        for f in pr.get_files()
    ]
    return {"title": pr.title, "number": pr.number, "html_url": pr.html_url, "files": files}


# Kept for backward compatibility -- existing callers/tests reference this name.
fetch_pull_request = fetch_github_pull_request


def _parse_unified_diff(diff_text: str) -> List[Dict[str, str]]:
    """Split a full multi-file unified diff (as Bitbucket's/Forgejo's `.diff`
    endpoints return it) into per-file {filename, patch} dicts, the same
    shape GitHub's API gives natively so `analyze_pr_files` is
    provider-agnostic."""
    files: List[Dict[str, str]] = []
    current_filename: Optional[str] = None
    current_lines: List[str] = []

    def _flush() -> None:
        if current_filename is not None:
            files.append({"filename": current_filename, "patch": "\n".join(current_lines)})

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            _flush()
            current_lines = []
            b_path = line.rsplit(" ", 1)[-1]
            current_filename = b_path[2:] if b_path.startswith("b/") else b_path
        elif line.startswith("+++ ") or line.startswith("--- ") or line.startswith("index "):
            continue
        else:
            current_lines.append(line)
    _flush()

    return files


def _http_client_or_new(http_client: Optional[httpx.Client]):
    """Returns (client, owns_it) -- mirrors the pattern in authz_hunter so
    tests can inject a MockTransport-backed client."""
    if http_client is not None:
        return http_client, False
    return httpx.Client(timeout=15.0), True


def fetch_bitbucket_pull_request(
    repo_full_name: str,
    pr_number: int,
    token: str,
    http_client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """Fetch a PR's metadata and diff from Bitbucket Cloud's REST API.
    `repo_full_name` is "workspace/repo_slug"."""
    client, owns = _http_client_or_new(http_client)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base = f"https://api.bitbucket.org/2.0/repositories/{repo_full_name}/pullrequests/{pr_number}"

    try:
        meta = client.get(base, headers=headers)
        meta.raise_for_status()
        meta_body = meta.json()

        diff = client.get(f"{base}/diff", headers=headers)
        diff.raise_for_status()

        return {
            "title": meta_body.get("title", ""),
            "number": pr_number,
            "html_url": meta_body.get("links", {}).get("html", {}).get("href", ""),
            "files": _parse_unified_diff(diff.text),
        }
    finally:
        if owns:
            client.close()


def fetch_forgejo_pull_request(
    repo_full_name: str,
    pr_number: int,
    token: str,
    host: str,
    http_client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """Fetch a PR's metadata and diff from a (typically self-hosted) Forgejo
    or Gitea instance's REST API. `repo_full_name` is "owner/repo"."""
    client, owns = _http_client_or_new(http_client)
    headers = {"Authorization": f"token {token}"} if token else {}
    base = f"{host.rstrip('/')}/api/v1/repos/{repo_full_name}/pulls/{pr_number}"

    try:
        meta = client.get(base, headers=headers)
        meta.raise_for_status()
        meta_body = meta.json()

        diff = client.get(f"{base}.diff", headers=headers)
        diff.raise_for_status()

        return {
            "title": meta_body.get("title", ""),
            "number": pr_number,
            "html_url": meta_body.get("html_url", ""),
            "files": _parse_unified_diff(diff.text),
        }
    finally:
        if owns:
            client.close()


def _added_lines(patch: str) -> List[tuple]:
    """Yield (new_file_line_number, line_text) for every added line in a
    unified diff patch, as GitHub's API returns it on a PR file."""
    results: List[tuple] = []
    new_lineno: Optional[int] = None

    for line in patch.splitlines():
        header = _HUNK_HEADER.match(line)
        if header:
            new_lineno = int(header.group(1))
            continue
        if new_lineno is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            results.append((new_lineno, line[1:]))
            new_lineno += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue  # removed lines don't exist in the new file
        else:
            new_lineno += 1

    return results


def analyze_pr_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Scan only the added lines of each file's diff for risky patterns,
    one finding per matching added line, ranked most-severe first."""
    findings: List[Dict[str, Any]] = []

    for f in files:
        for line_number, text in _added_lines(f.get("patch") or ""):
            for pattern, issue_type, severity in _ALL_PATTERNS:
                if pattern.search(text):
                    findings.append(
                        {
                            "file_path": f["filename"],
                            "line_number": line_number,
                            "issue_type": issue_type,
                            "severity": severity,
                            "summary": f"Potential {issue_type.replace('_', ' ')} introduced by this PR",
                            "suggested_fix": _get_remediation(issue_type),
                            "code_snippet": text.strip(),
                        }
                    )
                    break  # one finding per line, first matching rule wins

    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f["severity"], 5))
    return findings


_MERMAID_ID_SAFE = re.compile(r"[^a-zA-Z0-9_]")


def _mermaid_safe_id(name: str) -> str:
    return "f_" + _MERMAID_ID_SAFE.sub("_", name)


def build_review_diagram(files: List[Dict[str, Any]], findings: List[Dict[str, Any]]) -> str:
    """Render a Mermaid flowchart showing which files this PR touched and
    their worst finding severity -- a reviewer sees the shape of the change
    before reading the diff. This is the zero-hosting-infra equivalent of
    prlens.dev's animated architecture diagrams: those need a typed
    scene-graph renderer and somewhere to host the output image, which this
    project doesn't have; a fenced ```mermaid block needs neither, and
    GitHub and Forgejo/Gitea both render it inline in a PR comment. Returns
    "" when there's nothing to draw (no changed files)."""
    if not files:
        return ""

    worst_by_file: Dict[str, str] = {}
    for f in findings:
        fp = f["file_path"]
        if fp not in worst_by_file or _SEVERITY_ORDER.get(f["severity"], 5) < _SEVERITY_ORDER.get(
            worst_by_file[fp], 5
        ):
            worst_by_file[fp] = f["severity"]

    lines = ["```mermaid", "flowchart LR", '  PR(("Pull Request"))']
    for f in files:
        filename = f["filename"]
        node_id = _mermaid_safe_id(filename)
        severity = worst_by_file.get(filename)
        label = filename if not severity else f"{filename} [{severity.upper()}]"
        lines.append(f'  PR --> {node_id}["{label}"]')
        if severity in ("critical", "high"):
            lines.append(f"  style {node_id} fill:#f66,stroke:#900,color:#fff")
        elif severity == "medium":
            lines.append(f"  style {node_id} fill:#fc6,stroke:#a60")
    lines.append("```")
    return "\n".join(lines)


# Providers whose PR comments actually render a ```mermaid fence inline.
# Bitbucket Cloud's comment renderer does not, so the diagram is skipped
# there rather than posted as unrendered noise.
_MERMAID_RENDERING_PROVIDERS = ("github", "forgejo")


def build_review_comment(
    pr_title: str,
    findings: List[Dict[str, Any]],
    files: Optional[List[Dict[str, Any]]] = None,
    provider: str = "github",
) -> str:
    """Render findings as a single Markdown comment body, risk-ranked, with
    a Mermaid diagram of the changed files prepended when `files` is given
    and the provider renders Mermaid inline."""
    parts: List[str] = []

    if files and provider in _MERMAID_RENDERING_PROVIDERS:
        diagram = build_review_diagram(files, findings)
        if diagram:
            parts.append(diagram)

    if not findings:
        parts.append(f"**Ultron PR Review** — no risk patterns detected in the added lines of `{pr_title}`.")
    else:
        lines = [f"**Ultron PR Review** — {len(findings)} finding(s) in `{pr_title}`, ranked by risk:", ""]
        for f in findings:
            lines.append(
                f"- **[{f['severity'].upper()}]** `{f['file_path']}:{f['line_number']}` — "
                f"{f['summary']}. _Suggested fix:_ {f['suggested_fix']}"
            )
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def post_pr_comment(repo_full_name: str, pr_number: int, github_token: str, body: str) -> None:
    """Post (or re-post) a review comment on a GitHub PR. Called only when
    the caller explicitly opts in -- never as a side effect of analysis
    alone."""
    gh = Github(github_token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(body)


def post_bitbucket_comment(
    repo_full_name: str,
    pr_number: int,
    token: str,
    body: str,
    http_client: Optional[httpx.Client] = None,
) -> None:
    client, owns = _http_client_or_new(http_client)
    try:
        url = f"https://api.bitbucket.org/2.0/repositories/{repo_full_name}/pullrequests/{pr_number}/comments"
        resp = client.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={"content": {"raw": body}},
        )
        resp.raise_for_status()
    finally:
        if owns:
            client.close()


def post_forgejo_comment(
    repo_full_name: str,
    pr_number: int,
    token: str,
    body: str,
    host: str,
    http_client: Optional[httpx.Client] = None,
) -> None:
    client, owns = _http_client_or_new(http_client)
    try:
        url = f"{host.rstrip('/')}/api/v1/repos/{repo_full_name}/issues/{pr_number}/comments"
        resp = client.post(url, headers={"Authorization": f"token {token}"}, json={"body": body})
        resp.raise_for_status()
    finally:
        if owns:
            client.close()


SUPPORTED_PROVIDERS = ("github", "bitbucket", "forgejo")


def analyze_pull_request(
    repo_full_name: str,
    pr_number: int,
    token: str,
    post_comment: bool = False,
    provider: str = "github",
    host: Optional[str] = None,
    http_client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """Fetch, analyze, and (optionally) comment on a pull request in one
    call, on whichever `provider` is declared."""
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported provider: {provider!r} (expected one of {SUPPORTED_PROVIDERS})")
    if provider == "forgejo" and not host:
        raise ValueError("host is required for provider='forgejo'")

    if provider == "github":
        pr = fetch_github_pull_request(repo_full_name, pr_number, token)
    elif provider == "bitbucket":
        pr = fetch_bitbucket_pull_request(repo_full_name, pr_number, token, http_client=http_client)
    else:
        pr = fetch_forgejo_pull_request(repo_full_name, pr_number, token, host, http_client=http_client)

    findings = analyze_pr_files(pr["files"])

    comment_posted = False
    if post_comment:
        body = build_review_comment(pr["title"], findings, files=pr["files"], provider=provider)
        if provider == "github":
            post_pr_comment(repo_full_name, pr_number, token, body)
        elif provider == "bitbucket":
            post_bitbucket_comment(repo_full_name, pr_number, token, body, http_client=http_client)
        else:
            post_forgejo_comment(repo_full_name, pr_number, token, body, host, http_client=http_client)
        comment_posted = True

    return {
        "title": pr["title"],
        "html_url": pr["html_url"],
        "files_changed": len(pr["files"]),
        "findings": findings,
        "comment_posted": comment_posted,
    }
