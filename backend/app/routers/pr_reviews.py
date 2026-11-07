"""Whitebox pull-request review: risk-ranked findings on the PR.

Fetches a pull request's diff (GitHub, Bitbucket, or Forgejo -- see
`app.pr_review`), flags risky patterns introduced by its added lines, ranks
them by severity, and -- only when the caller opts in -- posts a single
findings comment back on the PR. The access token is used once, in memory,
to make the call: it is never written to the database or the audit log.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import get_db
from app import models, schemas, auth, audit, pr_review

router = APIRouter()


def run_and_persist_review(
    db: Session,
    client: models.Client,
    current_user: models.User,
    repo: str,
    pr_number: int,
    github_token: str,
    post_comment: bool = False,
    provider: str = "github",
    host: str = None,
) -> models.PRReview:
    """Run a PR review and persist it. Shared by the `/pr-reviews` endpoint
    and `app.commander` (multi-task campaigns)."""
    review = models.PRReview(
        client_id=client.id,
        requested_by_id=current_user.id,
        repo=repo,
        pr_number=pr_number,
        provider=provider,
        status="running",
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    try:
        result = pr_review.analyze_pull_request(
            repo, pr_number, github_token, post_comment=post_comment, provider=provider, host=host
        )
    except Exception as exc:
        review.status = "failed"
        review.completed_at = func.now()
        db.commit()
        raise HTTPException(status_code=400, detail=f"Could not review that pull request: {exc}")

    for f in result["findings"]:
        db.add(
            models.PRReviewFinding(
                review_id=review.id,
                file_path=f["file_path"],
                line_number=f["line_number"],
                issue_type=f["issue_type"],
                severity=f["severity"],
                summary=f["summary"],
                suggested_fix=f["suggested_fix"],
                code_snippet=f["code_snippet"],
            )
        )

    review.status = "completed"
    review.pr_title = result["title"]
    review.pr_url = result["html_url"]
    review.files_changed = result["files_changed"]
    review.findings_count = len(result["findings"])
    review.comment_posted = result["comment_posted"]
    review.completed_at = func.now()
    db.commit()
    db.refresh(review)

    audit.log_action(
        db,
        "run_pr_review",
        user_id=current_user.id,
        client_id=client.id,
        resource_type="pr_review",
        resource_id=str(review.id),
        details={
            "repo": repo,
            "pr_number": pr_number,
            "findings_count": review.findings_count,
            "comment_posted": review.comment_posted,
        },
    )
    return review


@router.post("/pr-reviews", response_model=schemas.PRReviewOut)
def create_pr_review(
    review_in: schemas.PRReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_role(models.UserRole.admin, models.UserRole.analyst)
    ),
):
    client = db.query(models.Client).filter(models.Client.id == review_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if review_in.provider not in pr_review.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"provider must be one of {pr_review.SUPPORTED_PROVIDERS}",
        )
    if review_in.provider == "forgejo" and not review_in.host:
        raise HTTPException(status_code=400, detail="host is required for provider='forgejo'")

    return run_and_persist_review(
        db,
        client,
        current_user,
        review_in.repo,
        review_in.pr_number,
        review_in.github_token,
        post_comment=review_in.post_comment,
        provider=review_in.provider,
        host=review_in.host,
    )


@router.get("/pr-reviews", response_model=List[schemas.PRReviewOut])
def list_pr_reviews(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.PRReview)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.order_by(models.PRReview.id.desc()).all()


@router.get("/pr-reviews/{review_id}", response_model=schemas.PRReviewOut)
def get_pr_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    review = db.query(models.PRReview).filter(models.PRReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="PR review not found")
    if current_user.role == models.UserRole.client and review.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return review


@router.get("/pr-reviews/{review_id}/findings", response_model=List[schemas.PRReviewFindingOut])
def get_pr_review_findings(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    review = db.query(models.PRReview).filter(models.PRReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="PR review not found")
    if current_user.role == models.UserRole.client and review.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return review.findings
