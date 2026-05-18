"""
End-to-end pipeline runner for PulseAI agents.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import structlog

from agents.conflict.agent import run_conflict
from agents.ingestion.agent import run_ingestion
from agents.insight.agent import run_insight

# NEW IMPORTS
from agents.planner.agent import PlannerAgent
from agents.executor.agent import ExecutorAgent

log = structlog.get_logger()


def ensure_mock_data(seed: str):
    """Ensure mock data exists for the given seed, or generate it."""
    workspace = Path(__file__).resolve().parent.parent
    source_dir = workspace / "sources" / "zarapk_regional_v1" / seed

    if not source_dir.exists() or not list(source_dir.glob("*")):
        log.info(f"Mock data for {seed} not found. Generating...")
        subprocess.run(
            [sys.executable, "-m", "agents.gen_mock_data", "--seed", seed],
            check=True
        )
        log.info(f"Mock data for {seed} generated successfully.")


def main():
    parser = argparse.ArgumentParser(description="PulseAI End-to-End Pipeline Runner")

    parser.add_argument(
        "--seed",
        required=True,
        choices=["lahore", "karachi"],
        help="Seed region"
    )

    parser.add_argument(
        "--run-id",
        required=True,
        help="Unique identifier for the run"
    )

    args = parser.parse_args()

    seed = args.seed
    run_id = args.run_id

    # ==================================================
    # 1. Ensure mock data
    # ==================================================

    ensure_mock_data(seed)

    # ==================================================
    # 2. Pipeline Header
    # ==================================================

    log.info(f"=== PulseAI Pipeline | seed={seed} | run_id={run_id} ===")

    # ==================================================
    # 3. Ingestion Agent
    # ==================================================

    ingestion_result = run_ingestion(run_id, seed)

    log.info(
        f"[ingest] processed={ingestion_result.sources_processed} "
        f"discarded={ingestion_result.sources_discarded}"
    )

    # ==================================================
    # 4. Insight Agent
    # ==================================================

    insight_result = run_insight(run_id)

    outlier_region = insight_result.detected_outlier_region
    insights_count = len(insight_result.insights)

    log.info(
        f"[insight] outlier={outlier_region} "
        f"insights={insights_count}"
    )

    # ==================================================
    # 5. Conflict Resolver Agent
    # ==================================================

    conflict_result = run_conflict(run_id)

    surfaced = 0
    needs_review = 0

    for contradiction in conflict_result.contradictions:
        surfaced += 1

        if contradiction.status == "needs_human_review":
            needs_review += 1

    not_a_conflict = len(conflict_result.not_a_conflict_log)

    log.info(
        f"[conflict] surfaced={surfaced} "
        f"not_a_conflict={not_a_conflict} "
        f"needs_review={needs_review}"
    )

    # ==================================================
    # 6. Summary Block
    # ==================================================

    workspace = Path(__file__).resolve().parent.parent
    state_dir = workspace / ".state" / run_id

    ingestion_path = state_dir / "ingestion.json"
    insights_path = state_dir / "insights.json"
    contradictions_path = state_dir / "contradictions.json"

    print("\n" + "=" * 50)
    print("FINAL SUMMARY BLOCK")
    print("=" * 50)
    print(f"run_id:                    {run_id}")
    print(f"seed_region:               {seed}")
    print(f"detected_outlier_region:   {outlier_region}")
    print(f"count of insights:         {insights_count}")
    print(f"surfaced contradictions:   {surfaced}")
    print(f"needs_human_review:        {needs_review}")
    print("-" * 50)

    print("Output Files:")
    print(f"- {ingestion_path}")
    print(f"- {insights_path}")
    print(f"- {contradictions_path}")

    print("=" * 50 + "\n")

    # ==================================================
    # 7. Planner Agent
    # ==================================================

    print("=" * 50)
    print("KICKING OFF DOWNSTREAM AGENT INTERACTION FLOW")
    print("=" * 50)

    planner = PlannerAgent()

    plan = planner.generate_plan(run_id)

    log.info(
        f"[planner] generated plan={plan.plan_id} "
        f"target_region={plan.target_region}"
    )

    # ==================================================
    # 8. Executor Agent
    # ==================================================

    executor = ExecutorAgent()

    executor.execute_plan(run_id)

    log.info("[executor] execution completed")

    print("\n" + "=" * 50)
    print("DOWNSTREAM EXECUTION COMPLETE")
    print("=" * 50)

    plan_path = state_dir / "plan.json"
    execution_logs_path = state_dir / "execution_logs.json"

    print("Generated Files:")
    print(f"- {plan_path}")
    print(f"- {execution_logs_path}")

    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()











# monika code
# """
# End-to-end pipeline runner for PulseAI agents.
# """
# import argparse
# import subprocess
# import sys
# from pathlib import Path

