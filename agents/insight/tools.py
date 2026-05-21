"""
Tools for the Insight Agent.

Thin wrappers around temporal analysis functions and a regex-based
entity extractor for HTML news articles.
"""
from __future__ import annotations

import re
from pathlib import Path

import structlog
from bs4 import BeautifulSoup

log = structlog.get_logger()

# Re-export temporal functions so the ADK agent can register them as tools.
from agents.insight.temporal import (  # noqa: F401, E402
    cluster_complaint_segment,
    compare_windows,
    correlate_in_time,
    detect_outlier_regions,
)

# Known region names for extraction
_REGIONS = {
    "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", "multan",
}


def extract_entities_from_html(html_path: str) -> dict:
    """
    Read a news HTML file and extract structured entities via regex/keywords.

    Returns
    -------
    {
        "competitor_name": str | None,
        "regions": list[str],
        "expansion_date": str | None,
    }
    """
    path = Path(html_path)
    with open(path, "r", encoding="utf-8") as fh:
        soup = BeautifulSoup(fh, "html.parser")

    text = soup.get_text(separator=" ", strip=True)

    # --- competitor name ---
    # Pattern: look for a capitalised brand name near "opens" / "expansion"
    competitor_name: str | None = None
    brand_match = re.search(r"([A-Z][a-zA-Z]+PK)\b", text)
    if brand_match:
        competitor_name = brand_match.group(1)

    # --- regions mentioned ---
    text_lower = text.lower()
    regions = sorted(r.title() for r in _REGIONS if r in text_lower)

    # --- expansion date ---
    expansion_date: str | None = None
    date_match = re.search(r"(\d{4}-\d{2})", text)
    if date_match:
        expansion_date = date_match.group(1)

    result = {
        "competitor_name": competitor_name,
        "regions": regions,
        "expansion_date": expansion_date,
    }

    log.info(
        "Entity extraction complete",
        agent="insight",
        phase="extract",
        kind="html_entities",
        payload=result,
        level="info",
    )
    return result
