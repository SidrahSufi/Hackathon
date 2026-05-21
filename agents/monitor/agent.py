"""
Monitor Agent — post-execution stage of the PulseAI pipeline.

In the real world this would run for 7 days. For the demo, it simulates
7 days of campaign performance compressed into a few seconds.
Reads .state/<run_id>/execution.json + plan.json. Writes monitor.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import structlog
import yaml

from agents.tools import mocks as mock_tools

log = structlog.get_logger()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _deterministic_roas_series(run_id: str, simulate_days: int) -> list[float]:
    """
    Generate a deterministic ROAS series based on run_id.

    For the demo seed (r-demo-1, r-final, etc.), produce a healthy series.
    For run_ids starting with 'r-bad', drop below threshold mid-week.
    """
    if run_id.startswith("r-bad") or run_id.startswith("test-bad"):
        return [1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8][:simulate_days]
    # Healthy demo curve
    base = [1.8, 2.1, 2.5, 2.8, 2.9, 2.8, 2.7]
    return base[:simulate_days]


def run_monitor(
    run_id: str,
    simulate_days: int = 7,
    compressed_seconds: float = 1.0,
) -> dict:
    """
    Simulate post-execution monitoring of the launched campaign.

    Returns a dict and also writes .state/<run_id>/monitor.json.
    """
    workspace = _workspace_root()
    state_dir = workspace / ".state" / run_id

    plan_path = state_dir / "plan.json"
    execution_path = state_dir / "execution.json"
    if not plan_path.exists() or not execution_path.exists():
        raise FileNotFoundError(
            f"Monitor needs plan.json + execution.json in {state_dir}"
        )

    with open(plan_path, "r", encoding="utf-8") as fh:
        plan_data = json.load(fh)
    with open(execution_path, "r", encoding="utf-8") as fh:
        execution_data = json.load(fh)

    # Load ROAS threshold from policies
    policies_path = workspace / "config" / "policies.yaml"
    with open(policies_path, "r", encoding="utf-8") as fh:
        policies = yaml.safe_load(fh)
    roas_threshold = float(policies["monitor"]["roas_threshold"])

    # Find the campaign action (A3)
    campaign_action = next(
        (a for a in plan_data.get("actions", []) if a.get("action_id") == "A3"),
        None,
    )
    if campaign_action is None:
        result = {
            "run_id": run_id,
            "campaign_action_id": None,
            "simulated_days": 0,
            "roas_daily": [],
            "auto_paused": False,
            "pause_day": None,
            "status": "no_campaign_to_monitor",
        }
        _write_monitor(state_dir, result)
        return result

    series = _deterministic_roas_series(run_id, simulate_days)

    # Compressed simulation — sleep a tiny bit per "day" so it feels live
    per_day_sleep = compressed_seconds / max(simulate_days, 1)
    auto_paused = False
    pause_day: int | None = None

    log.info(
        "Monitor: starting 7-day simulated watch",
        agent="monitor",
        phase="start",
        kind="watch_start",
        payload={"run_id": run_id, "simulate_days": simulate_days},
        level="info",
    )

    for day_idx, roas in enumerate(series, start=1):
        time.sleep(per_day_sleep)
        log.info(
            f"Monitor day {day_idx}: ROAS={roas}",
            agent="monitor",
            phase="tick",
            kind="day",
            payload={"day": day_idx, "roas": roas},
            level="info",
        )
        if roas < roas_threshold and not auto_paused:
            auto_paused = True
            pause_day = day_idx
            # invoke the compensating action
            campaign_id = "camp-mocked"  # would come from execution.json tool_calls
            mock_tools.mock_pause_campaign(campaign_id=campaign_id)
            log.warning(
                f"Monitor: ROAS {roas} below threshold {roas_threshold}, "
                f"auto-paused on day {day_idx}",
                agent="monitor",
                phase="tick",
                kind="auto_pause",
                payload={"day": day_idx, "roas": roas, "threshold": roas_threshold},
                level="warning",
            )

    final_status = "auto_paused" if auto_paused else "healthy"

    result = {
        "run_id": run_id,
        "campaign_action_id": "A3",
        "simulated_days": len(series),
        "roas_daily": series,
        "roas_threshold": roas_threshold,
        "auto_paused": auto_paused,
        "pause_day": pause_day,
        "status": final_status,
    }
    _write_monitor(state_dir, result)

    log.info(
        "Monitor: complete",
        agent="monitor",
        phase="done",
        kind="result",
        payload={"run_id": run_id, "status": final_status},
        level="info",
    )
    return result


def _write_monitor(state_dir: Path, result: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "monitor.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
