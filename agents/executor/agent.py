import json
from pathlib import Path
from typing import List

import structlog

from agents.executor.schemas import ExecutionResult
from agents.executor.policy_checker import PolicyChecker

log = structlog.get_logger()


class ExecutorAgent:
    """
    ExecutorAgent runs the strategic actions defined in the ActionChain.
    It enforces business rules, verifies contradiction states,
    and gracefully handles rollbacks.
    """

    def __init__(self):
        # Resolve workspace root
        self.workspace = Path(__file__).resolve().parent.parent.parent

        # Correct policy path
        policy_path = self.workspace / "config" / "policies.yaml"

        self.policy_checker = PolicyChecker(str(policy_path))

    # ==========================================================
    # Compatibility wrapper for run_pipeline.py
    # ==========================================================

    def execute_plan(self, run_id: str):
        """
        Wrapper method so orchestration can call:
        executor.execute_plan(run_id)
        """
        return self.execute_pipeline(run_id)

    # ==========================================================
    # Main execution pipeline
    # ==========================================================

    def execute_pipeline(self, run_id: str) -> ExecutionResult:

        state_dir = self.workspace / ".state" / run_id

        log.info(
            "Starting execution pipeline",
            run_id=run_id,
            agent="executor"
        )

        # ======================================================
        # 1. Read contradictions.json
        # ======================================================

        contradictions_path = state_dir / "contradictions.json"

        if contradictions_path.exists():

            try:
                contradictions_data = json.loads(
                    contradictions_path.read_text(encoding="utf-8")
                )

                contradictions = contradictions_data.get(
                    "contradictions",
                    []
                )

                for conflict in contradictions:

                    if conflict.get("status") == "needs_human_review":

                        log.warning(
                            "Execution blocked by unresolved contradiction",
                            run_id=run_id,
                            conflict_id=conflict.get("conflict_id")
                        )

                        return ExecutionResult(
                            run_id=run_id,
                            final_status="BLOCKED - NEEDS HUMAN REVIEW",
                            message=(
                                f"Contradiction "
                                f"{conflict.get('conflict_id')} "
                                f"requires human review."
                            )
                        )

            except Exception as e:

                log.error(
                    "Failed to parse contradictions.json",
                    error=str(e),
                    run_id=run_id
                )

        # ======================================================
        # 2. Read plan.json
        # ======================================================

        plan_path = state_dir / "plan.json"

        if not plan_path.exists():

            log.error("plan.json not found", run_id=run_id)

            return ExecutionResult(
                run_id=run_id,
                final_status="HALTED",
                message=(
                    "plan.json not found. "
                    "Pipeline cannot proceed without an ActionChain."
                )
            )

        try:
            plan_data = json.loads(
                plan_path.read_text(encoding="utf-8")
            )

            actions = plan_data.get("actions", [])

        except Exception as e:

            log.error(
                "Failed to load plan",
                error=str(e),
                run_id=run_id
            )

            return ExecutionResult(
                run_id=run_id,
                final_status="HALTED",
                message=f"Failed to load ActionChain plan: {e}"
            )

        # ======================================================
        # 3. Execution Loop
        # ======================================================

        completed_steps: List[str] = []

        rollback_triggered = False

        final_status = "SUCCESS"

        message = "All actions completed successfully."

        for action in actions:

            action_id = action.get("id")

            title = action.get("title")

            cost_pkr = action.get("cost_pkr", 0.0)

            # ==================================================
            # Policy Check
            # ==================================================

            budget_check = self.policy_checker.check_budget(
                cost_pkr
            )

            if not budget_check.is_valid:

                log.error(
                    "Policy violation detected",
                    action=action_id,
                    reason=budget_check.message
                )

                rollback_triggered = True

                final_status = "HALTED"

                message = (
                    f"Policy violation on {action_id}: "
                    f"{budget_check.message}"
                )

                break

            # ==================================================
            # Simulated execution
            # ==================================================

            try:

                log.info(
                    f"Executing step {action_id}...",
                    title=title,
                    cost_pkr=cost_pkr
                )

                # Simulated failure on A4
                if action_id == "A4":

                    raise RuntimeError(
                        "Simulated external API execution failure on A4."
                    )

                completed_steps.append(action_id)

                log.info(
                    f"Step {action_id} completed successfully."
                )

            except Exception as e:

                log.error(
                    f"Execution failed on {action_id}",
                    error=str(e)
                )

                rollback_triggered = True

                final_status = "HALTED"

                message = (
                    f"Execution failed on {action_id}: {e}"
                )

                break

        # ======================================================
        # 4. Rollback Sequence
        # ======================================================

        if rollback_triggered:

            log.warning(
                "Initiating rollback sequence...",
                completed_steps=completed_steps
            )

            while completed_steps:

                rollback_step = completed_steps.pop()

                log.info(
                    f"Rolling back step {rollback_step}..."
                )

                # Simulated rollback
                log.info(
                    f"Step {rollback_step} rolled back successfully."
                )

        # ======================================================
        # 5. Build Final Result
        # ======================================================

        result = ExecutionResult(
            run_id=run_id,
            final_status=final_status,
            completed_steps=completed_steps,
            rollback_triggered=rollback_triggered,
            message=message
        )

        # ======================================================
        # 6. Save execution.json
        # ======================================================

        state_dir.mkdir(parents=True, exist_ok=True)

        out_path = state_dir / "execution_logs.json"

        out_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8"
        )

        log.info(
            "Pipeline execution finished",
            run_id=run_id,
            final_status=final_status,
            rollback_triggered=rollback_triggered
        )

        return result


