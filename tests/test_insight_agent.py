"""
Tests for the Insight Agent.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from agents.ingestion import run_ingestion
from agents.insight import InsightResult, run_insight
from agents.insight.temporal import compare_windows


WORKSPACE = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True, scope="module")
def ensure_mock_data_and_ingestion():
    """Regenerate mock data + run ingestion for both seeds."""
    for seed in ("lahore", "karachi"):
        seed_dir = WORKSPACE / "sources" / "zarapk_regional_v1" / seed
        if not seed_dir.exists() or not any(seed_dir.iterdir()):
            subprocess.run(
                [sys.executable, "-m", "agents.gen_mock_data", "--seed", seed],
                cwd=str(WORKSPACE),
                check=True,
            )

    # Run ingestion for both seeds (idempotent — overwrites state)
    run_ingestion("r-insight-lahore", "lahore")
    run_ingestion("r-insight-karachi", "karachi")


@pytest.fixture(scope="module")
def lahore_result() -> InsightResult:
    return run_insight("r-insight-lahore")


@pytest.fixture(scope="module")
def karachi_result() -> InsightResult:
    return run_insight("r-insight-karachi")


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def test_lahore_outlier(lahore_result: InsightResult):
    """Lahore run detects Lahore as the outlier region."""
    assert lahore_result.detected_outlier_region == "Lahore"


def test_karachi_outlier(karachi_result: InsightResult):
    """Karachi run detects Karachi as the outlier region."""
    assert karachi_result.detected_outlier_region == "Karachi"


def test_five_insights(lahore_result: InsightResult):
    """Lahore run produces exactly 5 insights with ids I1..I5."""
    ids = [i.insight_id for i in lahore_result.insights]
    assert ids == ["I1", "I2", "I3", "I4", "I5"], f"Got {ids}"


def test_evidence_refs_valid(lahore_result: InsightResult):
    """Every evidence_ref is a valid src_id from ingestion.json."""
    state_path = WORKSPACE / ".state" / "r-insight-lahore" / "ingestion.json"
    ingestion_data = json.loads(state_path.read_text("utf-8"))
    valid_src_ids = {s["src_id"] for s in ingestion_data["signals"]}

    for insight in lahore_result.insights:
        for ref in insight.evidence_refs:
            assert ref in valid_src_ids, (
                f"Insight {insight.insight_id} references {ref} which is not "
                f"in ingestion signals {valid_src_ids}"
            )


def test_no_invented_numbers(lahore_result: InsightResult):
    """
    I1.metrics['orders_change_pct'] must be within 1pp of what
    compare_windows returns directly.
    """
    # Recompute from raw CSV
    csv_path = WORKSPACE / "sources" / "zarapk_regional_v1" / "lahore" / "pos_ecom_last_30d.csv"
    df = pd.read_csv(csv_path)
    window_df = compare_windows(df, "orders", "region", "date")
    lahore_row = window_df.loc[window_df["region"] == "Lahore"].iloc[0]
    expected_pct = float(lahore_row["pct_change"])

    i1 = next(i for i in lahore_result.insights if i.insight_id == "I1")
    actual_pct = i1.metrics["orders_change_pct"]

    assert abs(actual_pct - expected_pct) <= 1.0, (
        f"I1 orders_change_pct ({actual_pct}) differs from compare_windows "
        f"({expected_pct}) by more than 1pp"
    )
