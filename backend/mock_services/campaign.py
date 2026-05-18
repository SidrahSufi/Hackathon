"""
Mock campaign-launch service — logs only, no external calls.
"""
from uuid import uuid4

import structlog

log = structlog.get_logger()


def mock_launch_campaign(
    region: str,
    segment: str,
    discount_pct: int,
    run_id: str,
) -> dict:
    campaign_id = f"camp_{region.lower()}_{uuid4().hex[:4]}"
    log.info(
        "mock_campaign_launched",
        region=region,
        segment=segment,
        discount_pct=discount_pct,
        campaign_id=campaign_id,
        run_id=run_id,
    )
    return {"campaign_id": campaign_id, "status": "active"}
