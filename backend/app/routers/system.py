"""Root index and health probe."""

from fastapi import APIRouter

from app import scheduler
from app.config import settings

router = APIRouter()

# ============================================================
# Root, Health, and friendly 404s
# ============================================================
@router.get("/")
def root():
    """Landing payload so hitting the API root is never a bare 404."""
    return {
        "app": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "message": "Ultorn API. Interactive docs live at /docs.",
    }


@router.get("/health")
def health():
    """Liveness/readiness probe. Does not require auth."""
    from sqlalchemy import text
    from app.database import SessionLocal

    db_status = "ok"
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    finally:
        db.close()

    jobs = scheduler.job_count()
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "database": db_status,
        "scheduler": {"running": scheduler.is_running(), "jobs": jobs},
    }
