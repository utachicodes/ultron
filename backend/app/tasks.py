from __future__ import annotations

"""Celery tasks dispatched by the scheduler loop.

Thin wrappers around `app.worker`'s plain functions, which stay importable
and directly callable (no queue involved) for manual "run now" actions
triggered from the API -- those want the result in the same request, not a
round trip through a queue. Only the periodic scheduler path enqueues these.
"""

from app.celery_app import celery_app
from app import worker


@celery_app.task(name="ultorn.check_monitor")
def check_monitor(monitor_id: int) -> int:
    return worker.process_monitor_check(monitor_id)


@celery_app.task(name="ultorn.run_scheduled_scan")
def run_scheduled_scan(schedule_id: int) -> int:
    return worker.process_scheduled_scan(schedule_id)
