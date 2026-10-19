"""AI code scanning."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, code_scanner

router = APIRouter()

# ============================================================
# Code Scans
# ============================================================
@router.post("/code-scans", response_model=schemas.CodeScanOut)
def create_code_scan(
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client_id = request.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")

    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    code_scan = models.CodeScan(
        client_id=client_id,
        repository_url=request.get("repository_url"),
        branch=request.get("branch", "main"),
        status="pending",
    )
    db.add(code_scan)
    db.commit()
    db.refresh(code_scan)

    # Run synchronously for MVP
    results = code_scanner.run_code_scan(request.get("repository_url", ""), "code")

    issues_found = 0
    for r in results:
        if "error" in r:
            continue
        issue = models.CodeScanIssue(
            code_scan_id=code_scan.id,
            file_path=r.get("file_path"),
            line_number=r.get("line_number"),
            issue_type=r.get("issue_type"),
            severity=r.get("severity"),
            description=r.get("description"),
            remediation=r.get("remediation"),
        )
        db.add(issue)
        issues_found += 1

    code_scan.status = "completed"
    code_scan.total_files = len(set(r.get("file_path", "") for r in results if "error" not in r))
    code_scan.issues_found = issues_found
    db.commit()
    db.refresh(code_scan)

    return code_scan


@router.get("/code-scans", response_model=List[schemas.CodeScanOut])
def list_code_scans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.CodeScan)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.all()


@router.get("/code-scans/{code_scan_id}/issues", response_model=List[schemas.CodeScanIssueOut])
def get_code_scan_issues(
    code_scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    code_scan = db.query(models.CodeScan).filter(models.CodeScan.id == code_scan_id).first()
    if not code_scan:
        raise HTTPException(status_code=404, detail="Code scan not found")
    if current_user.role == models.UserRole.client and code_scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.CodeScanIssue).filter(models.CodeScanIssue.code_scan_id == code_scan_id).all()
