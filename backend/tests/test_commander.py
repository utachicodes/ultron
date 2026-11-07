from __future__ import annotations

"""Tests for the commander (app/commander.py) and /campaigns: planning,
dispatch into the existing authz_hunter/pr_review engines, and the
consolidated fact log -- no tmux, no shell execution, no third-party agents
involved anywhere in this path."""

import httpx
import pytest

from app import authz_hunter, commander, pr_review


def test_plan_campaign_labels_roles_by_workload():
    authz_configs = [
        {"base_url": "https://a.test", "probes": [{}]},  # 1 probe -> scout
        {"base_url": "https://b.test", "probes": [{}, {}, {}]},  # 3 -> soldier
        {"base_url": "https://c.test", "probes": [{}] * 7},  # 7 -> general
    ]
    pr_configs = [{"repo": "acme/app", "pr_number": 1}]

    tasks = commander.plan_campaign(authz_configs, pr_configs)

    assert len(tasks) == 4
    assert tasks[0]["role"] == "scout"
    assert tasks[1]["role"] == "soldier"
    assert tasks[2]["role"] == "general"
    assert tasks[3]["task_type"] == "pr_review"
    assert tasks[3]["role"] == "scout"


# ---------- fake backends for the end-to-end /campaigns test ----------

def _fake_authz_handler(request: httpx.Request) -> httpx.Response:
    role = request.headers.get("x-role", "")
    if request.url.path == "/profile/42":
        if role:
            return httpx.Response(200, json={"id": "42", "owner": "customer-a"})
        return httpx.Response(401)
    return httpx.Response(404)


class _FakeFile:
    def __init__(self, filename, patch):
        self.filename = filename
        self.patch = patch
        self.status = "modified"


class _FakePR:
    def __init__(self):
        self.title = "Add webhook"
        self.number = 7
        self.html_url = "https://github.com/acme/app/pull/7"
        self._files = [
            _FakeFile("app/webhook.py", "@@ -1,1 +1,2 @@\n import os\n+API_KEY = \"sk-1234567890abcd\"\n")
        ]

    def get_files(self):
        return self._files

    def create_issue_comment(self, body):
        pass


class _FakeGithub:
    def __init__(self, token):
        pass

    def get_repo(self, full_name):
        class _Repo:
            def get_pull(self, number):
                return _FakePR()

        return _Repo()


@pytest.fixture(autouse=True)
def fake_backends(monkeypatch):
    real_client_cls = httpx.Client

    def _http_factory(*args, **kwargs):
        return real_client_cls(transport=httpx.MockTransport(_fake_authz_handler))

    monkeypatch.setattr(authz_hunter.httpx, "Client", _http_factory)
    monkeypatch.setattr(pr_review, "Github", _FakeGithub)


def test_campaign_runs_authz_and_pr_tasks_and_builds_fact_log(client, sample_client):
    res = client.post(
        "/campaigns",
        json={
            "client_id": sample_client["id"],
            "goal": "Assess the new customer portal before launch",
            "authz_hunts": [
                {
                    "base_url": "https://api.testbank.sn",
                    "roles": [
                        {"name": "customer-a", "headers": {"X-Role": "customer-a"}},
                        {"name": "customer-b", "headers": {"X-Role": "customer-b"}},
                    ],
                    "probes": [
                        {
                            "method": "GET",
                            "path": "/profile/{id}",
                            "id_param": "id",
                            "owner_role": "customer-a",
                            "owner_value": "42",
                        }
                    ],
                }
            ],
            "pr_reviews": [
                {"repo": "acme/app", "pr_number": 7, "github_token": "ghp_x", "post_comment": False}
            ],
        },
    )
    assert res.status_code == 200, res.text
    campaign = res.json()
    assert campaign["status"] == "completed"
    assert campaign["tasks_total"] == 2
    assert campaign["tasks_completed"] == 2
    assert len(campaign["tasks"]) == 2

    task_types = {t["task_type"] for t in campaign["tasks"]}
    assert task_types == {"authz_hunt", "pr_review"}
    assert all(t["status"] == "completed" for t in campaign["tasks"])

    facts = client.get(f"/campaigns/{campaign['id']}/facts").json()
    titles = " ".join(f["title"] for f in facts)
    assert "Broken object-level authorization" in titles
    assert "risky pattern" in titles

    # The underlying single-task resources were actually created, not just
    # referenced -- a campaign dispatches real work, it doesn't fake it.
    authz_hunt_task = next(t for t in campaign["tasks"] if t["task_type"] == "authz_hunt")
    hunt = client.get(f"/authz-hunts/{authz_hunt_task['result_ref_id']}").json()
    assert hunt["confirmed_leaks"] == 1

    pr_task = next(t for t in campaign["tasks"] if t["task_type"] == "pr_review")
    review = client.get(f"/pr-reviews/{pr_task['result_ref_id']}").json()
    assert review["findings_count"] == 1


def test_campaign_tasks_run_in_parallel_not_sequentially(client, sample_client, monkeypatch):
    """Two independent authz-hunt tasks, each artificially slow, should
    finish in roughly one task's duration -- not the sum of both -- proving
    `_execute_task` dispatch via ThreadPoolExecutor actually overlaps."""
    import time

    DELAY = 0.3

    def slow_handler(request: httpx.Request) -> httpx.Response:
        time.sleep(DELAY)
        return httpx.Response(200, json={"id": "42", "owner": "customer-a"}) if request.headers.get("x-role") else httpx.Response(401)

    real_client_cls = httpx.Client

    def _factory(*args, **kwargs):
        return real_client_cls(transport=httpx.MockTransport(slow_handler))

    monkeypatch.setattr(authz_hunter.httpx, "Client", _factory)

    probe = {
        "method": "GET",
        "path": "/profile/{id}",
        "id_param": "id",
        "owner_role": "customer-a",
        "owner_value": "42",
    }
    roles = [
        {"name": "customer-a", "headers": {"X-Role": "customer-a"}},
        {"name": "customer-b", "headers": {"X-Role": "customer-b"}},
    ]
    hunt_config = {"base_url": "https://api.test", "roles": roles, "probes": [probe]}

    started = time.monotonic()
    res = client.post(
        "/campaigns",
        json={
            "client_id": sample_client["id"],
            "goal": "Parallel smoke test",
            "authz_hunts": [hunt_config, hunt_config],
        },
    )
    elapsed = time.monotonic() - started

    assert res.status_code == 200, res.text
    assert res.json()["tasks_completed"] == 2
    # Sequential would take >= 2 * DELAY (two tasks * one request each,
    # since the hunt's single cross-role probe issues 2 HTTP calls -> ~0.6s
    # per task, ~1.2s total sequential). Parallel should land near one
    # task's own duration. Generous margin for CI jitter.
    assert elapsed < DELAY * 2 * 1.5


def test_campaign_requires_at_least_one_task(client, sample_client):
    res = client.post(
        "/campaigns",
        json={"client_id": sample_client["id"], "goal": "Nothing to do"},
    )
    assert res.status_code == 400
