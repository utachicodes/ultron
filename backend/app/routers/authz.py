"""Autonomous authorization (IDOR/BOLA) hunting -- blackbox proof-of-exploit.

Replays authenticated requests across operator-declared roles against a
client's declared base_url to prove, or rule out, broken object-level
authorization: the "change /invoices/1024 to /invoices/1025" exploit, run
and evidenced automatically instead of by hand.

A `confirmed_leak` verdict is a strong automated signal, not a verified
client-facing report: it still requires a named human analyst to review it
(`POST /authz-findings/{id}/review`), the same gate `Finding` already
enforces for critical/high results.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import get_db
from app import models, schemas, auth, audit, authz_hunter, browser_crawl, scope_guard
from app.ai_router import route_ai_query

router = APIRouter()


def _narrative_prompt(result: dict) -> str:
    return (
        "A security scan replayed an API request as role "
        f"'{result['tested_role']}' using an object id that belongs to role "
        f"'{result['owner_role']}' on {result['method']} {result['path']}. "
        f"The other role received HTTP "
        f"{result['evidence']['attempt_response']['status_code']} with a "
        f"response body {round(result['confidence'] * 100)}% similar to the "
        "owner's own response. In 2-3 sentences, explain this as a broken "
        "object-level authorization (IDOR/BOLA) finding for a client "
        "report, and suggest a concrete fix."
    )


@router.post("/authz-hunts/suggest-probes")
def suggest_authz_probes(
    request: dict,
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    """Discovery helper: given an OpenAPI/Swagger spec (inline `spec` or a
    `spec_url` to fetch), suggest GET endpoints with an id-shaped path
    parameter as probe skeletons. Read-only -- issues no requests against the
    target itself when a spec is embedded, and only fetches the spec
    document when given a URL. The operator still fills in `owner_role` and
    `owner_value` with real data before running a hunt.
    """
    spec = request.get("spec")
    spec_url = request.get("spec_url")

    if not spec and not spec_url:
        raise HTTPException(status_code=400, detail="spec_url or spec is required")

    if not spec:
        try:
            spec = authz_hunter.fetch_openapi_spec(spec_url)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not fetch spec: {exc}")

    suggestions = authz_hunter.suggest_probes_from_spec(spec)
    return {"suggestions": suggestions}


@router.post("/authz-hunts/crawl-and-suggest")
def crawl_and_suggest_authz_config(
    crawl_in: schemas.BrowserCrawlRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    """Discovery helper for apps with no OpenAPI spec: logs in as each
    declared role through its real login form (Playwright/Chromium),
    crawls same-origin pages, and returns a ready-to-review
    `{base_url, roles, probes}` config -- owner_role/owner_value already
    filled in from what each role's crawl actually found. Does not run a
    hunt; the operator reviews (and can edit) the result before submitting
    it to `POST /authz-hunts`, the same human-in-the-loop step
    `suggest-probes` already requires.
    """
    if len(crawl_in.roles) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 roles are required to test cross-role access"
        )

    role_configs = [r.model_dump() for r in crawl_in.roles]
    try:
        config = browser_crawl.crawl_roles_and_build_authz_config(
            crawl_in.base_url, role_configs, max_pages=crawl_in.max_pages
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return config


def run_and_persist_hunt(
    db: Session,
    client: models.Client,
    current_user: models.User,
    base_url: str,
    roles: list,
    probes: list,
) -> models.AuthzHunt:
    """Run an authorization hunt and persist it. Shared by the `/authz-hunts`
    endpoint and `app.commander` (multi-task campaigns), so both paths get
    identical persistence, AI narratives, audit logging, and scope
    enforcement -- raises `scope_guard.ScopeViolation` (uncaught here) if
    `base_url` is explicitly excluded from this client's declared scope."""
    scope_guard.enforce_scope(base_url, client, db)

    hunt = models.AuthzHunt(
        client_id=client.id,
        requested_by_id=current_user.id,
        base_url=base_url,
        status="running",
    )
    db.add(hunt)
    db.commit()
    db.refresh(hunt)

    results = authz_hunter.run_authz_hunt(base_url, roles, probes)

    confirmed = 0
    for r in results:
        narrative = None
        if r["verdict"] == "confirmed_leak":
            confirmed += 1
            try:
                ai_result = route_ai_query(
                    prompt=_narrative_prompt(r),
                    client_name=client.name,
                    user=current_user,
                    client=client,
                    db=db,
                )
                narrative = ai_result["response"]
            except Exception:
                narrative = None

        db.add(
            models.AuthzFinding(
                hunt_id=hunt.id,
                method=r["method"],
                path=r["path"],
                owner_role=r["owner_role"],
                tested_role=r["tested_role"],
                verdict=r["verdict"],
                confidence=r["confidence"],
                severity=r["severity"],
                reason=r["reason"],
                narrative=narrative,
                evidence=json.dumps(r["evidence"]) if r.get("evidence") else None,
            )
        )

    hunt.status = "completed"
    hunt.probes_run = len(results)
    hunt.confirmed_leaks = confirmed
    hunt.completed_at = func.now()
    db.commit()
    db.refresh(hunt)

    audit.log_action(
        db,
        "run_authz_hunt",
        user_id=current_user.id,
        client_id=client.id,
        resource_type="authz_hunt",
        resource_id=str(hunt.id),
        details={
            "base_url": base_url,
            "probes_run": hunt.probes_run,
            "confirmed_leaks": confirmed,
        },
    )
    return hunt


