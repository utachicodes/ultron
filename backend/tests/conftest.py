from __future__ import annotations

"""Test fixtures.

Sets an isolated SQLite database and disables the background scheduler
*before* the application (which runs create_all at import time) is loaded.
"""

import os
import tempfile

import pytest

# Must happen before `app.main` is imported anywhere.
_tmpdir = tempfile.mkdtemp(prefix="ultorn-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine, SessionLocal  # noqa: E402
from app import models, auth, rate_limit  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    """Fresh schema and empty rate-limit buckets for every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limit.reset()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_token(db):
    user = models.User(
        email="admin@test.local",
        hashed_password=auth.get_password_hash("admin123"),
        full_name="Test Admin",
        role=models.UserRole.admin,
    )
    db.add(user)
    db.commit()
    return auth.create_access_token(data={"sub": user.email})


@pytest.fixture
def client(admin_token):
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {admin_token}"})
    return c


@pytest.fixture
def anon():
    return TestClient(app)


@pytest.fixture
def sample_client(client):
    res = client.post(
        "/clients",
        json={"name": "Test Bank", "contact_email": "sec@testbank.sn", "sector": "banking"},
    )
    assert res.status_code == 200, res.text
    return res.json()
