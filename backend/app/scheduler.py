from __future__ import annotations

"""Recurring scan scheduler for continuous monitoring."""

import schedule
import time
import threading
from app.worker import process_monitor_check
from app.database import SessionLocal
from app import models


def run_scheduler():
    """Run the background scheduler loop."""
    def loop():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread


def schedule_monitor(monitor_id: int, interval_minutes: int = 60):
    """Schedule a recurring monitor check."""
    def job():
        db = SessionLocal()
        try:
            monitor = db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()
            if monitor and monitor.is_active:
                process_monitor_check(monitor_id)
        finally:
            db.close()

    schedule.every(interval_minutes).minutes.do(job)
    print(f"Scheduled monitor {monitor_id} every {interval_minutes} minutes")
