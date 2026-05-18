"""
Tests for the Ingestion Agent.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agents.ingestion import IngestionResult, run_ingestion


WORKSPACE = Path(__file__).resolve().parent.parent
LAHORE_DIR = WORKSPACE / "sources" / "zarapk_regional_v1" / "lahore"


@pytest.fixture(autouse=True, scope="module")
def ensure_mock_data():
    """Regenerate mock data for 'lahore' seed if missing."""
    if not LAHORE_DIR.exists() or not any(LAHORE_DIR.iterdir()):
        subprocess.run(
            [sys.executable, "-m", "agents.gen_mock_data", "--seed", "lahore"],
            cwd=str(WORKSPACE),
            check=True,
        )


@pytest.fixture(scope="module")
def ingestion_result() -> IngestionResult:
    """Run ingestion once for the module and cache the result."""
    return run_ingestion("r-test-1", "lahore")


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def test_happy_path(ingestion_result: IngestionResult):
    """8 signals total, 2 discarded (the two throw-in files)."""
    assert ingestion_result.sources_processed == 8
    assert ingestion_result.sources_discarded == 2
    assert len(ingestion_result.signals) == 8


def test_news_pricing_blog_discarded(ingestion_result: IngestionResult):
    """Anonymous blog HTML must be discarded for low credibility."""
    blog = next(
        (s for s in ingestion_result.signals if "news_pricing_blog" in s.source_path),
        None,
    )
    assert blog is not None, "news_pricing_blog signal not found"
    assert blog.discarded is True
    assert blog.discard_reason is not None
    assert "credibility" in blog.discard_reason.lower()


def test_social_spam_discarded(ingestion_result: IngestionResult):
    """Spam social post JSON must be discarded for spam."""
    spam = next(
        (s for s in ingestion_result.signals if "social_post_spam" in s.source_path),
        None,
    )
    assert spam is not None, "social_post_spam signal not found"
    assert spam.discarded is True
    assert spam.discard_reason is not None
    assert "spam" in spam.discard_reason.lower()


def test_pos_csv_high_credibility(ingestion_result: IngestionResult):
    """POS CSV signal must have credibility >= 0.9."""
    pos = next(
        (s for s in ingestion_result.signals if "pos_ecom" in s.source_path),
        None,
    )
    assert pos is not None, "pos_ecom_last_30d signal not found"
    assert pos.credibility >= 0.9


def test_news_competitor_high_credibility(ingestion_result: IngestionResult):
    """Named-outlet news article must have credibility >= 0.6."""
    news = next(
        (s for s in ingestion_result.signals
         if "news_competitor_expansion" in s.source_path),
        None,
    )
    assert news is not None, "news_competitor_expansion signal not found"
    assert news.credibility >= 0.6


def test_output_file_written(ingestion_result: IngestionResult):
    """After run_ingestion, .state/r-test-1/ingestion.json must exist and be valid JSON."""
    state_file = WORKSPACE / ".state" / "r-test-1" / "ingestion.json"
    assert state_file.exists(), f"Expected {state_file} to exist"

    with open(state_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert "run_id" in data
    assert data["run_id"] == "r-test-1"
    assert len(data["signals"]) == 8
