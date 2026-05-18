from typing import List
from pydantic import BaseModel, Field

class ExecutionResult(BaseModel):
    """
    Tracks the result of the pipeline execution.
    """
    run_id: str = Field(..., description="The unique identifier for the execution run")
    final_status: str = Field(..., description="Final execution status (e.g., SUCCESS, HALTED, BLOCKED - NEEDS HUMAN REVIEW)")
    completed_steps: List[str] = Field(default_factory=list, description="List of successfully completed step IDs")
    rollback_triggered: bool = Field(default=False, description="Whether a rollback sequence was triggered during execution")
    message: str = Field("", description="Detailed execution message or reason for the final status")
