"""Campaigns: commander-orchestrated runs across Ultron's own proof engines.

A campaign decomposes a goal into tasks (authorization hunts, PR reviews),
dispatches them through the same engines and persistence paths their
single-task endpoints use, and consolidates the results into a layered fact
log. See `app/commander.py` for what this does and does not do -- in
particular, it never runs anything beyond what `/authz-hunts` and
`/pr-reviews` already can, and the same human-review gates still apply to
whatever it finds.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, audit, commander

router = APIRouter()


@router.post("/campaigns", response_model=schemas.CampaignOut)
def create_campaign(
    campaign_in: schemas.CampaignCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    client = db.query(models.Client).filter(models.Client.id == campaign_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if not campaign_in.authz_hunts and not campaign_in.pr_reviews:
        raise HTTPException(
            status_code=400, detail="A campaign needs at least one authz_hunt or pr_review task"
        )

    campaign = models.Campaign(
        client_id=client.id,
        requested_by_id=current_user.id,
        goal=campaign_in.goal,
        status="running",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    authz_configs = [c.model_dump() for c in campaign_in.authz_hunts]
    pr_configs = [c.model_dump() for c in campaign_in.pr_reviews]
    commander.run_campaign(db, campaign, client, current_user, authz_configs, pr_configs)

    audit.log_action(
        db,
        "run_campaign",
        user_id=current_user.id,
        client_id=client.id,
        resource_type="campaign",
        resource_id=str(campaign.id),
        details={
            "goal": campaign_in.goal,
            "tasks_total": campaign.tasks_total,
            "tasks_completed": campaign.tasks_completed,
        },
    )
    return campaign


@router.get("/campaigns", response_model=List[schemas.CampaignOut])
def list_campaigns(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Campaign)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.Campaign.id.desc()).all()


@router.get("/campaigns/{campaign_id}", response_model=schemas.CampaignOut)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if current_user.role == models.UserRole.client and campaign.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return campaign


@router.get("/campaigns/{campaign_id}/facts", response_model=List[schemas.CampaignFactOut])
def get_campaign_facts(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if current_user.role == models.UserRole.client and campaign.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return campaign.facts
