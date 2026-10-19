"""Ultorn API entry point.

Route handlers live in :mod:`app.routers`, grouped by domain. This module
owns the application object: middleware, the startup seed and scheduler,
the fallback 404 shape, and router registration.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models, auth, scheduler
from app.routers import (
    admin as admin_router,
    ai as ai_router,
    audit as audit_router,
    auth as auth_router,
    clients as clients_router,
    code_scans as code_scans_router,
    compliance as compliance_router,
    findings as findings_router,
    monitors as monitors_router,
    reports as reports_router,
    scans as scans_router,
    system as system_router,
)

# Create tables that do not exist yet (Alembic owns migrations in production).
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

    # Continuous monitoring. Disable with ENABLE_SCHEDULER=false (e.g. when
    # running multiple API replicas so only one process schedules jobs).
    import os

    if os.getenv("ENABLE_SCHEDULER", "true").lower() not in ("0", "false", "no"):
        try:
            scheduled = scheduler.bootstrap()
            scheduler.start()
            print(
                f"Scheduler started: {len(scheduled['monitors'])} monitor(s), "
                f"{len(scheduled['scan_schedules'])} scan schedule(s)"
            )
        except Exception as exc:  # pragma: no cover - startup must not crash
            print(f"Scheduler failed to start: {exc}")


# ------------------------------------------------------------
# Routers: one module per domain (see app/routers/__init__.py)
# ------------------------------------------------------------
for _router in (
    admin_router.router,
    ai_router.router,
    audit_router.router,
    auth_router.router,
    clients_router.router,
    code_scans_router.router,
    compliance_router.router,
    findings_router.router,
    monitors_router.router,
    reports_router.router,
    scans_router.router,
    system_router.router,
):
    app.include_router(_router)


@app.exception_handler(StarletteHTTPException)
async def not_found_hint(request: Request, exc: StarletteHTTPException):
    """Keep FastAPI's error shape but add a pointer for unrouted paths."""
    if exc.status_code == 404 and exc.detail == "Not Found":
        path = request.url.path
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Not Found",
                "path": path,
                "hint": (
                    "No route matches this path. See /docs for the API index. "
                    "Ultorn does not expose OpenAI-compatible /v1/* endpoints."
                ),
                "docs": "/docs",
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )
