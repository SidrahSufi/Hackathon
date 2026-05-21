"""
Outcome computation — final stage of the PulseAI pipeline.

Reads all state files and produces the before/after metrics consumed by the
mobile app's Outcome screen. The projection uses observed POS data so the
numbers are grounded, not hand-waved.

Writes .state/<run_id>/outcome.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import structlog

log = structlog.get_logger()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _last_n_days_avg_orders(pos_csv_path: Path, region: str, n: int = 14) -> float:
    """Average daily orders for region over the last n days."""
    df = pd.read_csv(pos_csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["region"] == region]
    if df.empty:
        return 0.0
    cutoff = df["date"].max() - pd.Timedelta(days=n)
    recent = df[df["date"] > cutoff]
    by_day = recent.groupby("date")["orders"].sum()
    if by_day.empty:
        return 0.0
    return float(by_day.mean())


def _projected_revenue_uplift_pkr(
    pos_csv_path: Path,
    region: str,
    discount_pct: float,
    projection_days: int = 30,
) -> tuple[float, float]:
    """
    Project the 30-day revenue recovery for the region if a campaign with the
    given discount runs.

    Simple linear elasticity model: uplift_pct = min(discount_pct * 1.5, 35).
    Returns (revenue_at_risk_pkr, revenue_recovery_pkr).
    """
    df = pd.read_csv(pos_csv_path)
    df["date"] = pd.to_datetime(df["date"])
    region_df = df[df["region"] == region]
    if region_df.empty:
        return 0.0, 0.0

    end = region_df["date"].max()
    last_15 = region_df[region_df["date"] > end - pd.Timedelta(days=15)]
    prior_15 = region_df[
        (region_df["date"] > end - pd.Timedelta(days=30))
        & (region_df["date"] <= end - pd.Timedelta(days=15))
    ]
    if last_15.empty or prior_15.empty:
        return 0.0, 0.0

    last_rev = float(last_15["revenue_pkr"].sum())
    prior_rev = float(prior_15["revenue_pkr"].sum())
    decline_factor = (prior_rev - last_rev) / max(prior_rev, 1.0)
    if decline_factor < 0:
        decline_factor = 0.0

    # Revenue at risk over 30 days at the current decline pace
    revenue_at_risk = decline_factor * prior_rev * (projection_days / 15.0)

    # Uplift model
    uplift_pct = min(discount_pct * 1.5, 35.0) / 100.0
    revenue_recovery = uplift_pct * prior_rev * (projection_days / 15.0)

    return revenue_at_risk, revenue_recovery


def compute_outcome(run_id: str) -> dict:
    """
    Build the outcome.json payload for the run.
    """
    workspace = _workspace_root()
    state_dir = workspace / ".state" / run_id

    # Load all upstream artifacts
    def _load(name: str) -> dict | None:
        path = state_dir / name
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    insights = _load("insights.json")
    contradictions = _load("contradictions.json")
    plan = _load("plan.json")
    execution = _load("execution.json")

    if insights is None or plan is None or execution is None:
        raise FileNotFoundError(
            "outcome requires insights.json, plan.json, and execution.json"
        )

    detected_region = insights.get("detected_outlier_region")
    if detected_region is None:
        result = {
            "run_id": run_id,
            "detected_region": None,
            "status": "no_action",
            "notes": ["No outlier region detected — pipeline produced no outcome."],
        }
        _write_outcome(state_dir, result)
        return result

    # Find the campaign action for cost + reach
    campaign_action = next(
        (a for a in plan.get("actions", []) if a.get("action_id") == "A3"),
        {},
    )
    discount_pct = float(campaign_action.get("discount_pct") or 0)
    projected_reach = int(campaign_action.get("projected_reach") or 5200)
    campaign_cost = float(execution.get("cumulative_cost_pkr") or 0)

    # Source CSV for projection
    seed_region = insights.get("seed_region", "lahore")
    pos_csv_path = (
        workspace / "sources" / "zarapk_regional_v1" / seed_region
        / "pos_ecom_last_30d.csv"
    )

    before_orders_per_day = _last_n_days_avg_orders(
        pos_csv_path, detected_region, n=14
    )
    revenue_at_risk, revenue_recovery = _projected_revenue_uplift_pkr(
        pos_csv_path, detected_region, discount_pct
    )

    uplift_pct = min(discount_pct * 1.5, 35.0) / 100.0
    after_orders_projected = before_orders_per_day * (1.0 + uplift_pct)

    projected_roas = (
        revenue_recovery / campaign_cost if campaign_cost > 0 else 0.0
    )

    # Build the notes — be honest about what happened during the run
    notes: list[str] = []
    nhr_count = sum(
        1 for c in (contradictions or {}).get("contradictions", [])
        if c.get("status") == "needs_human_review"
    )
    if nhr_count:
        notes.append(
            f"{nhr_count} unresolved contradiction(s) flagged for human review."
        )
    recovered_steps = sum(
        1 for s in execution.get("steps", [])
        if s.get("status") == "failed_then_recovered"
    )
    if recovered_steps:
        notes.append(
            f"{recovered_steps} step(s) failed and recovered automatically."
        )

    overall_status = execution.get("overall_status", "completed")

    result = {
        "run_id": run_id,
        "detected_region": detected_region,
        "before": {
            "orders_per_day_14d_avg": round(before_orders_per_day, 1),
            "revenue_at_risk_30d_pkr": round(revenue_at_risk, 0),
        },
        "after": {
            "orders_per_day_projected_7d": round(after_orders_projected, 1),
            "revenue_recovery_projected_pkr": round(revenue_recovery, 0),
            "projected_reach": projected_reach,
        },
        "campaign_cost_pkr": campaign_cost,
        "applied_discount_pct": discount_pct,
        "projected_roas": round(projected_roas, 2),
        "chain_latency_s": float(execution.get("total_latency_s") or 0.0),
        "overall_status": overall_status,
        "other_regions_status": "unchanged",
        "notes": notes,
    }

    _write_outcome(state_dir, result)

    log.info(
        "Outcome: complete",
        agent="outcome",
        phase="done",
        kind="result",
        payload={
            "run_id": run_id,
            "detected_region": detected_region,
            "projected_roas": result["projected_roas"],
            "projected_reach": projected_reach,
        },
        level="info",
    )
    return result


def _write_outcome(state_dir: Path, result: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "outcome.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
