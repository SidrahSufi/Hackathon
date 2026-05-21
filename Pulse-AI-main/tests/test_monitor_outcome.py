"""Tests for the Monitor Agent and Outcome computation."""
from __future__ import annotations

import pytest

from agents.conflict.agent import run_conflict
from agents.executor.agent import run_executor
from agents.ingestion.agent import run_ingestion
from agents.insight.agent import run_insight
from agents.monitor.agent import run_monitor
from agents.outcome.compute import compute_outcome
from agents.planner.agent import run_planner


@pytest.fixture(scope="module")
def lahore_run_id() -> str:
    rid = "test-mo-lahore"
    run_ingestion(rid, "lahore")
    run_insight(rid)
    run_conflict(rid)
    run_planner(rid)
    run_executor(rid)
    return rid


def test_monitor_simulates_seven_days(lahore_run_id):
    m = run_monitor(lahore_run_id, compressed_seconds=0.1)
    assert m["simulated_days"] == 7
    assert len(m["roas_daily"]) == 7


def test_monitor_healthy_no_pause(lahore_run_id):
    m = run_monitor(lahore_run_id, compressed_seconds=0.1)
    assert m["auto_paused"] is False
    assert m["status"] == "healthy"


def test_monitor_bad_run_id_triggers_pause():
    """Run-id starting with r-bad triggers a declining ROAS series."""
    rid = "r-bad-monitor-1"
    run_ingestion(rid, "lahore")
    run_insight(rid)
    run_conflict(rid)
    run_planner(rid)
    run_executor(rid)
    m = run_monitor(rid, compressed_seconds=0.1)
    assert m["auto_paused"] is True
    assert m["status"] == "auto_paused"
    assert m["pause_day"] is not None


def test_outcome_has_required_fields(lahore_run_id):
    run_monitor(lahore_run_id, compressed_seconds=0.1)
    o = compute_outcome(lahore_run_id)
    for key in (
        "run_id", "detected_region", "before", "after",
        "campaign_cost_pkr", "projected_roas", "chain_latency_s",
    ):
        assert key in o, f"missing key: {key}"


def test_outcome_projected_reach_at_least_5000(lahore_run_id):
    o = compute_outcome(lahore_run_id)
    assert o["after"]["projected_reach"] >= 5000


def test_outcome_detected_region_matches(lahore_run_id):
    o = compute_outcome(lahore_run_id)
    assert o["detected_region"] == "Lahore"