# import structlog

# from agents.conflict.agent import run_conflict
# from agents.ingestion.agent import run_ingestion
# from agents.insight.agent import run_insight

# log = structlog.get_logger()

# def ensure_mock_data(seed: str):
#     """Ensure mock data exists for the given seed, or generate it."""
#     workspace = Path(__file__).resolve().parent.parent
#     source_dir = workspace / "sources" / "zarapk_regional_v1" / seed

#     if not source_dir.exists() or not list(source_dir.glob("*")):
#         log.info(f"Mock data for {seed} not found. Generating...")
#         subprocess.run(
#             [sys.executable, "-m", "agents.gen_mock_data", "--seed", seed],
#             check=True
#         )
#         log.info(f"Mock data for {seed} generated successfully.")


# def main():
#     parser = argparse.ArgumentParser(description="PulseAI End-to-End Pipeline Runner")
#     parser.add_argument("--seed", required=True, choices=["lahore", "karachi"], help="Seed region")
#     parser.add_argument("--run-id", required=True, help="Unique identifier for the run")
#     args = parser.parse_args()

#     seed = args.seed
#     run_id = args.run_id

#     # 1 & 2. Parse args and ensure mock data
#     ensure_mock_data(seed)

#     # 3. Print header
#     log.info(f"=== PulseAI Pipeline | seed={seed} | run_id={run_id} ===")

#     # 4. Call run_ingestion
#     ingestion_result = run_ingestion(run_id, seed)
#     log.info(
#         f"[ingest] processed={ingestion_result.sources_processed} "
#         f"discarded={ingestion_result.sources_discarded}"
#     )

#     # 5. Call run_insight
#     insight_result = run_insight(run_id)
#     outlier_region = insight_result.detected_outlier_region
#     insights_count = len(insight_result.insights)
#     log.info(f"[insight] outlier={outlier_region} insights={insights_count}")

#     # 6. Call run_conflict
#     conflict_result = run_conflict(run_id)
    
#     surfaced = 0
#     needs_review = 0
#     for c in conflict_result.contradictions:
#         surfaced += 1
#         if c.status == "needs_human_review":
#             needs_review += 1
            
#     not_a_conflict = len(conflict_result.not_a_conflict_log)

#     log.info(
#         f"[conflict] surfaced={surfaced} not_a_conflict={not_a_conflict} "
#         f"needs_review={needs_review}"
#     )

#     # 7. Print final summary block
#     workspace = Path(__file__).resolve().parent.parent
#     state_dir = workspace / ".state" / run_id
    
#     ingestion_path = state_dir / "ingestion.json"
#     insights_path = state_dir / "insights.json"
#     contradictions_path = state_dir / "contradictions.json"

#     print("\n" + "="*50)
#     print("FINAL SUMMARY BLOCK")
#     print("="*50)
#     print(f"run_id:                    {run_id}")
#     print(f"seed_region:               {seed}")
#     print(f"detected_outlier_region:   {outlier_region}")
#     print(f"count of insights:         {insights_count}")
#     print(f"surfaced contradictions:   {surfaced}")
#     print(f"needs_human_review:        {needs_review}")
#     print("-" * 50)
#     print("Output Files:")
#     print(f"- {ingestion_path}")
#     print(f"- {insights_path}")
#     print(f"- {contradictions_path}")
#     print("="*50 + "\n")


# if __name__ == "__main__":
#     main()
