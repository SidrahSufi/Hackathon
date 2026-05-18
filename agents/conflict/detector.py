"""
Pure-Python pair detection for the ConflictResolver Agent.

Rule-based detection of source pairs that potentially disagree on the same
metric.  This can be generalised to an LLM-driven approach later.
"""
from __future__ import annotations

from pathlib import Path

import structlog

from agents.ingestion.schemas import Signal

log = structlog.get_logger()


def _filename(signal: Signal) -> str:
    """Lowercase filename from the signal's source_path."""
    return Path(signal.source_path).name.lower()


def find_metric_pairs(
    signals: list[Signal],
) -> list[tuple[Signal, Signal, str]]:
    """
    Return (signal_a, signal_b, metric_name) tuples for known conflict patterns.

    Operates on ALL signals (including discarded) so that contradictions
    involving discarded sources can be surfaced for human review.

    MVP detects three patterns:
    1. PDF report vs POS CSV on regional growth  → growth_pct_{outlier_region}
    2. Marketing spend vs analytics reach         → campaign_health_{region}
    3. Credible news vs anonymous blog on pricing → competitor_pricing_claim

    This can be generalised to arbitrary metric matching later.
    """
    pairs: list[tuple[Signal, Signal, str]] = []

    # Build lookup helpers
    by_type: dict[str, list[Signal]] = {}
    for s in signals:
        by_type.setdefault(s.source_type, []).append(s)

    pdf_signals = by_type.get("pdf", [])
    csv_signals = [s for s in by_type.get("csv", []) if "pos_ecom" in _filename(s)]
    html_signals = by_type.get("html", [])
    json_signals = by_type.get("json", [])

    # --- Pattern 1: PDF vs POS CSV on growth ---
    for pdf in pdf_signals:
        for csv in csv_signals:
            # Derive region from the insight context — use directory name
            region = Path(pdf.source_path).parent.name.title()
            metric = f"growth_pct_{region.lower()}"
            pairs.append((pdf, csv, metric))

    # --- Pattern 2: Marketing spend vs analytics reach ---
    marketing = [s for s in json_signals if "marketing" in _filename(s)]
    analytics = [s for s in json_signals if "analytics" in _filename(s)]
    for mkt in marketing:
        for ana in analytics:
            region = Path(mkt.source_path).parent.name.title()
            metric = f"campaign_health_{region.lower()}"
            pairs.append((mkt, ana, metric))

    # --- Pattern 3: Credible news vs anonymous blog on pricing ---
    news_credible = [s for s in html_signals if "news_competitor" in _filename(s)]
    news_blog = [s for s in html_signals if "news_pricing_blog" in _filename(s)]
    for nc in news_credible:
        for nb in news_blog:
            pairs.append((nc, nb, "competitor_pricing_claim"))

    log.info(
        "Metric pairs detected",
        agent="conflict",
        phase="detect",
        kind="pairs",
        payload={"count": len(pairs)},
        level="info",
    )
    return pairs


def classify_pair(metric: str, sig_a: Signal, sig_b: Signal) -> str:
    """
    Classify a detected pair as one of:
    - "direct_conflict"   : sources report the SAME thing differently
    - "different_angle"   : both facts are true but viewed from different angles
    - "unrelated"         : false positive, skip

    Rules:
    - growth_pct_*            → direct_conflict (PDF and POS report growth differently)
    - campaign_health_*       → different_angle  (full budget AND -40% reach are both true)
    - competitor_pricing_claim → direct_conflict  (contradictory pricing claims)
    """
    if metric.startswith("growth_pct_"):
        return "direct_conflict"

    if metric.startswith("campaign_health_"):
        return "different_angle"

    if metric == "competitor_pricing_claim":
        return "direct_conflict"

    return "unrelated"
