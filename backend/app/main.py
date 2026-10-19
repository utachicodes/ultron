from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import json

from app.config import settings
from app.database import Base, engine, SessionLocal, get_db
from app import models, schemas, auth, scanner, ai_router, audit
from app.sanitizer import sanitize_text

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup seed: default admin user
# ============================================================
@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        admin = db.query(models.User).filter(models.User.email == "admin@ultorn.local").first()
        if not admin:
            admin = models.User(
                email="admin@ultorn.local",
                hashed_password=auth.get_password_hash("admin123"),
                full_name="Platform Admin",
                role=models.UserRole.admin,
            )
            db.add(admin)
            db.commit()
            print("Seeded admin user: admin@ultorn.local / admin123")
    finally:
        db.close()


# ============================================================
# Auth
# ============================================================
@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: dict, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.get("email", ""), form_data.get("password", ""))
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=user_in.email,
        hashed_password=auth.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# Clients
# ============================================================
@app.post("/clients", response_model=schemas.ClientOut)
def create_client(
    client_in: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = models.Client(**client_in.model_dump(), owner_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    audit.log_action(db, "create_client", user_id=current_user.id, client_id=client.id, details={"name": client_in.name})
    return client


@app.get("/clients", response_model=List[schemas.ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Client)
    if current_user.role == models.UserRole.client:
        query = query.filter(models.Client.owner_id == current_user.id)
    return query.all()


@app.get("/clients/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if current_user.role == models.UserRole.client and client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return client


# ============================================================
# Scan Scopes
# ============================================================
@app.post("/clients/{client_id}/scopes", response_model=schemas.ScanScopeOut)
def add_scope(
    client_id: int,
    scope_in: schemas.ScanScopeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    token = str(uuid.uuid4())
    scope = models.ScanScope(
        client_id=client_id,
        target=scope_in.target,
        target_type=scope_in.target_type,
        is_excluded=scope_in.is_excluded,
        verification_method=scope_in.verification_method,
        verification_token=token,
    )
    db.add(scope)
    db.commit()
    db.refresh(scope)
    audit.log_action(
        db, "add_scan_scope", user_id=current_user.id, client_id=client_id,
        resource_type="scan_scope", resource_id=str(scope.id),
        details={"target": scope_in.target, "verification_token": token},
    )
    return scope


@app.get("/clients/{client_id}/scopes", response_model=List[schemas.ScanScopeOut])
def list_scopes(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if current_user.role == models.UserRole.client and client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.ScanScope).filter(models.ScanScope.client_id == client_id).all()


@app.post("/scopes/{scope_id}/verify")
def verify_scope(
    scope_id: int,
    verification: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scope = db.query(models.ScanScope).filter(models.ScanScope.id == scope_id).first()
    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")
    token = verification.get("token", "")
    if token != scope.verification_token:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    scope.verified = True
    from sqlalchemy.sql import func
    scope.verified_at = func.now()
    db.commit()
    audit.log_action(
        db, "verify_scan_scope", user_id=current_user.id, client_id=scope.client_id,
        resource_type="scan_scope", resource_id=str(scope_id),
    )
    return {"verified": True}


# ============================================================
# Scans: NO verification gate, runs on all scopes
# ============================================================
@app.post("/scans", response_model=schemas.ScanOut)
def start_scan(
    scan_in: schemas.ScanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    client = db.query(models.Client).filter(models.Client.id == scan_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    scan = models.Scan(
        client_id=scan_in.client_id,
        requested_by_id=current_user.id,
        scan_type=scan_in.scan_type,
        status="running",
        configuration=json.dumps(scan_in.configuration) if scan_in.configuration else None,
    )
    from sqlalchemy.sql import func
    scan.started_at = func.now()
    db.add(scan)
    db.commit()
    db.refresh(scan)

    audit.log_action(
        db, "start_scan", user_id=current_user.id, client_id=scan_in.client_id,
        resource_type="scan", resource_id=str(scan.id),
        details={"scan_type": scan_in.scan_type},
    )
    return scan


@app.get("/scans", response_model=List[schemas.ScanOut])
def list_scans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Scan)
    if current_user.role == models.UserRole.client:
        query = query.join(models.Client).filter(models.Client.owner_id == current_user.id)
    return query.all()


@app.get("/scans/{scan_id}", response_model=schemas.ScanOut)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return scan


@app.post("/scans/{scan_id}/run")
def run_scan_endpoint(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan.status = "running"
    db.commit()

    # NO verification gate: runs on all non-excluded scopes
    scopes = db.query(models.ScanScope).filter(
        models.ScanScope.client_id == scan.client_id,
        models.ScanScope.is_excluded == False,
    ).all()

    all_findings = []
    for scope in scopes:
        results = scanner.run_scan(scope.target, scan.scan_type)
        for r in results:
            if "error" in r:
                continue
            finding = models.Finding(
                scan_id=scan.id,
                title=r.get("title", "Unknown"),
                description=r.get("description"),
                severity=r.get("severity", "info"),
                cvss_score=r.get("cvss_score"),
                owasp_category=None,
                target=r.get("target"),
                evidence=json.dumps(r.get("evidence")) if r.get("evidence") else None,
                remediation=r.get("remediation"),
            )
            db.add(finding)
            all_findings.append(finding)

    critical_high = [f for f in all_findings if f.severity in ("critical", "high")]

    scan.status = "completed"
    from sqlalchemy.sql import func
    scan.completed_at = func.now()
    scan.summary = json.dumps({
        "total_findings": len(all_findings),
        "critical": len([f for f in all_findings if f.severity == "critical"]),
        "high": len([f for f in all_findings if f.severity == "high"]),
        "medium": len([f for f in all_findings if f.severity == "medium"]),
        "low": len([f for f in all_findings if f.severity == "low"]),
        "requires_human_review": len(critical_high),
    })
    db.commit()
    db.refresh(scan)

    audit.log_action(
        db, "complete_scan", user_id=current_user.id, client_id=scan.client_id,
        resource_type="scan", resource_id=str(scan_id),
        details=scan.summary,
    )
    return {"status": "completed", "findings_count": len(all_findings), "requires_human_review": len(critical_high)}


# ============================================================
# Findings
# ============================================================
@app.get("/scans/{scan_id}/findings", response_model=List[schemas.FindingOut])
def get_findings(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if current_user.role == models.UserRole.client and scan.client.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Finding).filter(models.Finding.scan_id == scan_id).all()


@app.post("/findings/{finding_id}/review")
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
# AI / Sovereignty
# ============================================================
@app.post("/ai/query")
def ai_query(
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    prompt = request.get("prompt", "")
    client_name = request.get("client_name")
    force_local = request.get("force_local", False)

    client_obj = None
    if request.get("client_id"):
        client_obj = db.query(models.Client).filter(models.Client.id == request["client_id"]).first()
        if client_obj and current_user.role == models.UserRole.client and client_obj.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    response = ai_router.route_ai_query(
        prompt=prompt,
        client_name=client_name,
        user=current_user,
        client=client_obj,
        db=db,
        force_local=force_local,
    )
    return {"response": response}


@app.get("/ai/audit", response_model=List[schemas.AIQueryOut])
def ai_audit_log(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    return db.query(models.AIQueryLog).order_by(models.AIQueryLog.created_at.desc()).all()


# ============================================================
# Audit
# ============================================================
@app.get("/audit", response_model=List[schemas.AuditLogOut])
def get_audit_log(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin, models.UserRole.analyst)),
):
    entries = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).all()
    results = []
    for entry in entries:
        out = schemas.AuditLogOut.model_validate(entry)
        out.user_email = entry.user.email if entry.user else None
        results.append(out)
    return results


# ============================================================
# Sanitize (demo endpoint)
# ============================================================
@app.post("/sanitize")
def sanitize_endpoint(
    request: dict,
    current_user: models.User = Depends(auth.get_current_user),
):
    text = request.get("text", "")
    client_name = request.get("client_name")
    clean, stats = sanitize_text(text, client_name)
    return {"sanitized": clean, "stats": stats}


# ============================================================
# Admin: user management
# ============================================================
@app.get("/admin/users", response_model=List[schemas.UserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@app.patch("/admin/users/{user_id}", response_model=schemas.UserOut)
def admin_update_user(
    user_id: int,
    update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    changes = update.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    audit.log_action(
        db, "admin_update_user", user_id=current_user.id,
        resource_type="user", resource_id=str(user_id), details=changes,
    )
    return user


# ============================================================
# Admin: API key management
# ============================================================
@app.get("/admin/api-keys", response_model=List[schemas.APIKeyOut])
def admin_list_api_keys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    return db.query(models.APIKey).order_by(models.APIKey.created_at.desc()).all()


@app.post("/admin/api-keys", response_model=schemas.APIKeyCreated)
def admin_create_api_key(
    key_in: schemas.APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    raw_key, prefix, key_hash = auth.generate_api_key()
    key = models.APIKey(
        name=key_in.name,
        owner_id=current_user.id,
        key_prefix=prefix,
        key_hash=key_hash,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    audit.log_action(
        db, "admin_create_api_key", user_id=current_user.id,
        resource_type="api_key", resource_id=str(key.id),
        details={"name": key_in.name, "prefix": prefix},
    )
    return schemas.APIKeyCreated(**schemas.APIKeyOut.model_validate(key).model_dump(), api_key=raw_key)


@app.delete("/admin/api-keys/{key_id}")
def admin_revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.admin)),
):
    key = db.query(models.APIKey).filter(models.APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    from sqlalchemy.sql import func
    key.revoked_at = func.now()
    db.commit()
    audit.log_action(
        db, "admin_revoke_api_key", user_id=current_user.id,
        resource_type="api_key", resource_id=str(key_id),
    )
    return {"revoked": True}


# ============================================================
# Health
# ============================================================
@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
