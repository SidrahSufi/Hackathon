"""End-to-end pipeline tests covering all 6 stages."""
from __future__ import annotations

from pathlib import Path

import pytest

from agents.run_pipeline import run_pipeline


def _state_dir(run_id: str) -> Path:
    return Path(__file__).resolve().parent.parent / ".state" / run_id


def _all_artifacts_exist(run_id: str) -> bool:
    sd = _state_dir(run_id)
    return all((sd / name).exists() for name in (
        "ingestion.json", "insights.json", "contradictions.json",
        "plan.json", "execution.json", "monitor.json", "outcome.json",
    ))


def test_lahore_full_pipeline():
    summary = run_pipeline("test-full-lahore", "lahore")
    assert summary["detected_outlier_region"] == "Lahore"
    assert summary["insights_count"] == 5
    assert summary["plan_actions"] == 5
    assert summary["execution_status"] == "completed"
    assert _all_artifacts_exist("test-full-lahore")


def test_karachi_full_pipeline():
    summary = run_pipeline("test-full-karachi", "karachi")
    assert summary["detected_outlier_region"] == "Karachi"
    assert summary["insights_count"] == 5
    assert summary["plan_actions"] == 5
    assert summary["execution_status"] == "completed"
    assert _all_artifacts_exist("test-full-karachi")


def test_region_agnostic():
    """Same code; different seeds; different detected outlier."""
    l = run_pipeline("test-agn-lahore", "lahore")
    k = run_pipeline("test-agn-karachi", "karachi")
    assert l["detected_outlier_region"] != k["detected_outlier_region"]


def test_pipeline_produces_projected_reach_meeting_brief_target():
    """Brief example targets ≥5000 reach for the campaign."""
    summary = run_pipeline("test-reach-lahore", "lahore")
    reach = summary["outcome"]["after"]["projected_reach"]
    assert reach >= 5000, f"projected_reach {reach} < 5000"


def test_pipeline_surfaces_needs_human_review():
    """Property check — the competitor-pricing conflict should never be auto-resolved."""
    summary = run_pipeline("test-nhr-lahore", "lahore")
    assert summary["needs_human_review"] >= 1
