"""AI Guard red-team: attack known prompt-injection/jailbreak patterns
against a declared target, then close the loop by turning confirmed
bypasses into defense patterns `ai_router` checks on every future query.

`mode="internal"` targets Ultron's own AI Guard pipeline (`ai_router.route_ai_query`);
`mode="external"` targets a client's own AI-powered feature they've
authorized testing on, reached over plain HTTP. Either way this only ever
sends declared, canary-based test prompts -- it does not discover a target,
and a bypass here triggers a defense update, not a client-facing report.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import get_db
from app import models, schemas, auth, audit, ai_redteam, jailbreak_guard, scope_guard
from app.ai_router import route_ai_query

router = APIRouter()


@router.post("/ai-redteam/runs", response_model=schemas.AIRedTeamRunOut)
def create_redteam_run(
    run_in: schemas.AIRedTeamRunCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    client = db.query(models.Client).filter(models.Client.id == run_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if run_in.mode not in ("internal", "external"):
        raise HTTPException(status_code=400, detail="mode must be 'internal' or 'external'")
    if run_in.mode == "external" and not run_in.external:
        raise HTTPException(status_code=400, detail="external config is required for mode='external'")
    if run_in.mode == "external":
        try:
            scope_guard.enforce_scope(run_in.external.url, client, db)
        except scope_guard.ScopeViolation as exc:
            raise HTTPException(status_code=403, detail=str(exc))

    target_summary = "Ultron AI Guard" if run_in.mode == "internal" else run_in.external.url

    run = models.AIRedTeamRun(
        client_id=client.id,
        requested_by_id=current_user.id,
        mode=run_in.mode,
        target_summary=target_summary,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if run_in.mode == "internal":
        results = ai_redteam.run_internal_redteam(
            route_ai_query,
            client_name=client.name,
            user=current_user,
            client=client,
            db=db,
            force_local=run_in.force_local,
        )
    else:
        results = ai_redteam.run_external_redteam(
            run_in.external.url,
            run_in.external.headers,
            prompt_field=run_in.external.prompt_field,
            response_field=run_in.external.response_field,
        )

    bypassed = 0
    patterns_learned = 0
    for r in results:
        pattern_learned = False
        if r["verdict"] == "bypassed":
            bypassed += 1
            jailbreak_guard.add_pattern_from_bypass(db, r["category"], source_run_id=run.id)
            patterns_learned += 1
            pattern_learned = True

        db.add(
            models.AIRedTeamResult(
                run_id=run.id,
                payload_id=r["payload_id"],
                category=r["category"],
                verdict=r["verdict"],
                prompt_preview=r["prompt"][:500],
                response_preview=r["response_preview"],
                pattern_learned=pattern_learned,
            )
        )

    run.status = "completed"
    run.payloads_run = len(results)
    run.bypassed_count = bypassed
    run.patterns_learned = patterns_learned
    run.completed_at = func.now()
    db.commit()
    db.refresh(run)

    audit.log_action(
        db,
        "run_ai_redteam",
        user_id=current_user.id,
        client_id=client.id,
        resource_type="ai_redteam_run",
        resource_id=str(run.id),
        details={
            "mode": run_in.mode,
            "payloads_run": run.payloads_run,
            "bypassed_count": bypassed,
            "patterns_learned": patterns_learned,
        },
    )
    return run


@router.get("/ai-redteam/runs", response_model=List[schemas.AIRedTeamRunOut])
def list_redteam_runs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.AIRedTeamRun)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.AIRedTeamRun.id.desc()).all()


@router.get("/ai-redteam/runs/{run_id}", response_model=schemas.AIRedTeamRunOut)
def get_redteam_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    run = db.query(models.AIRedTeamRun).filter(models.AIRedTeamRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Red-team run not found")
    if current_user.role == models.UserRole.client and run.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return run


@router.get("/ai-redteam/runs/{run_id}/results", response_model=List[schemas.AIRedTeamResultOut])
def get_redteam_results(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    run = db.query(models.AIRedTeamRun).filter(models.AIRedTeamRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Red-team run not found")
    if current_user.role == models.UserRole.client and run.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return run.results


@router.get("/jailbreak-patterns", response_model=List[schemas.JailbreakPatternOut])
def list_jailbreak_patterns(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    return jailbreak_guard.list_active_patterns(db)