@router.post("/authz-hunts", response_model=schemas.AuthzHuntOut)
def create_authz_hunt(
    hunt_in: schemas.AuthzHuntCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    client = db.query(models.Client).filter(models.Client.id == hunt_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if len(hunt_in.roles) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 roles are required to test cross-role access"
        )
    if not hunt_in.probes:
        raise HTTPException(status_code=400, detail="At least 1 probe is required")

    roles = [r.model_dump() for r in hunt_in.roles]
    probes = [p.model_dump() for p in hunt_in.probes]
    try:
        return run_and_persist_hunt(db, client, current_user, hunt_in.base_url, roles, probes)
    except scope_guard.ScopeViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/authz-hunts", response_model=List[schemas.AuthzHuntOut])
def list_authz_hunts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.AuthzHunt)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.AuthzHunt.id.desc()).all()


@router.get("/authz-hunts/{hunt_id}", response_model=schemas.AuthzHuntOut)
def get_authz_hunt(
    hunt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    hunt = db.query(models.AuthzHunt).filter(models.AuthzHunt.id == hunt_id).first()
    if not hunt:
        raise HTTPException(status_code=404, detail="Authz hunt not found")
    if current_user.role == models.UserRole.client and hunt.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return hunt


@router.get("/authz-hunts/{hunt_id}/findings", response_model=List[schemas.AuthzFindingOut])
def get_authz_hunt_findings(
    hunt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    hunt = db.query(models.AuthzHunt).filter(models.AuthzHunt.id == hunt_id).first()
    if not hunt:
        raise HTTPException(status_code=404, detail="Authz hunt not found")
    if current_user.role == models.UserRole.client and hunt.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return hunt.findings


@router.post("/authz-findings/{finding_id}/review")
def review_authz_finding(
    finding_id: int,
    review: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    finding = db.query(models.AuthzFinding).filter(models.AuthzFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Authz finding not found")

    finding.reviewed_by_id = current_user.id
    finding.reviewed_at = func.now()
    db.commit()

    audit.log_action(
        db,
        "review_authz_finding",
        user_id=current_user.id,
        client_id=finding.hunt.client_id,
        resource_type="authz_finding",
        resource_id=str(finding_id),
        details={"verdict": finding.verdict},
    )
    return {"id": finding.id, "reviewed_by": current_user.email}
