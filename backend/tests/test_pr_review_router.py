from __future__ import annotations

"""End-to-end test of /pr-reviews: mocks PyGithub so no network call or real
token is involved, and checks the token itself never gets persisted."""

import httpx
import pytest

from app import pr_review


class _FakeFile:
    def __init__(self, filename, patch):
        self.filename = filename
        self.patch = patch
        self.status = "modified"


class _FakePR:
    def __init__(self, title, number, files):
        self.title = title
        self.number = number
        self.html_url = f"https://github.com/acme/app/pull/{number}"
        self._files = files
        self.comments_posted = []

    def get_files(self):
        return self._files

    def create_issue_comment(self, body):
        self.comments_posted.append(body)


class _FakeRepo:
    def __init__(self, pr):
        self._pr = pr

    def get_pull(self, number):
        return self._pr


class _FakeGithub:
    last_token = None

    def __init__(self, token):
        _FakeGithub.last_token = token

    def get_repo(self, full_name):
        return _FakeRepo(FAKE_PR)


FAKE_PR = _FakePR(
    "Add payment webhook",
    42,
    [
        _FakeFile(
            "app/webhook.py",
            "@@ -1,1 +1,2 @@\n import os\n+API_KEY = \"sk-1234567890abcd\"\n",
        )
    ],
)


@pytest.fixture(autouse=True)
def fake_github(monkeypatch):
    monkeypatch.setattr(pr_review, "Github", _FakeGithub)


def test_pr_review_flags_finding_and_never_persists_token(client, sample_client, db):
    res = client.post(
        "/pr-reviews",
        json={
            "client_id": sample_client["id"],
            "repo": "acme/app",
            "pr_number": 42,
            "github_token": "ghp_supersecrettoken",
            "post_comment": False,
        },
    )
    assert res.status_code == 200, res.text
    review = res.json()
    assert review["status"] == "completed"
    assert review["pr_title"] == "Add payment webhook"
    assert review["findings_count"] == 1
    assert review["comment_posted"] is False

    findings = client.get(f"/pr-reviews/{review['id']}/findings").json()
    assert len(findings) == 1
    assert findings[0]["issue_type"] == "hardcoded_secret"
    assert findings[0]["severity"] == "high"

    # The token must never land in the database in any form.
    from app import models

    for row in db.query(models.PRReview).all():
        dump = str(row.__dict__)
        assert "ghp_supersecrettoken" not in dump
    for row in db.query(models.AuditLog).all():
        assert "ghp_supersecrettoken" not in (row.details or "")


def test_pr_review_posts_comment_when_requested(client, sample_client):
    FAKE_PR.comments_posted.clear()
    res = client.post(
        "/pr-reviews",
        json={
            "client_id": sample_client["id"],
            "repo": "acme/app",
            "pr_number": 42,
            "github_token": "ghp_anothertoken",
            "post_comment": True,
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["comment_posted"] is True
    assert len(FAKE_PR.comments_posted) == 1
    assert "hardcoded secret" in FAKE_PR.comments_posted[0]


def test_pr_review_requires_valid_client(client):
    res = client.post(
        "/pr-reviews",
        json={"client_id": 999999, "repo": "acme/app", "pr_number": 1, "github_token": "t"},
    )
    assert res.status_code == 404


def test_client_role_cannot_see_other_clients_pr_reviews(client, sample_client, db):
    client.post(
        "/pr-reviews",
        json={
            "client_id": sample_client["id"],
            "repo": "acme/app",
            "pr_number": 42,
            "github_token": "ghp_x",
        },
    )

    from app import models, auth
    from fastapi.testclient import TestClient
    from app.main import app

    other_user = models.User(
        email="other-client-2@test.local",
        hashed_password=auth.get_password_hash("password123"),
        role=models.UserRole.client,
    )
    db.add(other_user)
    db.commit()
    token = auth.create_access_token(data={"sub": other_user.email})

    other_http = TestClient(app)
    other_http.headers.update({"Authorization": f"Bearer {token}"})
    res = other_http.get("/pr-reviews")
    assert res.status_code == 200
    assert res.json() == []


def test_pr_review_bitbucket_provider_end_to_end(client, sample_client, monkeypatch):
    diff = "diff --git a/f.py b/f.py\nindex 1..2 100644\n--- a/f.py\n+++ b/f.py\n@@ -1,1 +1,2 @@\n import os\n+API_KEY = \"sk-1234567890abcd\"\n"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/diff"):
            return httpx.Response(200, text=diff)
        return httpx.Response(200, json={"title": "Fix", "links": {"html": {"href": "https://bitbucket.org/acme/app/pull-requests/1"}}})

    real_client_cls = httpx.Client

    def _factory(*args, **kwargs):
        return real_client_cls(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(pr_review.httpx, "Client", _factory)

    res = client.post(
        "/pr-reviews",
        json={
            "client_id": sample_client["id"],
            "repo": "acme/app",
            "pr_number": 1,
            "github_token": "bb_token",
            "provider": "bitbucket",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["provider"] == "bitbucket"
    assert body["findings_count"] == 1


def test_pr_review_forgejo_requires_host(client, sample_client):
    res = client.post(
        "/pr-reviews",
        json={
            "client_id": sample_client["id"],
            "repo": "acme/app",
            "pr_number": 1,
            "github_token": "t",
            "provider": "forgejo",
        },
    )
    assert res.status_code == 400


def test_pr_review_rejects_unknown_provider(client, sample_client):
    res = client.post(
        "/pr-reviews",
        json={
            "client_id": sample_client["id"],
            "repo": "acme/app",
            "pr_number": 1,
            "github_token": "t",
            "provider": "gitlab",
        },
    )
    assert res.status_code == 400
