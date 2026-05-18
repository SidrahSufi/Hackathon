"""
Mock monitor-scheduling service — logs only, no external calls.
"""
from uuid import uuid4

import structlog

log = structlog.get_logger()


def mock_schedule_monitor(
    region: str,
    metric: str,
    interval_hours: int,
    run_id: str,
) -> dict:
    schedule_id = f"sched-{uuid4().hex[:8]}"
    log.info(
        "mock_monitor_scheduled",
        region=region,
        metric=metric,
        interval_hours=interval_hours,
        schedule_id=schedule_id,
        run_id=run_id,
    )
    return {
        "status": "scheduled",
        "schedule_id": schedule_id,
        "next_check_in_hours": interval_hours,
    }
