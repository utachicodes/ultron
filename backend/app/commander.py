from __future__ import annotations

"""The commander: plans and dispatches a campaign across Ultron's own proof
engines, and consolidates the results into a shared, layered fact log.

Architecturally inspired by sapper-v2's commander/worker division of labor
(https://github.com/N1nEmAn/sapper-v2) and its three-layer fact history
(title/summary/evidence) -- reimplemented natively, with none of its code or
runtime model:

- No tmux, no shell-spawning, no third-party agent processes. A "task" here
  is just a call into `app.routers.authz.run_and_persist_hunt` or
  `app.routers.pr_reviews.run_and_persist_review` -- the same engines the
  single-task API endpoints use, with the same scope limits, redaction, and
  human-review gates.
- No autonomous exploitation beyond what those engines already do
  (authenticated request replay, PR diff analysis). The commander only
  decides *what order to run declared tasks in* and *how to summarize them*
  -- it never invents a target, a probe, or a repo on its own.
- `role` on each task is a descriptive label (scout/soldier/general) sized
  by how much work the task represents, not a separate spawned agent.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app import models
from app.ai_router import route_ai_query
from app.database import SessionLocal
from app.routers.authz import run_and_persist_hunt
from app.routers.pr_reviews import run_and_persist_review

MAX_PARALLEL_TASKS = 4


def _role_for_probe_count(n: int) -> str:
    if n <= 1:
        return "scout"
    if n <= 5:
        return "soldier"
    return "general"


def plan_campaign(
    authz_configs: List[Dict[str, Any]], pr_configs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Decompose a campaign's declared targets into a task list, each
    labeled with a role sized by its workload. Pure planning -- runs
    nothing."""
    tasks: List[Dict[str, Any]] = []

    for cfg in authz_configs:
        probe_count = len(cfg.get("probes", []))
        tasks.append(
            {
                "task_type": "authz_hunt",
                "role": _role_for_probe_count(probe_count),
                "target_summary": f"{cfg.get('base_url')} ({probe_count} probe(s))",
                "config": cfg,
            }
        )

    for cfg in pr_configs:
        tasks.append(
            {
                "task_type": "pr_review",
                "role": "scout",
                "target_summary": f"{cfg.get('repo')}#{cfg.get('pr_number')}",
                "config": cfg,
            }
        )

    return tasks


def _facts_from_authz_hunt(hunt: models.AuthzHunt) -> List[Dict[str, Any]]:
    facts = []
    for f in hunt.findings:
        if f.verdict != "confirmed_leak":
            continue
        facts.append(
            {
                "title": f"Broken object-level authorization: {f.method} {f.path}",
                "summary": f.reason or f.narrative or "Confirmed cross-role data leak.",
                "severity": f.severity,
                "evidence": {"type": "authz_finding", "id": f.id, "hunt_id": hunt.id},
            }
        )
    return facts


_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _facts_from_pr_review(review: models.PRReview) -> List[Dict[str, Any]]:
    facts = []
    if review.findings_count > 0:
        top = sorted(review.findings, key=lambda f: _SEVERITY_RANK.get(f.severity, 5))[:1]
        facts.append(
            {
                "title": f"{review.findings_count} risky pattern(s) in {review.repo}#{review.pr_number}",
                "summary": (top[0].summary if top else "Risky patterns found in added lines."),
                "severity": top[0].severity if top else "medium",
                "evidence": {"type": "pr_review", "id": review.id},
            }
        )
    return facts


def _campaign_narrative_prompt(goal: str, facts: List[Dict[str, Any]], tasks_total: int) -> str:
    fact_lines = "\n".join(f"- [{f['severity']}] {f['title']}" for f in facts) or "- No significant findings."
    return (
        f"A security campaign ran {tasks_total} task(s) toward this goal: \"{goal}\".\n"
        f"Consolidated findings:\n{fact_lines}\n\n"
        "In 3-4 sentences, summarize this campaign for a client report: what was tested, "
        "what matters most, and what to do next."
    )


