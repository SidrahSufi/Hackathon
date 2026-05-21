"""Tests for the Executor Agent."""
from __future__ import annotations

import pytest

from agents.conflict.agent import run_conflict
from agents.executor.agent import run_executor
from agents.ingestion.agent import run_ingestion
from agents.insight.agent import run_insight
from agents.planner.agent import run_planner
from agents.tools import mocks as mock_tools


@pytest.fixture(scope="module")
def lahore_run_id() -> str:
    rid = "test-executor-lahore"
    run_ingestion(rid, "lahore")
    run_insight(rid)
    run_conflict(rid)
    run_planner(rid)
    return rid


def test_executor_runs_all_five_steps(lahore_run_id):
    result = run_executor(lahore_run_id)
    assert len(result.steps) == 5
    assert [s.action_id for s in result.steps] == ["A1", "A2", "A3", "A4", "A5"]


def test_executor_overall_status_completed(lahore_run_id):
    result = run_executor(lahore_run_id)
    assert result.overall_status == "completed"


def test_executor_a4_notification_recovers(lahore_run_id):
    """A4 has an injected notification failure; the executor must recover."""
    result = run_executor(lahore_run_id)
    a4 = next(s for s in result.steps if s.action_id == "A4")
    assert a4.status == "failed_then_recovered"
    assert a4.attempts >= 2
    # Verify the recovery path actually called the notification tool more than once
    notif_calls = [tc for tc in a4.tool_calls if tc.tool == "mock_draft_notification"]
    assert len(notif_calls) >= 2


def test_executor_cumulative_cost_matches_plan(lahore_run_id):
    result = run_executor(lahore_run_id)
    # A3 is the only paid action and costs 720k
    assert result.cumulative_cost_pkr == 720000.0


def test_executor_records_latency():
    rid = "test-executor-latency"
    run_ingestion(rid, "lahore")
    run_insight(rid)
    run_conflict(rid)
    run_planner(rid)
    result = run_executor(rid)
    assert result.total_latency_s > 0
