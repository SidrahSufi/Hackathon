from typing import List
from pydantic import BaseModel, Field

class ActionItem(BaseModel):
    id: str = Field(..., description="Action ID (e.g., A1-A5)")
    title: str = Field(..., description="Title of the strategic action")
    cost_pkr: float = Field(..., description="Estimated cost of the action in PKR")
    preconditions: List[str] = Field(
        default_factory=list, 
        description="List of Action IDs that must complete before this action"
    )

class ActionChain(BaseModel):
    plan_id: str = Field(..., description="Unique identifier for the action plan")
    target_region: str = Field(..., description="The dynamic detected_outlier_region from insights")
    actions: List[ActionItem] = Field(..., description="Exactly 5 ordered actions mapping out the strategic response")