def _execute_task(client_id: int, user_id: int, task_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Run one task's engine call to completion, on its own DB session.

    Runs in a worker thread (see `run_campaign`) so independent tasks (e.g.
    an authz hunt against one target and a PR review against an unrelated
    repo) execute concurrently instead of blocking on each other's network
    I/O. A plain `ThreadPoolExecutor` rather than a Celery group: this is a
    synchronous, request-scoped action (same convention `worker.execute_scan`
    already follows for "run now" calls) -- it doesn't need a broker or a
    separate worker process to get real parallelism, since the engines
    themselves are I/O-bound, not CPU-bound. Each thread gets its own
    SQLAlchemy session; sessions are not thread-safe to share.
    """
    session = SessionLocal()
    try:
        client = session.get(models.Client, client_id)
        user = session.get(models.User, user_id)

        if task_plan["task_type"] == "authz_hunt":
            cfg = task_plan["config"]
            hunt = run_and_persist_hunt(
                session, client, user, cfg["base_url"], cfg["roles"], cfg["probes"]
            )
            return {
                "task_type": "authz_hunt",
                "status": "completed",
                "result_ref_id": hunt.id,
                "result_summary": f"{hunt.confirmed_leaks} confirmed leak(s) across {hunt.probes_run} probe(s)",
                "facts": _facts_from_authz_hunt(hunt),
            }

        cfg = task_plan["config"]
        review = run_and_persist_review(
            session,
            client,
            user,
            cfg["repo"],
            cfg["pr_number"],
            cfg["github_token"],
            post_comment=cfg.get("post_comment", False),
        )
        return {
            "task_type": "pr_review",
            "status": "completed",
            "result_ref_id": review.id,
            "result_summary": f"{review.findings_count} risky pattern(s) in {review.files_changed} file(s)",
            "facts": _facts_from_pr_review(review),
        }
    except Exception as exc:
        return {
            "task_type": task_plan["task_type"],
            "status": "failed",
            "result_ref_id": None,
            "result_summary": str(exc),
            "facts": [],
        }
    finally:
        session.close()


def run_campaign(
    db: Session,
    campaign: models.Campaign,
    client: models.Client,
    current_user: models.User,
    authz_configs: Optional[List[Dict[str, Any]]] = None,
    pr_configs: Optional[List[Dict[str, Any]]] = None,
) -> models.Campaign:
    """Plan, dispatch, and consolidate a campaign. Independent tasks run in
    parallel (see `_execute_task`); this function's own DB session is only
    ever touched from this thread, after each task's result comes back."""
    tasks = plan_campaign(authz_configs or [], pr_configs or [])
    campaign.tasks_total = len(tasks)
    db.commit()

    pending_rows: Dict[Any, models.CampaignTask] = {}
    for task_plan in tasks:
        task = models.CampaignTask(
            campaign_id=campaign.id,
            task_type=task_plan["task_type"],
            role=task_plan["role"],
            status="running",
            target_summary=task_plan["target_summary"],
        )
        db.add(task)
        pending_rows[id(task_plan)] = task
    db.commit()

    all_facts: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_TASKS, len(tasks) or 1)) as executor:
        future_to_plan = {
            executor.submit(_execute_task, client.id, current_user.id, tp): tp for tp in tasks
        }
        for future in as_completed(future_to_plan):
            task_plan = future_to_plan[future]
            task = pending_rows[id(task_plan)]
            result = future.result()

            task.status = result["status"]
            task.result_ref_id = result["result_ref_id"]
            task.result_summary = result["result_summary"]
            task.completed_at = func.now()
            campaign.tasks_completed += 1
            all_facts.extend(result["facts"])
            db.commit()

    for f in all_facts:
        db.add(
            models.CampaignFact(
                campaign_id=campaign.id,
                title=f["title"],
                summary=f["summary"],
                severity=f["severity"],
                evidence=json.dumps(f["evidence"]),
            )
        )
    db.commit()

    try:
        ai_result = route_ai_query(
            prompt=_campaign_narrative_prompt(campaign.goal, all_facts, len(tasks)),
            client_name=client.name,
            user=current_user,
            client=client,
            db=db,
        )
        campaign.summary = ai_result["response"]
    except Exception:
        campaign.summary = None

    campaign.status = "completed"
    campaign.completed_at = func.now()
    db.commit()
    db.refresh(campaign)
    return campaign
