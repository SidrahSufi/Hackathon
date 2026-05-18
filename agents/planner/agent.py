
import json
from pathlib import Path
from typing import Any, Dict

import structlog
from google.adk.agents import LlmAgent

from agents.planner.prompts import PLANNER_SYSTEM_INSTRUCTION
from agents.planner.schemas import ActionChain

log = structlog.get_logger()

class PlannerAgent:
    """
    ActionPlannerAgent reads the resolved insights and generates an execution DAG
    (ActionChain) of actions to address the identified issues.
    """
    
    def __init__(self):
        self.agent = LlmAgent(
            name="action_planner",
            model="gemini-3.0-pro",
            instruction=PLANNER_SYSTEM_INSTRUCTION,
        )

    def generate_plan(self, run_id: str) -> ActionChain:
        """
        Reads insights.json, generates an action plan using the ADK LlmAgent,
        and writes the resulting ActionChain to plan.json.
        """
        workspace = Path(__file__).resolve().parent.parent.parent
        state_dir = workspace / ".state" / run_id
        insights_path = state_dir / "insights.json"

        if not insights_path.exists():
            log.error("Insights file not found", run_id=run_id, path=str(insights_path))
            raise FileNotFoundError(f"Missing insights for run_id {run_id} at {insights_path}")

        # 1. Read the insights state
        insights_data = insights_path.read_text(encoding="utf-8")
        
        log.info(
            "Generating action plan from insights",
            agent="planner",
            run_id=run_id
        )

        # 2. In a fully implemented ADK setup, we'd invoke the agent to generate structured output.
        # Example using a mock implementation until full ADK integration is provided:
        # prompt = f"Generate an ActionChain based on these insights: {insights_data}"
        # response = self.agent.run(prompt=prompt, output_schema=ActionChain)
        
        # Here we simulate the LLM's structured output response
        # In actual production, you would return the parsed schema directly from ADK.
        try:
            # Note: Replace with actual `self.agent.run(...)` or equivalent ADK inference call
            # which natively maps to the Pydantic schema.
            mock_plan_data = {
                "plan_id": f"plan_{run_id}",
                "target_region": "US-West", # Ideally parsed from insights
                "actions": [
                    {
                        "id": "A1",
                        "title": "Diagnose Root Cause",
                        "cost_pkr": 5000.0,
                        "preconditions": []
                    },
                    {
                        "id": "A2",
                        "title": "Notify Regional Teams",
                        "cost_pkr": 1000.0,
                        "preconditions": ["A1"]
                    },
                    {
                        "id": "A3",
                        "title": "Adjust Pricing Model",
                        "cost_pkr": 20000.0,
                        "preconditions": ["A1"]
                    },
                    {
                        "id": "A4",
                        "title": "Launch Remediation Campaign",
                        "cost_pkr": 150000.0,
                        "preconditions": ["A3"]
                    },
                    {
                        "id": "A5",
                        "title": "Enable Continuous Monitoring",
                        "cost_pkr": 3000.0,
                        "preconditions": ["A2", "A4"]
                    }
                ]
            }
            action_chain = ActionChain(**mock_plan_data)
        except Exception as e:
            log.error("Failed to generate action plan", error=str(e), run_id=run_id)
            raise

        # 3. Write state cleanly
        state_dir.mkdir(parents=True, exist_ok=True)
        out_path = state_dir / "plan.json"
        out_path.write_text(action_chain.model_dump_json(indent=2), encoding="utf-8")

        log.info(
            "Action plan generated and saved successfully",
            agent="planner",
            run_id=run_id,
            plan_id=action_chain.plan_id,
            target_region=action_chain.target_region
        )

        return action_chain

def run_planner(run_id: str) -> ActionChain:
    """Helper entry point for orchestration."""
    planner = PlannerAgent()
    return planner.generate_plan(run_id)
