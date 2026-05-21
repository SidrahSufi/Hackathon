"""
Tests for the temporal analysis module.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from agents.insight.temporal import compare_windows, detect_outlier_regions


WORKSPACE = Path(__file__).resolve().parent.parent
LAHORE_CSV = WORKSPACE / "sources" / "zarapk_regional_v1" / "lahore" / "pos_ecom_last_30d.csv"
KARACHI_CSV = WORKSPACE / "sources" / "zarapk_regional_v1" / "karachi" / "pos_ecom_last_30d.csv"


@pytest.fixture(autouse=True, scope="module")
def ensure_mock_data():
    """Regenerate mock data for both seeds if missing."""
    for seed in ("lahore", "karachi"):
        seed_dir = WORKSPACE / "sources" / "zarapk_regional_v1" / seed
        if not seed_dir.exists() or not any(seed_dir.iterdir()):
            subprocess.run(
                [sys.executable, "-m", "agents.gen_mock_data", "--seed", seed],
                cwd=str(WORKSPACE),
                check=True,
            )


def test_lahore_outlier_detected():
    """compare_windows + detect_outlier_regions returns ['Lahore'] for lahore seed."""
    df = pd.read_csv(LAHORE_CSV)
    window_df = compare_windows(df, "orders", "region", "date")
    outliers = detect_outlier_regions(window_df)
    assert "Lahore" in outliers, f"Expected 'Lahore' in outliers, got {outliers}"


def test_karachi_outlier_detected():
    """compare_windows + detect_outlier_regions returns ['Karachi'] for karachi seed."""
    df = pd.read_csv(KARACHI_CSV)
    window_df = compare_windows(df, "orders", "region", "date")
    outliers = detect_outlier_regions(window_df)
    assert "Karachi" in outliers, f"Expected 'Karachi' in outliers, got {outliers}"


def test_flat_data_no_outlier():
    """Synthetic flat data produces no outliers."""
    rows = []
    for day in range(30):
        date_str = f"2026-05-{day + 1:02d}"
        for region in ["RegionA", "RegionB", "RegionC"]:
            rows.append({
                "date": date_str,
                "region": region,
                "orders": 100,
            })

    df = pd.DataFrame(rows)
    window_df = compare_windows(df, "orders", "region", "date")
    outliers = detect_outlier_regions(window_df)
    assert outliers == [], f"Expected no outliers, got {outliers}"
