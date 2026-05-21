"""
End-to-end pipeline runner for PulseAI agents (all 6 stages).
"""
import argparse
import subprocess
import sys
from pathlib import Path

import structlog

from agents.conflict.agent import run_conflict
from agents.executor.agent import run_executor
from agents.ingestion.agent import run_ingestion
from agents.insight.agent import run_insight
from agents.monitor.agent import run_monitor
from agents.outcome.compute import compute_outcome
from agents.planner.agent import run_planner

log = structlog.get_logger()


def ensure_mock_data(seed: str):
    """Ensure mock data exists for the given seed, or generate it."""
    workspace = Path(__file__).resolve().parent.parent
    source_dir = workspace / "sources" / "zarapk_regional_v1" / seed

    if not source_dir.exists() or not list(source_dir.glob("*")):
        log.info(f"Mock data for {seed} not found. Generating...")
        subprocess.run(
            [sys.executable, "-m", "agents.gen_mock_data", "--seed", seed],
            check=True,
        )
        log.info(f"Mock data for {seed} generated successfully.")


def run_pipeline(run_id: str, seed: str) -> dict:
    """
    Programmatic entry-point used by the FastAPI backend and tests.
    Runs all 6 stages and returns a summary dict.
    """
    ensure_mock_data(seed)
    log.info(f"=== PulseAI Pipeline | seed={seed} | run_id={run_id} ===")

    ingestion_result = run_ingestion(run_id, seed)
    log.info(
        f"[ingest] processed={ingestion_result.sources_processed} "
        f"discarded={ingestion_result.sources_discarded}"
    )

    insight_result = run_insight(run_id)
    outlier = insight_result.detected_outlier_region
    insights_count = len(insight_result.insights)
    log.info(f"[insight] outlier={outlier} insights={insights_count}")

    conflict_result = run_conflict(run_id)
    surfaced = len(conflict_result.contradictions)
    needs_review = sum(
        1 for c in conflict_result.contradictions
        if c.status == "needs_human_review"
    )
    not_a_conflict = len(conflict_result.not_a_conflict_log)
    log.info(
        f"[conflict] surfaced={surfaced} not_a_conflict={not_a_conflict} "
        f"needs_review={needs_review}"
    )

    plan = run_planner(run_id)
    log.info(
        f"[planner] actions={len(plan.actions)} cost={plan.total_cost_pkr:.0f} "
        f"feasible={plan.feasible} revisions={len(plan.revisions_applied)}"
    )

    execution = run_executor(run_id)
    recoveries = sum(
        1 for s in execution.steps if s.status == "failed_then_recovered"
    )
    log.info(
        f"[executor] status={execution.overall_status} "
        f"steps={len(execution.steps)} latency={execution.total_latency_s}s "
        f"recoveries={recoveries}"
    )

    monitor = run_monitor(run_id, compressed_seconds=0.5)
    log.info(
        f"[monitor] simulated_days={monitor['simulated_days']} "
        f"auto_paused={monitor['auto_paused']}"
    )

    outcome = compute_outcome(run_id)
    log.info(
        f"[outcome] roas={outcome.get('projected_roas')} "
        f"reach={outcome.get('after', {}).get('projected_reach')}"
    )

    return {
        "run_id": run_id,
        "seed": seed,
        "detected_outlier_region": outlier,
        "insights_count": insights_count,
        "surfaced_contradictions": surfaced,
        "needs_human_review": needs_review,
        "plan_actions": len(plan.actions),
        "execution_status": execution.overall_status,
        "monitor_status": monitor["status"],
        "outcome": outcome,
    }


def main():
    parser = argparse.ArgumentParser(description="PulseAI End-to-End Pipeline Runner")
    parser.add_argument(
        "--seed", required=True, choices=["lahore", "karachi"], help="Seed region"
    )
    parser.add_argument(
        "--run-id", required=True, help="Unique identifier for the run"
    )
    args = parser.parse_args()

    summary = run_pipeline(args.run_id, args.seed)

    workspace = Path(__file__).resolve().parent.parent
    state_dir = workspace / ".state" / args.run_id

    print("\n" + "=" * 60)
    print("FINAL SUMMARY BLOCK")
    print("=" * 60)
    print(f"run_id:                    {summary['run_id']}")
    print(f"seed_region:               {summary['seed']}")
    print(f"detected_outlier_region:   {summary['detected_outlier_region']}")
    print(f"insights:                  {summary['insights_count']}")
    print(f"surfaced contradictions:   {summary['surfaced_contradictions']}")
    print(f"needs_human_review:        {summary['needs_human_review']}")
    print(f"plan actions:              {summary['plan_actions']}")
    print(f"execution status:          {summary['execution_status']}")
    print(f"monitor status:            {summary['monitor_status']}")
    out = summary['outcome']
    print(f"projected ROAS:            {out.get('projected_roas')}")
    print(f"projected reach:           {out.get('after', {}).get('projected_reach')}")
    print(f"campaign cost (PKR):       {out.get('campaign_cost_pkr')}")
    print(f"chain latency (s):         {out.get('chain_latency_s')}")
    print("-" * 60)
    print("Output files:")
    for name in (
        "ingestion.json", "insights.json", "contradictions.json",
        "plan.json", "execution.json", "monitor.json", "outcome.json",
    ):
        print(f"  - {state_dir / name}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
