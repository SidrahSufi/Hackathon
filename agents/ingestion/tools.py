"""
Pure-Python parser and scoring tools for the Ingestion Agent.

All math / scoring logic lives here — never inside LLM prompts.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import structlog
from pypdf import PdfReader

log = structlog.get_logger()

# Same fixed reference date used by the mock-data generator.
REFERENCE_TODAY = datetime(2026, 5, 17, tzinfo=timezone.utc)

KNOWN_OUTLETS = {"reuters", "bloomberg", "dawn", "tribune", "geo"}

SPAM_PHRASES = {"act now", "dm me", "limited time"}


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_pdf(path: str) -> dict:
    """Extract text and metadata from a PDF file."""
    reader = PdfReader(path)
    pages_text: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    creation_date: str | None = None
    if reader.metadata and reader.metadata.creation_date:
        creation_date = reader.metadata.creation_date.isoformat()

    return {
        "text": "\n".join(pages_text),
        "page_count": len(reader.pages),
        "creation_date": creation_date,
    }


def parse_csv(path: str) -> dict:
    """Read a CSV into summary statistics."""
    df = pd.read_csv(path)
    head = df.head(5).to_dict(orient="records")

    summary_stats: dict[str, dict] = {}
    for col in df.select_dtypes(include="number").columns:
        summary_stats[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": round(float(df[col].mean()), 2),
        }

    return {
        "row_count": len(df),
        "columns": list(df.columns),
        "head": head,
        "summary_stats": summary_stats,
    }


def parse_html(path: str) -> dict:
    """Extract title, body text, byline, and date string from an HTML file."""
    from bs4 import BeautifulSoup

    with open(path, "r", encoding="utf-8") as fh:
        soup = BeautifulSoup(fh, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    body_text = soup.get_text(separator=" ", strip=True)

    # Attempt to find a byline — look for "By <name>" pattern
    byline: str | None = None
    byline_match = re.search(r"\bBy\s+([A-Z][\w\s]+?)(?:\s*\|)", body_text)
    if byline_match:
        byline = byline_match.group(1).strip()

    # Attempt to find a date string — look for common date formats
    date_str: str | None = None
    date_match = re.search(
        r"(\w+ \d{1,2}, \d{4})", body_text
    )
    if date_match:
        date_str = date_match.group(1)

    return {
        "title": title,
        "text": body_text,
        "byline": byline,
        "date_str": date_str,
    }


def parse_json(path: str) -> dict:
    """Read a JSON file and wrap its contents."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {"data": data}


def parse_jsonl(path: str) -> dict:
    """Read a JSONL file (one JSON object per line)."""
    records: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return {"records": records, "record_count": len(records)}


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _emoji_count(text: str) -> int:
    """Count characters classified as emoji / symbols."""
    return sum(
        1 for ch in text
        if unicodedata.category(ch) in ("So", "Sk")
    )


def _caps_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are uppercase."""
    alpha = [ch for ch in text if ch.isalpha()]
    if not alpha:
        return 0.0
    return sum(1 for ch in alpha if ch.isupper()) / len(alpha)


def score_credibility(source_type: str, metadata: dict) -> float:
    """
    Heuristic credibility score ∈ [0.0, 1.0].

    Base scores by source pattern, then adjustments for outlet recognition
    and spam markers.
    """
    filename = metadata.get("filename", "").lower()
    text = metadata.get("text", "")
    byline = metadata.get("byline", "") or ""

    # --- base score ---
    if source_type == "pdf":
        base = 0.85
    elif source_type == "csv" and "pos_ecom" in filename:
        base = 0.95
    elif source_type == "json" and "analytics" in filename:
        base = 0.90
    elif source_type == "json" and "marketing" in filename:
        base = 0.85
    elif source_type == "jsonl":
        base = 0.60
    elif source_type == "html" and byline:
        base = 0.70
    elif source_type == "html" and not byline:
        base = 0.30
    elif source_type == "json" and "social" in filename:
        base = 0.20
    else:
        base = 0.50

    # --- adjustments ---
    # Boost for recognised outlet
    byline_lower = byline.lower()
    if any(outlet in byline_lower for outlet in KNOWN_OUTLETS):
        base += 0.10

    # Penalty for spam markers
    if is_spam(text):
        base -= 0.30

    return max(0.0, min(1.0, round(base, 2)))


def score_recency(timestamp: datetime) -> float:
    """
    Linear decay from 1.0 (today) to 0.0 over 90 days.

    Uses REFERENCE_TODAY for determinism.
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    age_days = (REFERENCE_TODAY - timestamp).total_seconds() / 86400
    if age_days <= 0:
        return 1.0
    if age_days >= 90:
        return 0.0
    return round(1.0 - age_days / 90.0, 4)


def is_spam(text: str) -> bool:
    """
    Return True if text exhibits spam markers:
    - contains known spam phrases
    - excessive uppercase (>60 % of alpha chars)
    - emoji count > 5
    """
    lower = text.lower()
    for phrase in SPAM_PHRASES:
        if phrase in lower:
            return True

    if _caps_ratio(text) > 0.60 and len(text) > 20:
        return True

    if _emoji_count(text) > 5:
        return True

    return False
