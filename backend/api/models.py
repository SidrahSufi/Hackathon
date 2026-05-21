"""Request/response models for the FastAPI layer."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    scenario_id: str = "zarapk_regional_v1"
    seed_region: Literal["lahore", "karachi"] = "lahore"


class RunStarted(BaseModel):
    run_id: str
    status: Literal["started"] = "started"


class RunStatus(BaseModel):
    run_id: str
    status: Literal["running", "completed", "failed"]
    current_phase: str
    detected_region: str | None = None
    started_at: str
    completed_at: str | None = None
    available_resources: list[str] = Field(default_factory=list)
    error: str | None = None


class ResourceNotReady(BaseModel):
    status: Literal["not_ready"] = "not_ready"
    current_phase: str
    run_id: str
