from __future__ import annotations

"""Celery application for distributed scheduled work.

The in-process `schedule` library (see `scheduler.py`) still owns *when* a
monitor check or scheduled scan is due -- that part doesn't need a queue.
What it used to do wrong is *run* that work inline, in whichever API replica
happened to be ticking, with no coordination between replicas. If you scale
the API to N replicas, each one eventually runs its own scheduler loop and
N copies of the same check fire.

Now the scheduler loop only enqueues a Celery task (`tasks.check_monitor` /
`tasks.run_scheduled_scan`). A separate `celery -A app.celery_app worker`
process (or a replicated fleet of them) actually executes the work exactly
once per enqueued job, backed by Redis as the broker/result store.

In tests and in any environment without a running worker, set
`CELERY_TASK_ALWAYS_EAGER=true` (already the default for `pytest`, via
`tests/conftest.py`) so `.delay()` runs the task inline and synchronously --
no Redis required.
"""

from celery import Celery

from app.config import settings

celery_app = Celery("ultorn", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_always_eager,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
)
