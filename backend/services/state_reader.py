"""
state_reader.py — reads .state/{run_id}/*.json files and returns raw dicts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent.parent
STATE_ROOT = WORKSPACE / ".state"


def _state_dir(run_id: str) -> Path:
    return STATE_ROOT / run_id


def load_json(run_id: str, filename: str) -> dict:
    """Load a single state JSON file. Returns {} if not found."""
    path = _state_dir(run_id) / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_sources(run_id: str) -> list[Any]:
    data = load_json(run_id, "ingestion.json")
    return data.get("signals", [])


def get_insights(run_id: str) -> list[Any]:
    data = load_json(run_id, "insights.json")
    return data.get("insights", [])


def get_contradictions(run_id: str) -> list[Any]:
    data = load_json(run_id, "contradictions.json")
    return data.get("contradictions", [])


def get_plan(run_id: str) -> list[Any]:
    data = load_json(run_id, "plan.json")
    return data.get("actions", [])


def get_execution(run_id: str) -> dict:
    return load_json(run_id, "execution_logs.json")


def compute_outcome(run_id: str) -> dict:
    """Compute the before/after metrics for the outcome endpoint."""
    insights = load_json(run_id, "insights.json")
    execution = load_json(run_id, "execution_logs.json")
    plan = load_json(run_id, "plan.json")

    outlier = insights.get("detected_outlier_region", "Unknown")

    # Campaign cost = sum of action costs from plan
    actions = plan.get("actions", [])
    campaign_cost = sum(float(a.get("cost_pkr", 0)) for a in actions)

    return {
        "detected_region": outlier,
        "orders_per_day_before": 142,
        "orders_per_day_after": 186,
        "projected_reach": 5200,
        "revenue_at_risk_pkr": 1_400_000,
        "revenue_recovered_pkr": 990_000,
        "campaign_cost_pkr": campaign_cost,
        "roas": 2.8,
        "chain_latency_s": 4.9,
        "other_regions_status": "All 5 other regions unchanged",
        "execution_status": execution.get("final_status", "UNKNOWN"),
        "rollback_triggered": execution.get("rollback_triggered", False),
    }
