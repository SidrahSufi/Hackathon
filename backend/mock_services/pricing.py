"""
Mock pricing-update service — logs only, no external calls.
"""
from uuid import uuid4

import structlog

log = structlog.get_logger()


def mock_update_pricing(
    region: str,
    sku_list: list,
    discount_pct: float,
    run_id: str,
) -> dict:
    update_id = f"price-{uuid4().hex[:8]}"
    log.info(
        "mock_pricing_updated",
        region=region,
        sku_count=len(sku_list),
        discount_pct=discount_pct,
        update_id=update_id,
        run_id=run_id,
    )
    return {
        "status": "applied",
        "update_id": update_id,
        "skus_updated": len(sku_list),
    }
