"""
Pydantic v2 schemas for the Executor Agent.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StepStatus = Literal[
    "success",
    "failed_then_recovered",
    "failed_then_rolled_back",
    "skipped",
]
OverallStatus = Literal["completed", "partial", "rolled_back"]


class ToolCall(BaseModel):
    tool: str
    args_summary: dict = Field(default_factory=dict)
    result_summary: dict = Field(default_factory=dict)
    ts: str
    latency_ms: int


class ExecutionStep(BaseModel):
    action_id: str
    status: StepStatus
    attempts: int
    tool_calls: list[ToolCall] = Field(default_factory=list)
    compensating_action_run: str | None = None
    rationale: str = ""


class ExecutionResult(BaseModel):
    run_id: str
    detected_region: str | None
    steps: list[ExecutionStep] = Field(default_factory=list)
    cumulative_cost_pkr: float = 0.0
    total_latency_s: float = 0.0
    overall_status: OverallStatus = "completed"
