"""
Pydantic v2 schemas for the Ingestion Agent.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["pdf", "csv", "html", "json", "jsonl", "feed"]


class Signal(BaseModel):
    """A single normalised record produced by the Ingestion Agent."""

    src_id: str = Field(..., description="e.g. 'src-1'")
    source_type: SourceType
    source_path: str
    title: str
    timestamp: datetime = Field(..., description="When the content was produced")
    ingested_at: datetime
    credibility: float = Field(..., ge=0.0, le=1.0)
    recency: float = Field(..., ge=0.0, le=1.0, description="1.0 = today")
    region: str | None = None
    metric: str | None = None
    content: dict = Field(default_factory=dict, description="Normalised payload")
    discarded: bool = False
    discard_reason: str | None = None


class IngestionResult(BaseModel):
    """Aggregated output of the Ingestion Agent for a single run."""

    run_id: str
    seed_region: str
    signals: list[Signal]
    sources_processed: int
    sources_discarded: int
    discarded_summary: list[dict] = Field(
        default_factory=list,
        description="[{src_id, reason, details}]",
    )
