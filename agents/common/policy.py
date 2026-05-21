"""
PolicyChecker — enforces constraints on every action before execution.

Pure-Python decision logic (no LLM). Loads rules from config/policies.yaml.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

import structlog
import yaml

log = structlog.get_logger()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class PolicyChecker:
    """Validates actions against budget, discount, rate-limit, and window policies."""

    def __init__(self, policies_path: str | Path | None = None):
        if policies_path is None:
            policies_path = _workspace_root() / "config" / "policies.yaml"
        self.policies_path = Path(policies_path)
        with open(self.policies_path, "r", encoding="utf-8") as fh:
            self.policies: dict[str, Any] = yaml.safe_load(fh)

        # in-memory counters
        self._cumulative_spend_pkr: float = 0.0
        self._notification_count_this_hour: int = 0
        self._campaign_count_per_region_per_week: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, action: dict) -> dict:
        """
        Validate a single action against all applicable policies.

        Returns: {"ok": bool, "violations": list, "suggested_revisions": dict}
        """
        violations: list[dict] = []
        suggested: dict[str, Any] = {}

        # ---- Budget ----
        cost = float(action.get("cost_pkr", 0) or 0)
        cap = float(self.policies["budget"]["cap"])
        if self._cumulative_spend_pkr + cost > cap:
            violations.append({
                "type": "budget",
                "detail": (
                    f"Action would push cumulative spend to "
                    f"{self._cumulative_spend_pkr + cost:.0f} PKR, "
                    f"over cap {cap:.0f}"
                ),
            })

        # ---- Discount ----
        discount_pct = action.get("discount_pct")
        if discount_pct is not None:
            max_pct = float(self.policies["discount"]["max_pct"])
            margin_floor = float(self.policies["discount"]["margin_floor_pct"])
            if discount_pct > max_pct:
                violations.append({
                    "type": "discount",
                    "detail": f"discount_pct {discount_pct} exceeds max {max_pct}",
                })
                suggested["discount_pct"] = max_pct
            # margin floor — discount cannot drop margin below floor
            # we model this conservatively: any discount above (100 - margin_floor) is rejected
            elif discount_pct > (100 - margin_floor):
                violations.append({
                    "type": "discount_margin",
                    "detail": (
                        f"discount_pct {discount_pct} would breach margin floor "
                        f"{margin_floor}%"
                    ),
                })
                suggested["discount_pct"] = max(margin_floor, 100 - margin_floor)

        # ---- Notification window ----
        scheduled = action.get("scheduled_time")
        if scheduled is not None:
            window = self.policies["notification_window"]
            start = self._parse_time(window["start"])
            end = self._parse_time(window["end"])
            sched_dt = self._coerce_dt(scheduled)
            if sched_dt is not None:
                if not (start <= sched_dt.time() <= end):
                    violations.append({
                        "type": "notification_window",
                        "detail": (
                            f"scheduled_time {sched_dt.time()} outside window "
                            f"{start} – {end}"
                        ),
                    })
                    suggested["scheduled_time"] = self._next_valid_slot(
                        sched_dt, start
                    ).isoformat()

        # ---- Rate limit: notification API ----
        if action.get("tool") in {"mock_draft_notification", "mock_send_push"}:
            audience = int(action.get("audience_size", 0) or 0)
            cap_per_hour = int(self.policies["rate_limits"]["notification_api_per_hour"])
            if self._notification_count_this_hour + audience > cap_per_hour:
                violations.append({
                    "type": "rate_limit",
                    "detail": (
                        f"Notification API would send "
                        f"{self._notification_count_this_hour + audience} this hour, "
                        f"over limit {cap_per_hour}"
                    ),
                })

        # ---- Rate limit: campaign launch ----
        if action.get("tool") == "mock_launch_campaign":
            region = action.get("region")
            if region is not None:
                count = self._campaign_count_per_region_per_week.get(region, 0)
                cap_pr = int(
                    self.policies["rate_limits"]["campaign_launch_per_region_per_week"]
                )
                if count + 1 > cap_pr:
                    violations.append({
                        "type": "rate_limit_campaign",
                        "detail": (
                            f"Campaign launches in {region} this week: "
                            f"{count + 1} > {cap_pr}"
                        ),
                    })

        ok = len(violations) == 0
        return {
            "ok": ok,
            "violations": violations,
            "suggested_revisions": suggested,
        }

    def record_usage(self, action: dict, result: dict) -> None:
        """Update cumulative counters after an action has executed."""
        # budget — only count successful actions
        if result.get("success", True):
            self._cumulative_spend_pkr += float(action.get("cost_pkr", 0) or 0)

        # notification volume
        if action.get("tool") in {"mock_draft_notification", "mock_send_push"}:
            self._notification_count_this_hour += int(
                action.get("audience_size", 0) or 0
            )

        # campaign launch
        if action.get("tool") == "mock_launch_campaign":
            region = action.get("region")
            if region:
                self._campaign_count_per_region_per_week[region] = (
                    self._campaign_count_per_region_per_week.get(region, 0) + 1
                )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_time(s: str) -> time:
        hh, mm = s.split(":")
        return time(hour=int(hh), minute=int(mm))

    @staticmethod
    def _coerce_dt(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _next_valid_slot(sched_dt: datetime, start: time) -> datetime:
        """Return the next datetime at `start` time, on or after sched_dt's date."""
        candidate = sched_dt.replace(
            hour=start.hour, minute=start.minute, second=0, microsecond=0
        )
        if candidate <= sched_dt:
            candidate += timedelta(days=1)
        return candidate

    # ------------------------------------------------------------------
    # Introspection (for tests + UI)
    # ------------------------------------------------------------------

    @property
    def cumulative_spend_pkr(self) -> float:
        return self._cumulative_spend_pkr

    def reset(self) -> None:
        self._cumulative_spend_pkr = 0.0
        self._notification_count_this_hour = 0
        self._campaign_count_per_region_per_week = {}
