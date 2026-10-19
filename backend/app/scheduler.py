from __future__ import annotations

"""Recurring scan scheduler for continuous monitoring.

The `schedule` library keeps a process-global job registry, so every monitor
is tagged with its own id. Re-scheduling a monitor replaces its previous job
instead of stacking duplicates.
"""

import threading
import time

import schedule

from app.worker import process_monitor_check

_scheduler_thread: threading.Thread | None = None
_started = False


def _job_tag(monitor_id: int) -> str:
    return f"monitor-{monitor_id}"


def schedule_monitor(monitor_id: int, interval_minutes: int = 60) -> None:
    """Schedule (or re-schedule) a recurring monitor check."""
    tag = _job_tag(monitor_id)

    for existing in list(schedule.get_jobs(tag)):
        schedule.cancel_job(existing)

    schedule.every(interval_minutes).minutes.do(
        process_monitor_check, monitor_id=monitor_id
    ).tag(tag)


def unschedule_monitor(monitor_id: int) -> None:
    for existing in list(schedule.get_jobs(_job_tag(monitor_id))):
        schedule.cancel_job(existing)


def bootstrap() -> list[int]:
    """Load every active monitor from the database into the scheduler.

    Returns the monitor ids that were scheduled. Safe to call repeatedly.
    """
    from app.database import SessionLocal
    from app import models

    scheduled: list[int] = []
    db = SessionLocal()
    try:
        monitors = db.query(models.Monitor).filter(models.Monitor.is_active == True).all()
        for monitor in monitors:
            schedule_monitor(monitor.id)
            scheduled.append(monitor.id)
    finally:
        db.close()
    return scheduled


def _loop() -> None:
    while True:
        try:
            schedule.run_pending()
        except Exception:
            # A single failing job must never kill the scheduler thread.
            pass
        time.sleep(30)


def start() -> threading.Thread:
    """Start the scheduler thread once. Returns the existing thread if running."""
    global _scheduler_thread, _started

    if _started and _scheduler_thread and _scheduler_thread.is_alive():
        return _scheduler_thread

    bootstrap()
    _scheduler_thread = threading.Thread(target=_loop, name="ultorn-scheduler", daemon=True)
    _scheduler_thread.start()
    _started = True
    return _scheduler_thread


def stop() -> None:
    global _started
    schedule.clear()
    _started = False
