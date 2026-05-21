"""
Mock external tools for the PulseAI Executor.

Every mock returns a dict shaped like:
    {"success": bool, "latency_ms": int, "details": dict | str}

For the demo we run deterministic behavior — failure injection is controlled
by config/policies.yaml so the demo can show retry + fallback live.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

import structlog

log = structlog.get_logger()

# Module-level call counters so we can sequence "first call fails, retry succeeds"
_call_counters: dict[str, int] = {}


def _bump(name: str) -> int:
    _call_counters[name] = _call_counters.get(name, 0) + 1
    return _call_counters[name]


def reset_counters() -> None:
    """Test helper — clear call counters."""
    _call_counters.clear()


# ---------------------------------------------------------------------------
# A1: Diagnose target — segment breakdown
# ---------------------------------------------------------------------------
def mock_segment_breakdown(region: str, **kwargs: Any) -> dict:
    """Simulate diagnosing affected SKUs and customer segments."""
    _bump("mock_segment_breakdown")
    log.info("mock_segment_breakdown", region=region)
    return {
        "success": True,
        "latency_ms": 320,
        "details": {
            "region": region,
            "skus_identified": 412,
            "segments": [
                {
                    "category": "women's casual wear",
                    "age_range": [22, 32],
                    "share_of_decline": 0.62,
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# A2: Notify regional managers
# ---------------------------------------------------------------------------
def mock_send_email(to: list[str], subject: str, body: str, **kwargs: Any) -> dict:
    """Simulate sending an email."""
    _bump("mock_send_email")
    log.info("mock_send_email", to=to, subject=subject[:50])
    return {
        "success": True,
        "latency_ms": 180,
        "details": {
            "recipients": to,
            "subject": subject,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def mock_send_push(user_id: str, message: str, **kwargs: Any) -> dict:
    """Fallback for email — push notification."""
    _bump("mock_send_push")
    log.info("mock_send_push", user_id=user_id)
    return {
        "success": True,
        "latency_ms": 90,
        "details": {"user_id": user_id, "message": message},
    }


# ---------------------------------------------------------------------------
# A3: Launch campaign
# ---------------------------------------------------------------------------
def mock_launch_campaign(
    region: str,
    segment: dict,
    discount_pct: float,
    budget_pkr: float,
    **kwargs: Any,
) -> dict:
    """Simulate launching a regional discount campaign."""
    _bump("mock_launch_campaign")
    campaign_id = f"camp-{region.lower()}-{_call_counters['mock_launch_campaign']}"
    # Projected reach is a small model: budget × engagement_factor.
    projected_reach = int(budget_pkr * 0.0072)  # 720000 -> ~5184
    log.info(
        "mock_launch_campaign",
        region=region,
        discount_pct=discount_pct,
        budget_pkr=budget_pkr,
        projected_reach=projected_reach,
    )
    return {
        "success": True,
        "latency_ms": 410,
        "details": {
            "campaign_id": campaign_id,
            "region": region,
            "segment": segment,
            "discount_pct": discount_pct,
            "budget_pkr": budget_pkr,
            "projected_reach": projected_reach,
        },
    }


def mock_pause_campaign(campaign_id: str, **kwargs: Any) -> dict:
    """Compensating action for mock_launch_campaign."""
    _bump("mock_pause_campaign")
    log.info("mock_pause_campaign", campaign_id=campaign_id)
    return {
        "success": True,
        "latency_ms": 75,
        "details": {"campaign_id": campaign_id, "status": "paused"},
    }


# ---------------------------------------------------------------------------
# A4: Update pricing + draft notifications
# ---------------------------------------------------------------------------
def mock_update_pricing(
    region: str,
    sku_list: list[str],
    discount_pct: float,
    **kwargs: Any,
) -> dict:
    """Simulate applying a checkout discount."""
    _bump("mock_update_pricing")
    log.info("mock_update_pricing", region=region, sku_count=len(sku_list or []))
    return {
        "success": True,
        "latency_ms": 240,
        "details": {
            "region": region,
            "sku_count": len(sku_list or []),
            "discount_pct": discount_pct,
        },
    }


def mock_revert_pricing(region: str, **kwargs: Any) -> dict:
    """Compensating action for mock_update_pricing."""
    _bump("mock_revert_pricing")
    log.info("mock_revert_pricing", region=region)
    return {
        "success": True,
        "latency_ms": 110,
        "details": {"region": region, "reverted": True},
    }


# ---------------------------------------------------------------------------
# A4 side effect: notification draft — built-in failure injection
# ---------------------------------------------------------------------------
def mock_draft_notification(
    channel: str,
    audience_size: int,
    inject_failure: bool = True,
    **kwargs: Any,
) -> dict:
    """
    Simulate drafting a customer notification.

    First call fails (the demo's headline failure moment).
    The Executor's retry path will reduce audience_size (batching) and re-call.
    A reduced batch (<2000) succeeds.
    """
    attempts = _bump("mock_draft_notification")
    if inject_failure and attempts == 1:
        log.warning(
            "mock_draft_notification: notification API failure",
            audience_size=audience_size,
        )
        return {
            "success": False,
            "latency_ms": 8200,
            "details": {
                "error": "notification_api_timeout",
                "audience_size": audience_size,
            },
        }

    # Retry with batching: succeed if audience_size <= 2000
    if audience_size and audience_size > 2000:
        return {
            "success": False,
            "latency_ms": 4100,
            "details": {
                "error": "audience_too_large_for_retry",
                "audience_size": audience_size,
            },
        }

    log.info("mock_draft_notification: success", audience_size=audience_size)
    return {
        "success": True,
        "latency_ms": 290,
        "details": {
            "channel": channel,
            "audience_size": audience_size,
            "drafted": True,
        },
    }


def mock_in_app_banner(message: str, region: str, **kwargs: Any) -> dict:
    """Fallback for failed notification — show in-app banner."""
    _bump("mock_in_app_banner")
    log.info("mock_in_app_banner", region=region)
    return {
        "success": True,
        "latency_ms": 60,
        "details": {"region": region, "message": message},
    }


# ---------------------------------------------------------------------------
# A5: Monitor scheduler
# ---------------------------------------------------------------------------
def mock_schedule_monitor(
    run_id: str,
    window_days: int = 7,
    **kwargs: Any,
) -> dict:
    """Schedule the 7-day post-campaign monitor."""
    _bump("mock_schedule_monitor")
    log.info("mock_schedule_monitor", run_id=run_id, window_days=window_days)
    return {
        "success": True,
        "latency_ms": 25,
        "details": {
            "run_id": run_id,
            "monitor_window_days": window_days,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# Tool registry — used by Executor
# ---------------------------------------------------------------------------
TOOL_REGISTRY: dict[str, Any] = {
    "mock_segment_breakdown": mock_segment_breakdown,
    "mock_send_email": mock_send_email,
    "mock_send_push": mock_send_push,
    "mock_launch_campaign": mock_launch_campaign,
    "mock_pause_campaign": mock_pause_campaign,
    "mock_update_pricing": mock_update_pricing,
    "mock_revert_pricing": mock_revert_pricing,
    "mock_draft_notification": mock_draft_notification,
    "mock_in_app_banner": mock_in_app_banner,
    "mock_schedule_monitor": mock_schedule_monitor,
}
