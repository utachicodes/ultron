from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app import auth, models
from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def isolated_attachment_dir(tmp_path, monkeypatch):
    """Keep uploaded files out of the repo during tests."""
    monkeypatch.setattr(settings, "attachment_storage_dir", str(tmp_path / "attachments"))
    yield


def _make_finding(client, db, sample_client):
    scan = client.post(
        "/scans",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability"},
    ).json()
    client.post(f"/scans/{scan['id']}/run")
    finding = models.Finding(
        scan_id=scan["id"],
        title="Evidence test finding",
        severity="high",
        status="open",
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def _client_owner_token(db, sample_client):
    """A client-role user who owns `sample_client` (its owner is the admin
    fixture user, so this creates a *different* client-role account, used to
    assert cross-client isolation)."""
    user = models.User(
        email="other-client@test.local",
        hashed_password=auth.get_password_hash("pw12345"),
        full_name="Other Client",
        role=models.UserRole.client,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return auth.create_access_token(data={"sub": user.email})


def test_upload_list_download_roundtrip(client, db, sample_client):
    finding = _make_finding(client, db, sample_client)

    content = b"scanner raw output line 1\nline 2\n"
    res = client.post(
        f"/findings/{finding.id}/attachments",
        files={"file": ("raw-output.txt", content, "text/plain")},
    )
    assert res.status_code == 200, res.text
    attachment = res.json()
    assert attachment["filename"] == "raw-output.txt"
    assert attachment["content_type"] == "text/plain"
    assert attachment["size_bytes"] == len(content)
    assert attachment["finding_id"] == finding.id

    listed = client.get(f"/findings/{finding.id}/attachments")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == attachment["id"]

    downloaded = client.get(f"/findings/{finding.id}/attachments/{attachment['id']}")
    assert downloaded.status_code == 200
    assert downloaded.content == content

    # On-disk file exists and is not named after the original filename
    # (safe, non-guessable storage name).
    db_row = db.query(models.FindingAttachment).filter_by(id=attachment["id"]).first()
    assert os.path.isfile(db_row.storage_path)
    assert os.path.basename(db_row.storage_path) != "raw-output.txt"


def test_upload_rejected_over_size_limit(client, db, sample_client, monkeypatch):
    finding = _make_finding(client, db, sample_client)
    monkeypatch.setattr(settings, "attachment_max_size_mb", 1 / 1024 / 1024 * 0.001)  # ~ a few bytes

    res = client.post(
        f"/findings/{finding.id}/attachments",
        files={"file": ("too-big.bin", b"x" * 10000, "application/octet-stream")},
    )
    assert res.status_code == 400

    # Nothing was persisted.
    assert db.query(models.FindingAttachment).filter_by(finding_id=finding.id).count() == 0


def test_other_client_cannot_access_attachments(client, db, sample_client):
    finding = _make_finding(client, db, sample_client)
    res = client.post(
        f"/findings/{finding.id}/attachments",
        files={"file": ("evidence.png", b"fakeimagebytes", "image/png")},
    )
    assert res.status_code == 200
    attachment_id = res.json()["id"]

    other_token = _client_owner_token(db, sample_client)
    other = TestClient(app)
    other.headers.update({"Authorization": f"Bearer {other_token}"})

    assert other.get(f"/findings/{finding.id}/attachments").status_code == 403
    assert other.get(f"/findings/{finding.id}/attachments/{attachment_id}").status_code == 403
    assert other.post(
        f"/findings/{finding.id}/attachments",
        files={"file": ("x.txt", b"data", "text/plain")},
    ).status_code == 403


def test_anonymous_cannot_access_attachments(anon, db, client, sample_client):
    finding = _make_finding(client, db, sample_client)
    assert anon.get(f"/findings/{finding.id}/attachments").status_code == 401
    assert anon.post(
        f"/findings/{finding.id}/attachments",
        files={"file": ("x.txt", b"data", "text/plain")},
    ).status_code == 401


def test_delete_removes_db_row_and_file(client, db, sample_client):
    finding = _make_finding(client, db, sample_client)
    res = client.post(
        f"/findings/{finding.id}/attachments",
        files={"file": ("to-delete.txt", b"bye", "text/plain")},
    )
    attachment_id = res.json()["id"]
    db_row = db.query(models.FindingAttachment).filter_by(id=attachment_id).first()
    storage_path = db_row.storage_path
    assert os.path.isfile(storage_path)

    del_res = client.delete(f"/findings/{finding.id}/attachments/{attachment_id}")
    assert del_res.status_code == 200, del_res.text

    assert db.query(models.FindingAttachment).filter_by(id=attachment_id).first() is None
    assert not os.path.isfile(storage_path)

    # Deleting again (or a dangling disk file) must not crash.
    assert client.get(f"/findings/{finding.id}/attachments/{attachment_id}").status_code == 404


def test_attachment_id_scoped_to_finding(client, db, sample_client):
    finding_a = _make_finding(client, db, sample_client)
    finding_b = _make_finding(client, db, sample_client)

    res = client.post(
        f"/findings/{finding_a.id}/attachments",
        files={"file": ("a.txt", b"a", "text/plain")},
    )
    attachment_id = res.json()["id"]

    # Same attachment id, wrong finding id in the path -> not found.
    assert client.get(f"/findings/{finding_b.id}/attachments/{attachment_id}").status_code == 404
    assert client.delete(f"/findings/{finding_b.id}/attachments/{attachment_id}").status_code == 404
