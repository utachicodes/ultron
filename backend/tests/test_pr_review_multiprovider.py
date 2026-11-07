from __future__ import annotations

"""Tests for Bitbucket and Forgejo support in app/pr_review.py -- the diff
parsing is provider-agnostic, so these confirm `_parse_unified_diff` plus
the fetch/comment calls against each provider's REST shape, using
httpx.MockTransport (no real network)."""

import httpx

from app import pr_review

RAW_DIFF = (
    "diff --git a/app/webhook.py b/app/webhook.py\n"
    "index 1111111..2222222 100644\n"
    "--- a/app/webhook.py\n"
    "+++ b/app/webhook.py\n"
    "@@ -1,1 +1,2 @@\n"
    " import os\n"
    "+API_KEY = \"sk-1234567890abcd\"\n"
    "diff --git a/app/other.py b/app/other.py\n"
    "index 3333333..4444444 100644\n"
    "--- a/app/other.py\n"
    "+++ b/app/other.py\n"
    "@@ -2,1 +2,2 @@\n"
    " x = 1\n"
    "+debug = True\n"
)


def test_parse_unified_diff_splits_into_per_file_patches():
    files = pr_review._parse_unified_diff(RAW_DIFF)
    assert [f["filename"] for f in files] == ["app/webhook.py", "app/other.py"]
    assert "API_KEY" in files[0]["patch"]
    assert "debug = True" in files[1]["patch"]
    # Header noise never leaks into the patch body analyze_pr_files sees.
    assert "diff --git" not in files[0]["patch"]
    assert "index " not in files[0]["patch"]


def test_parse_unified_diff_feeds_analyze_pr_files_correctly():
    files = pr_review._parse_unified_diff(RAW_DIFF)
    findings = pr_review.analyze_pr_files(files)
    issue_types = {f["issue_type"] for f in findings}
    assert "hardcoded_secret" in issue_types
    assert "debug_mode_enabled" in issue_types


def _bitbucket_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path.endswith("/diff"):
        return httpx.Response(200, text=RAW_DIFF)
    if request.method == "GET":
        return httpx.Response(
            200,
            json={"title": "Add webhook", "links": {"html": {"href": "https://bitbucket.org/acme/app/pull-requests/5"}}},
        )
    if request.method == "POST" and request.url.path.endswith("/comments"):
        return httpx.Response(201, json={"id": 1})
    return httpx.Response(404)


def test_fetch_and_analyze_bitbucket_pull_request():
    with httpx.Client(transport=httpx.MockTransport(_bitbucket_handler)) as c:
        result = pr_review.analyze_pull_request(
            "acme/app", 5, "token123", provider="bitbucket", http_client=c
        )
    assert result["title"] == "Add webhook"
    assert result["html_url"].endswith("/pull-requests/5")
    assert result["files_changed"] == 2
    assert any(f["issue_type"] == "hardcoded_secret" for f in result["findings"])


def test_bitbucket_posts_comment_when_requested():
    posted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posted.append(request)
            return httpx.Response(201, json={"id": 1})
        return _bitbucket_handler(request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        result = pr_review.analyze_pull_request(
            "acme/app", 5, "token123", post_comment=True, provider="bitbucket", http_client=c
        )
    assert result["comment_posted"] is True
    assert len(posted) == 1


def _forgejo_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path.endswith(".diff"):
        return httpx.Response(200, text=RAW_DIFF)
    if request.method == "GET":
        return httpx.Response(
            200, json={"title": "Add webhook", "html_url": "https://forgejo.example.sn/acme/app/pulls/3"}
        )
    if request.method == "POST" and "/issues/" in request.url.path:
        return httpx.Response(201, json={"id": 1})
    return httpx.Response(404)


def test_fetch_and_analyze_forgejo_pull_request():
    with httpx.Client(transport=httpx.MockTransport(_forgejo_handler)) as c:
        result = pr_review.analyze_pull_request(
            "acme/app",
            3,
            "token123",
            provider="forgejo",
            host="https://forgejo.example.sn",
            http_client=c,
        )
    assert result["title"] == "Add webhook"
    assert result["html_url"].endswith("/pulls/3")
    assert any(f["issue_type"] == "hardcoded_secret" for f in result["findings"])


def test_forgejo_requires_host():
    import pytest

    with pytest.raises(ValueError):
        pr_review.analyze_pull_request("acme/app", 3, "token123", provider="forgejo")


def test_unsupported_provider_rejected():
    import pytest

    with pytest.raises(ValueError):
        pr_review.analyze_pull_request("acme/app", 3, "token123", provider="gitlab")
