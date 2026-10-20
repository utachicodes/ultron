from __future__ import annotations

"""Application configuration.

Security note: if `SECRET_KEY` is left at its development default, a random
key is generated on first boot and persisted next to the database. Tokens then
survive restarts without ever shipping a known key.
"""

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings

DEV_SECRET = "dev-secret-change-me"
_BASE_DIR = Path(__file__).resolve().parent.parent


def _secret_file() -> Path:
    """Store the generated key beside the SQLite database when possible so it
    survives container re-creation; otherwise fall back to the app directory."""
    import os

    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        db_path = Path(db_url[len("sqlite:///"):])
        try:
            return db_path.resolve().parent / ".secret_key"
        except OSError:
            pass
    return _BASE_DIR / ".secret_key"


def _resolve_secret() -> str:
    """Load SECRET_KEY from env if set, else a generated key stored on disk."""
    import os

    env_secret = os.getenv("SECRET_KEY")
    if env_secret and env_secret != DEV_SECRET:
        return env_secret

    key_file = _secret_file()
    if key_file.exists():
        existing = key_file.read_text().strip()
        if existing:
            return existing

    generated = secrets.token_urlsafe(48)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(generated)
        key_file.chmod(0o600)
    except OSError:
        # Read-only filesystem: fall back to an ephemeral key. Tokens will
        # not survive a restart, which is safer than a known default.
        pass
    return generated


class Settings(BaseSettings):
    app_name: str = "Ultorn"
    debug: bool = True
    database_url: str = "sqlite:///./ultorn.db"
    secret_key: str = _resolve_secret()
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI providers. "ollama" talks to a local, open-source model (no API key,
    # no external network call) -- useful for exercising the AI Guard flow
    # end to end without paying for Anthropic/OpenAI access.
    ai_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Scanning
    scanner_timeout: int = 300
    nuclei_path: str = "nuclei"

    # Alert delivery (optional)
    alert_webhook_url: str = ""
    alert_webhook_secret: str = ""

    # Background queue: periodic scheduler ticks enqueue work here instead of
    # running it in-process, so multiple API replicas never duplicate a run.
    # A separate `celery -A app.celery_app worker` process executes it.
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False

    # Password reset
    password_reset_token_expire_minutes: int = 30

    # Finding evidence attachments
    attachment_storage_dir: str = "./attachments"
    attachment_max_size_mb: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
