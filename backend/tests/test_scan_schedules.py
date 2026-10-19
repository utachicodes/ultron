from __future__ import annotations

import schedule

from app import scheduler


def teardown_function():
    scheduler.stop()


def _create(client, sample_client, interval=60):
    res = client.post(
        "/scan-schedules",
        json={
            "client_id": sample_client["id"],
            "scan_type": "vulnerability",
            "interval_minutes": interval,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_create_and_list_scan_schedules(client, sample_client):
    created = _create(client, sample_client)
    assert created["is_active"] is True
    assert created["interval_minutes"] == 60

    listed = client.get("/scan-schedules")
    assert listed.status_code == 200
    assert any(s["id"] == created["id"] for s in listed.json())


def test_create_schedule_rejects_unknown_client(client):
    res = client.post(
        "/scan-schedules",
        json={"client_id": 99999, "scan_type": "vulnerability", "interval_minutes": 60},
    )
    assert res.status_code == 404


def test_create_schedule_rejects_bad_interval(client, sample_client):
    res = client.post(
        "/scan-schedules",
        json={"client_id": sample_client["id"], "scan_type": "vulnerability", "interval_minutes": 0},
    )
    assert res.status_code == 400


def test_patch_schedule_reschedules_jobs(client, sample_client):
    created = _create(client, sample_client)
    tag = f"scan-schedule-{created['id']}"
    assert len(schedule.get_jobs(tag)) == 1

    res = client.patch(f"/scan-schedules/{created['id']}", json={"interval_minutes": 120})
    assert res.status_code == 200, res.text
    assert res.json()["interval_minutes"] == 120
    assert len(schedule.get_jobs(tag)) == 1

    res = client.patch(f"/scan-schedules/{created['id']}", json={"is_active": False})
    assert res.json()["is_active"] is False
    assert len(schedule.get_jobs(tag)) == 0


def test_delete_schedule_removes_job(client, sample_client):
    created = _create(client, sample_client)
    assert client.delete(f"/scan-schedules/{created['id']}").status_code == 200
    assert len(schedule.get_jobs(f"scan-schedule-{created['id']}")) == 0
    assert client.patch(
        f"/scan-schedules/{created['id']}", json={"is_active": True}
    ).status_code == 404


def test_run_schedule_now_creates_a_scan(client, sample_client, db):
    from app import models

    db.add(
        models.ScanScope(
            client_id=sample_client["id"],
            target="127.0.0.1",
            target_type="ip",
        )
    )
    db.commit()

    created = _create(client, sample_client)
    before = len(client.get("/scans").json())

    res = client.post(f"/scan-schedules/{created['id']}/run")
    assert res.status_code == 200, res.text
    scan_id = res.json()["scan_id"]
    assert scan_id

    after = client.get("/scans").json()
    assert len(after) == before + 1
    assert any(s["id"] == scan_id for s in after)

    updated = client.get("/scan-schedules").json()
    row = next(s for s in updated if s["id"] == created["id"])
    assert row["last_run"] is not None
    assert row["next_run"] is not None


def test_bootstrap_includes_active_schedules(client, sample_client):
    active = _create(client, sample_client)
    paused = _create(client, sample_client, interval=120)
    client.patch(f"/scan-schedules/{paused['id']}", json={"is_active": False})

    scheduler.stop()
    result = scheduler.bootstrap()

    assert active["id"] in result["scan_schedules"]
    assert paused["id"] not in result["scan_schedules"]
