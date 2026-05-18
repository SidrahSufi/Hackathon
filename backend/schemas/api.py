"""
Pydantic v2 schemas for the BizPulse FastAPI backend.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    scenario_id: str = Field(..., description="e.g. 'zarapk_regional_v1'")
    seed_region: str = Field(..., description="'lahore' or 'karachi'")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class RunStartResponse(BaseModel):
    run_id: str
    status: str = "started"


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    current_phase: Optional[str] = None
    detected_region: Optional[str] = None
    seed_region: Optional[str] = None
    created_at: Optional[str] = None


class SourcesResponse(BaseModel):
    sources: List[Any]


class InsightsResponse(BaseModel):
    insights: List[Any]


class ContradictionsResponse(BaseModel):
    contradictions: List[Any]


class PlanResponse(BaseModel):
    actions: List[Any]


class ExecutionResponse(BaseModel):
    run_id: Optional[str] = None
    final_status: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    rollback_triggered: bool = False
    message: Optional[str] = None


class OutcomeResponse(BaseModel):
    detected_region: Optional[str] = None
    orders_per_day_before: int = 142
    orders_per_day_after: int = 186
    projected_reach: int = 5200
    revenue_at_risk_pkr: int = 1_400_000
    revenue_recovered_pkr: int = 990_000
    campaign_cost_pkr: float = 0.0
    roas: float = 2.8
    chain_latency_s: float = 4.9
    other_regions_status: str = "All 5 other regions unchanged"
    execution_status: Optional[str] = None
    rollback_triggered: bool = False


# ---------------------------------------------------------------------------
# WebSocket event schema
# ---------------------------------------------------------------------------

class WSEvent(BaseModel):
    ts: str
    run_id: str
    agent: str
    phase: str
    kind: str
    level: str = "info"
    message: str = ""
    payload: dict = Field(default_factory=dict)
