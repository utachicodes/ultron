"""Findings and human analyst review."""

import os
import secrets

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from typing import List
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas, auth, audit

router = APIRouter()


def _check_finding_read_access(current_user: models.User, finding: models.Finding) -> None:
    """Same ownership scoping as `get_findings`: clients may only read
    findings on scans that belong to their own client."""
    if current_user.role == models.UserRole.client and finding.scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")


def _get_finding_or_404(db: Session, finding_id: int) -> models.Finding:
    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


def _get_attachment_or_404(db: Session, finding_id: int, attachment_id: int) -> models.FindingAttachment:
    # Scope the lookup by both ids so an attachment id can't be probed
    # against a finding it doesn't belong to.
    attachment = (
        db.query(models.FindingAttachment)
        .filter(
            models.FindingAttachment.id == attachment_id,
            models.FindingAttachment.finding_id == finding_id,
        )
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment

# ============================================================
# Findings
# ============================================================
@router.get("/scans/{scan_id}/findings", response_model=List[schemas.FindingOut])
def get_findings(
    scan_id: int,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return (
        db.query(models.Finding)
        .filter(models.Finding.scan_id == scan_id)
        .order_by(models.Finding.id)
        .offset(offset)
        .limit(min(limit, 1000))
        .all()
    )


@router.post("/findings/{finding_id}/review")
def review_finding(
    finding_id: int,
    review: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.status = review.get("status", finding.status)
    finding.reviewed_by_id = current_user.id
    from sqlalchemy.sql import func
    finding.reviewed_at = func.now()
    db.commit()
    audit.log_action(
        db, "review_finding", user_id=current_user.id, client_id=finding.scan.client_id,
        resource_type="finding", resource_id=str(finding_id),
        details={"status": finding.status},
    )
    return {"status": finding.status, "reviewed_by": current_user.email}


# ============================================================
# Evidence attachments (screenshots, raw scanner output, etc.)
# ============================================================
# Access rule: admin/analyst can always upload evidence to any finding.
# A client-role user may also attach their own supporting evidence, but only
# to findings that live on scans belonging to their own client - the same
# ownership scoping `get_findings` already uses for reads. There is no role
# restriction here beyond that ownership check, matching how clients are
# treated elsewhere for findings (read-only but scoped to their own data).
@router.post("/findings/{finding_id}/attachments", response_model=schemas.FindingAttachmentOut)
def upload_finding_attachment(
    finding_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    finding = _get_finding_or_404(db, finding_id)
    _check_finding_read_access(current_user, finding)

    max_bytes = settings.attachment_max_size_mb * 1024 * 1024
    os.makedirs(settings.attachment_storage_dir, exist_ok=True)

    # Never trust the client-supplied filename for the on-disk path: generate
    # a random, non-guessable name and keep only a safe extension from the
    # original filename for convenience.
    original_name = file.filename or "upload"
    _, ext = os.path.splitext(original_name)
    ext = ext if len(ext) <= 10 else ""  # guard against absurd/garbage extensions
    safe_name = f"{secrets.token_hex(16)}{ext}"
    storage_path = os.path.join(settings.attachment_storage_dir, safe_name)

    size_bytes = 0
    chunk_size = 1024 * 1024
    try:
        with open(storage_path, "wb") as out_file:
            while True:
                chunk = file.file.read(chunk_size)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    out_file.close()
                    try:
                        os.remove(storage_path)
                    except OSError:
                        pass
                    raise HTTPException(
                        status_code=400,
                        detail=f"File exceeds maximum size of {settings.attachment_max_size_mb}MB",
                    )
                out_file.write(chunk)
    finally:
        file.file.close()

    attachment = models.FindingAttachment(
        finding_id=finding.id,
        filename=original_name,
        content_type=file.content_type,
        size_bytes=size_bytes,
        storage_path=storage_path,
        uploaded_by_id=current_user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    audit.log_action(
        db, "upload_finding_attachment", user_id=current_user.id, client_id=finding.scan.client_id,
        resource_type="finding_attachment", resource_id=str(attachment.id),
        details={"finding_id": finding_id, "filename": original_name, "size_bytes": size_bytes},
    )
    return attachment


@router.get("/findings/{finding_id}/attachments", response_model=List[schemas.FindingAttachmentOut])
def list_finding_attachments(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    finding = _get_finding_or_404(db, finding_id)
    _check_finding_read_access(current_user, finding)
    return (
        db.query(models.FindingAttachment)
        .filter(models.FindingAttachment.finding_id == finding_id)
        .order_by(models.FindingAttachment.id)
        .all()
    )


@router.get("/findings/{finding_id}/attachments/{attachment_id}")
def download_finding_attachment(
    finding_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    finding = _get_finding_or_404(db, finding_id)
    _check_finding_read_access(current_user, finding)
    attachment = _get_attachment_or_404(db, finding_id, attachment_id)

    if not os.path.isfile(attachment.storage_path):
        raise HTTPException(status_code=404, detail="Attachment file not found on disk")

    return FileResponse(
        path=attachment.storage_path,
        media_type=attachment.content_type or "application/octet-stream",
        filename=attachment.filename,
    )


@router.delete("/findings/{finding_id}/attachments/{attachment_id}")
def delete_finding_attachment(
    finding_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    finding = _get_finding_or_404(db, finding_id)
    attachment = _get_attachment_or_404(db, finding_id, attachment_id)

    try:
        os.remove(attachment.storage_path)
    except OSError:
        pass  # best-effort: file may already be gone

    db.delete(attachment)
    db.commit()

    audit.log_action(
        db, "delete_finding_attachment", user_id=current_user.id, client_id=finding.scan.client_id,
        resource_type="finding_attachment", resource_id=str(attachment_id),
        details={"finding_id": finding_id, "filename": attachment.filename},
    )
    return {"status": "deleted", "id": attachment_id}
