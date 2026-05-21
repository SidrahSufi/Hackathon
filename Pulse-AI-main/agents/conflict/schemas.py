"""
Pydantic v2 schemas for the ConflictResolver Agent.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Status = Literal["resolved", "needs_human_review", "not_a_conflict"]


class Contradiction(BaseModel):
    """A detected contradiction between two sources on the same metric."""

    conflict_id: str = Field(..., description="e.g. 'c1'")
    metric: str = Field(..., description="What they disagree about, e.g. 'growth_pct_lahore'")
    region: str | None = None
    source_a: str = Field(..., description="src_id from ingestion")
    source_b: str = Field(..., description="src_id from ingestion")
    value_a: str = Field(..., description="Textual representation, e.g. '+5% YoY'")
    value_b: str = Field(..., description="Textual representation, e.g. '-25% over 30 days'")
    status: Status
    chosen_source: str | None = Field(
        default=None,
        description="src_id of the winner, None if needs_human_review",
    )
    rationale: str = Field(..., description="1-2 sentence explanation")
    confidence: float = Field(..., ge=0.0, le=1.0)


class ConflictResult(BaseModel):
    """Aggregated output of the ConflictResolver Agent for a single run."""

    run_id: str
    contradictions: list[Contradiction] = Field(
        default_factory=list,
        description="Only status in {resolved, needs_human_review}",
    )
    not_a_conflict_log: list[dict] = Field(
        default_factory=list,
        description="Pairs classified as not_a_conflict, with reason",
    )
