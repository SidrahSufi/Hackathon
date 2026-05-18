"""
Pydantic v2 schemas for the Insight Agent.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["info", "low", "medium", "high", "critical"]


class Insight(BaseModel):
    """A single ranked insight produced by the Insight Agent."""

    insight_id: str = Field(..., description="e.g. 'I1'")
    title: str = Field(..., description="Human-readable headline")
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    region: str | None = None
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="src_ids from ingestion that back this insight",
    )
    metrics: dict = Field(
        default_factory=dict,
        description="Computed numbers, e.g. {'orders_change_pct': -25.3}",
    )
    rationale: str = Field(
        ...,
        description="1-2 sentence human explanation",
    )


class InsightResult(BaseModel):
    """Aggregated output of the Insight Agent for a single run."""

    run_id: str
    seed_region: str
    detected_outlier_region: str | None = None
    insights: list[Insight]
