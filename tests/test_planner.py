"""Tests for the Action Planner Agent."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.conflict.agent import run_conflict
from agents.ingestion.agent import run_ingestion
from agents.insight.agent import run_insight
from agents.planner.agent import run_planner


@pytest.fixture(scope="module")
def lahore_run_id() -> str:
    rid = "test-planner-lahore"
    run_ingestion(rid, "lahore")
    run_insight(rid)
    run_conflict(rid)
    return rid


def test_planner_produces_five_actions(lahore_run_id):
    plan = run_planner(lahore_run_id)
    assert len(plan.actions) == 5
    assert [a.action_id for a in plan.actions] == ["A1", "A2", "A3", "A4", "A5"]


def test_planner_targets_detected_region(lahore_run_id):
    plan = run_planner(lahore_run_id)
    assert plan.detected_region == "Lahore"
    # A3 must target the detected region
    a3 = next(a for a in plan.actions if a.action_id == "A3")
    assert a3.tool_args["region"] == "Lahore"


def test_planner_revises_discount_to_policy_cap(lahore_run_id):
    plan = run_planner(lahore_run_id)
    a3 = next(a for a in plan.actions if a.action_id == "A3")
    assert a3.discount_pct == 20.0   # capped from initial 25.0
    assert any(
        r["action_id"] == "A3" and r["field"] == "discount_pct"
        for r in plan.revisions_applied
    )


def test_planner_total_cost_under_budget_cap(lahore_run_id):
    plan = run_planner(lahore_run_id)
    assert plan.total_cost_pkr <= 800000.0


def test_planner_no_outlier_returns_empty_plan(tmp_path, monkeypatch):
    """When detected_outlier_region is None, planner must produce empty plan."""
    rid = "test-planner-noop"
    workspace = Path(__file__).resolve().parent.parent
    state_dir = workspace / ".state" / rid
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "insights.json").write_text(json.dumps({
        "run_id": rid,
        "seed_region": "lahore",
        "detected_outlier_region": None,
        "insights": [],
    }))
    (state_dir / "contradictions.json").write_text(json.dumps({
        "run_id": rid,
        "contradictions": [],
        "not_a_conflict_log": [],
    }))
    plan = run_planner(rid)
    assert plan.actions == []
    assert plan.feasible is False