# ==============================================================
# Helper Entrypoint
# ==============================================================

def run_executor(run_id: str) -> ExecutionResult:
    """
    Helper entry point for orchestration.
    """

    agent = ExecutorAgent()

    return agent.execute_pipeline(run_id)


# import json
# from pathlib import Path
# from typing import List

# import structlog

# from agents.executor.schemas import ExecutionResult
# from agents.executor.policy_checker import PolicyChecker

# log = structlog.get_logger()

# class ExecutorAgent:
#     """
#     ExecutorAgent runs the strategic actions defined in the ActionChain.
#     It enforces business rules, verifies contradiction states, and gracefully handles rollbacks.
#     """
    
#     def __init__(self):
#         # Resolve path to the policies configuration
#         self.workspace = Path(__file__).resolve().parent.parent.parent
#         policy_path = self.workspace / "config" / "policies.yaml"
#         self.policy_checker = PolicyChecker(str(policy_path))
        
#     def execute_pipeline(self, run_id: str) -> ExecutionResult:
#         state_dir = self.workspace / ".state" / run_id
        
#         log.info("Starting execution pipeline", run_id=run_id, agent="executor")
        
#         # 1. Read contradictions.json
#         contradictions_path = state_dir / "contradictions.json"
#         if contradictions_path.exists():
#             try:
#                 contradictions_data = json.loads(contradictions_path.read_text(encoding="utf-8"))
#                 contradictions = contradictions_data.get("contradictions", [])
                
#                 for conflict in contradictions:
#                     if conflict.get("status") == "needs_human_review":
#                         log.warning(
#                             "Execution blocked by unresolved contradiction",
#                             run_id=run_id,
#                             conflict_id=conflict.get("conflict_id")
#                         )
#                         return ExecutionResult(
#                             run_id=run_id,
#                             final_status="BLOCKED - NEEDS HUMAN REVIEW",
#                             message=f"Contradiction {conflict.get('conflict_id')} requires human review."
#                         )
#             except Exception as e:
#                 log.error("Failed to parse contradictions.json", error=str(e), run_id=run_id)
        
#         # 2. Read the Action Plan (plan.json)
#         plan_path = state_dir / "plan.json"
#         if not plan_path.exists():
#             log.error("plan.json not found", run_id=run_id)
#             return ExecutionResult(
#                 run_id=run_id,
#                 final_status="HALTED",
#                 message="plan.json not found. Pipeline cannot proceed without an ActionChain."
#             )
            
#         try:
#             plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
#             actions = plan_data.get("actions", [])
#         except Exception as e:
#             log.error("Failed to load plan", error=str(e), run_id=run_id)
#             return ExecutionResult(
#                 run_id=run_id,
#                 final_status="HALTED",
#                 message=f"Failed to load ActionChain plan: {e}"
#             )
            
#         completed_steps: List[str] = []
#         rollback_triggered = False
#         final_status = "SUCCESS"
#         message = "All actions completed successfully."

#         # 3. Execute actions loop
#         for action in actions:
#             action_id = action.get("id")
#             title = action.get("title")
#             cost_pkr = action.get("cost_pkr", 0.0)
            
#             # Policy Check
#             budget_check = self.policy_checker.check_budget(cost_pkr)
#             if not budget_check.is_valid:
#                 log.error("Policy violation detected", action=action_id, reason=budget_check.message)
#                 rollback_triggered = True
#                 final_status = "HALTED"
#                 message = f"Policy violation on {action_id}: {budget_check.message}"
#                 break
                
#             try:
#                 log.info(f"Executing step {action_id}...", title=title, cost_pkr=cost_pkr)
                
#                 # Simulated failure on A4 as specified by requirements
#                 if action_id == "A4":
#                     raise RuntimeError("Simulated external API execution failure on A4.")
                
#                 completed_steps.append(action_id)
#                 log.info(f"Step {action_id} completed successfully.")
                
#             except Exception as e:
#                 log.error(f"Execution failed on {action_id}", error=str(e))
#                 rollback_triggered = True
#                 final_status = "HALTED"
#                 message = f"Execution failed on {action_id}: {e}"
#                 break
                
#         # 4. Rollback sequence using backward-stepping stack loop
#         if rollback_triggered:
#             log.warning("Initiating rollback sequence...", completed_steps=completed_steps)
#             while completed_steps:
#                 rollback_step = completed_steps.pop()
#                 log.info(f"Rolling back step {rollback_step}...")
#                 # Simulate rollback success
#                 log.info(f"Step {rollback_step} rolled back successfully.")
            
#         result = ExecutionResult(
#             run_id=run_id,
#             final_status=final_status,
#             completed_steps=completed_steps,
#             rollback_triggered=rollback_triggered,
#             message=message
#         )
        
#         # 5. Write state cleanly
#         state_dir.mkdir(parents=True, exist_ok=True)
#         out_path = state_dir / "execution.json"
#         out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        
#         log.info(
#             "Pipeline execution finished", 
#             run_id=run_id, 
#             final_status=final_status, 
#             rollback_triggered=rollback_triggered
#         )
        
#         return result

# def run_executor(run_id: str) -> ExecutionResult:
#     """Helper entry point for orchestration."""
#     agent = ExecutorAgent()
#     return agent.execute_pipeline(run_id)
