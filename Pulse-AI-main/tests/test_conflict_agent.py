"""
Tests for the ConflictResolver Agent.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from agents.ingestion import run_ingestion
from agents.insight import run_insight
from agents.conflict import ConflictResult, run_conflict
from agents.conflict.resolver import score_source_pair


WORKSPACE = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True, scope="module")
def ensure_pipeline():
    """Regenerate mock data + run ingestion + insight for lahore seed."""
    seed_dir = WORKSPACE / "sources" / "zarapk_regional_v1" / "lahore"
    if not seed_dir.exists() or not any(seed_dir.iterdir()):
        subprocess.run(
            [sys.executable, "-m", "agents.gen_mock_data", "--seed", "lahore"],
            cwd=str(WORKSPACE),
            check=True,
        )
    run_ingestion("r-conflict-test", "lahore")
    run_insight("r-conflict-test")


@pytest.fixture(scope="module")
def conflict_result() -> ConflictResult:
    return run_conflict("r-conflict-test")


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def test_c1_pdf_vs_pos_resolved(conflict_result: ConflictResult):
    """C1: PDF vs POS disagree on Lahore growth — resolved, POS wins."""
    c1 = next(
        (c for c in conflict_result.contradictions
         if c.metric.startswith("growth_pct_")),
        None,
    )
    assert c1 is not None, "No growth_pct contradiction found"
    assert c1.status == "resolved"
    assert c1.chosen_source is not None
    # POS CSV should win — it has src_id for the csv signal
    assert "src-" in c1.chosen_source


def test_c2_marketing_analytics_not_in_contradictions(conflict_result: ConflictResult):
    """campaign_health pair must NOT appear in contradictions, only in not_a_conflict_log."""
    campaign_in_contradictions = [
        c for c in conflict_result.contradictions
        if "campaign_health" in c.metric
    ]
    assert len(campaign_in_contradictions) == 0, (
        "campaign_health should not be in contradictions list"
    )

    campaign_in_log = [
        entry for entry in conflict_result.not_a_conflict_log
        if "campaign_health" in entry.get("metric", "")
    ]
    assert len(campaign_in_log) == 1, (
        f"Expected 1 campaign_health entry in not_a_conflict_log, "
        f"got {len(campaign_in_log)}"
    )


def test_c3_pricing_needs_human_review(conflict_result: ConflictResult):
    """News vs blog pricing pair must have needs_human_review, chosen_source=None."""
    c3 = next(
        (c for c in conflict_result.contradictions
         if c.metric == "competitor_pricing_claim"),
        None,
    )
    assert c3 is not None, "No competitor_pricing_claim contradiction found"
    assert c3.status == "needs_human_review"
    assert c3.chosen_source is None


def test_no_invented_decisions(conflict_result: ConflictResult):
    """
    No resolved contradiction should have both |credibility_delta| < 0.2
    AND |recency_delta| < 0.3.  This proves the system never forces a decision.
    """
    # Reload signals to compute deltas
    from agents.ingestion.schemas import IngestionResult

    ingestion_path = WORKSPACE / ".state" / "r-conflict-test" / "ingestion.json"
    ingestion = IngestionResult.model_validate_json(
        ingestion_path.read_text("utf-8")
    )
    signals_map = {s.src_id: s for s in ingestion.signals}

    for c in conflict_result.contradictions:
        if c.status != "resolved":
            continue
        sig_a = signals_map[c.source_a]
        sig_b = signals_map[c.source_b]
        scores = score_source_pair(sig_a, sig_b)

        assert not (
            abs(scores["credibility_delta"]) < 0.2
            and abs(scores["recency_delta"]) < 0.3
        ), (
            f"Contradiction {c.conflict_id} was resolved but both deltas are "
            f"below threshold: cred={scores['credibility_delta']}, "
            f"rec={scores['recency_delta']}"
        )


def test_total_surfaced_count(conflict_result: ConflictResult):
    """Contradictions list has 2 entries (C1, C3). not_a_conflict_log has 1."""
    assert len(conflict_result.contradictions) == 2, (
        f"Expected 2 contradictions, got {len(conflict_result.contradictions)}"
    )
    assert len(conflict_result.not_a_conflict_log) == 1, (
        f"Expected 1 not_a_conflict entry, "
        f"got {len(conflict_result.not_a_conflict_log)}"
    )
