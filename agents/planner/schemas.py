"""
Pydantic v2 schemas for the Action Planner Agent.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Action(BaseModel):
    """A single action in the action chain (DAG)."""

    action_id: str = Field(..., description="e.g. 'A1'")
    title: str
    tool: str = Field(..., description="Name of the mock_* tool to call")
    preconditions: list[str] = Field(
        default_factory=list,
        description="action_ids that must complete before this one",
    )
    cost_pkr: float = 0.0
    latency_s: float = 0.0
    projected_reach: int | None = None
    discount_pct: float | None = None
    region: str | None = None
    constraints: list[str] = Field(default_factory=list)
    rationale: str = ""
    compensating_action: str | None = Field(
        default=None,
        description="Name of the mock_* tool used to roll back",
    )
    tool_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Concrete keyword args passed to the tool at execute time",
    )


class ActionPlan(BaseModel):
    """The full plan produced by the Planner Agent."""

    run_id: str
    detected_region: str | None
    actions: list[Action] = Field(default_factory=list)
    total_cost_pkr: float = 0.0
    total_projected_reach: int = 0
    feasible: bool = True
    revisions_applied: list[dict] = Field(
        default_factory=list,
        description="Log of changes PolicyChecker forced on the plan",
    )
    rationale: str = ""
