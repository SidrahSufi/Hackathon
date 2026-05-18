"""
Mock push-notification service — logs only, no external calls.
"""
from uuid import uuid4

import structlog

log = structlog.get_logger()


def mock_send_push(
    user_segment: str,
    title: str,
    body: str,
    run_id: str,
) -> dict:
    notif_id = f"push-{uuid4().hex[:8]}"
    log.info(
        "mock_push_sent",
        user_segment=user_segment,
        title=title,
        notification_id=notif_id,
        run_id=run_id,
    )
    return {"status": "delivered", "notification_id": notif_id}
