from typing import List
from pydantic import BaseModel, Field

class MonitorResult(BaseModel):
    """
    Schema capturing the final tracked state of the campaign post-monitoring.
    """
    campaign_id: str = Field(..., description="The unique ID of the tracked campaign")
    days_tracked: int = Field(..., description="Number of days the campaign was monitored before completion or termination")
    daily_roas_log: List[float] = Field(..., description="Log of the daily Return on Ad Spend (ROAS) values")
    termination_status: str = Field(..., description="Status of the campaign termination (e.g., ACTIVE, PAUSED_DUE_TO_ROAS, COMPLETED)")
