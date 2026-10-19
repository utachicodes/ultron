from __future__ import annotations

import schedule

from app import scheduler


def teardown_function():
    scheduler.stop()


def test_schedule_monitor_is_idempotent():
    scheduler.schedule_monitor(1)
    scheduler.schedule_monitor(1)
    scheduler.schedule_monitor(1)
    assert len(schedule.get_jobs("monitor-1")) == 1


def test_distinct_monitors_get_distinct_jobs():
    scheduler.schedule_monitor(1)
    scheduler.schedule_monitor(2)
    assert len(schedule.get_jobs("monitor-1")) == 1
    assert len(schedule.get_jobs("monitor-2")) == 1


def test_unschedule_removes_only_that_monitor():
    scheduler.schedule_monitor(1)
    scheduler.schedule_monitor(2)
    scheduler.unschedule_monitor(1)
    assert len(schedule.get_jobs("monitor-1")) == 0
    assert len(schedule.get_jobs("monitor-2")) == 1


def test_bootstrap_schedules_active_monitors(client, sample_client):
    active = client.post(
        "/monitors",
        json={"target": "example.com", "monitor_type": "config_drift", "client_id": sample_client["id"]},
    ).json()
    paused = client.post(
        "/monitors",
        json={"target": "example.org", "monitor_type": "config_drift", "client_id": sample_client["id"]},
    ).json()
    client.patch(f"/monitors/{paused['id']}", json={"is_active": False})

    scheduler.stop()
    scheduled = scheduler.bootstrap()

    assert active["id"] in scheduled
    assert paused["id"] not in scheduled
    assert len(schedule.get_jobs(f"monitor-{active['id']}")) == 1
    assert len(schedule.get_jobs(f"monitor-{paused['id']}")) == 0


def test_paused_monitor_skipped_by_scheduler_logic(client, sample_client, db):
    from app import worker

    monitor = client.post(
        "/monitors",
        json={"target": "http://127.0.0.1:9/nope", "monitor_type": "access_anomaly", "client_id": sample_client["id"]},
    ).json()
    client.patch(f"/monitors/{monitor['id']}", json={"is_active": False})

    # Scheduled path honours the pause.
    assert worker.process_monitor_check(monitor["id"]) == 0

    # Explicit operator check overrides it.
    assert client.post(f"/monitors/{monitor['id']}/check").json()["alerts_created"] == 1
