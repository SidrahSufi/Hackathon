"""
Action Planner Agent — third stage of the PulseAI pipeline.

Reads .state/<run_id>/insights.json and contradictions.json.
Builds the 5-action chain (Diagnose → Notify → Launch → Update Pricing → Monitor)
targeting the detected outlier region. Runs each action through PolicyChecker
and revises as needed. Writes plan.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import structlog

from agents.common.policy import PolicyChecker
from agents.planner.schemas import Action, ActionPlan

log = structlog.get_logger()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _build_baseline_chain(region: str, run_id: str) -> list[Action]:
    """
    Construct the canonical 5-action chain.

    Initial discount on A3 is 25% — PolicyChecker will revise this to 20%
    (the demo's "revisions_applied" trail).
    """
    affected_segment = {
        "category": "women's casual wear",
        "age_range": [22, 32],
    }

    return [
        Action(
            action_id="A1",
            title=f"Diagnose affected SKUs + customer segments in {region}",
            tool="mock_segment_breakdown",
            preconditions=[],
            cost_pkr=0.0,
            latency_s=30.0,
            region=region,
            rationale=(
                f"Identify which SKUs and customer segments are driving the decline "
                f"in {region} so subsequent actions target precisely."
            ),
            tool_args={"region": region},
        ),
        Action(
            action_id="A2",
            title=f"Notify {region} sales manager + marketing lead",
            tool="mock_send_email",
            preconditions=["A1"],
            cost_pkr=0.0,
            latency_s=5.0,
            region=region,
            rationale=(
                f"Brief the regional sales and marketing leads on the diagnosis "
                f"so on-the-ground action can begin."
            ),
            tool_args={
                "to": [
                    f"sales-lead-{region.lower()}@zarapk.example",
                    f"marketing-lead-{region.lower()}@zarapk.example",
                ],
                "subject": f"[Action required] {region} performance brief",
                "body": (
                    f"Hi team — Pulse detected an outlier decline in {region}. "
                    f"Please review the attached diagnosis and standby for "
                    f"the discount campaign launch."
                ),
            },
        ),
        Action(
            action_id="A3",
            title=(
                f"Launch discount campaign in {region} "
                f"(women's casual, ages 22-32)"
            ),
            tool="mock_launch_campaign",
            preconditions=["A1"],
            cost_pkr=720000.0,
            latency_s=12.0,
            projected_reach=5200,
            discount_pct=25.0,  # intentionally over the 20% cap; PolicyChecker fixes it
            region=region,
            constraints=[
                "budget_800k",
                "max_discount_20pct",
                "segment_targeted",
                "single_region_per_run",
            ],
            rationale=(
                f"A targeted regional campaign limits spend while concentrating "
                f"effort where it matters."
            ),
            compensating_action="mock_pause_campaign",
            tool_args={
                "region": region,
                "segment": affected_segment,
                "discount_pct": 25.0,
                "budget_pkr": 720000.0,
            },
        ),
        Action(
            action_id="A4",
            title=f"Update checkout pricing + draft customer notifications for {region}",
            tool="mock_update_pricing",
            preconditions=["A3"],
            cost_pkr=0.0,
            latency_s=120.0,
            region=region,
            constraints=[
                "notification_window",
                "rate_limit_5k_per_hr",
                "respect_optouts",
            ],
            rationale=(
                "Apply the agreed discount at checkout and prepare the "
                "customer-facing announcement."
            ),
            compensating_action="mock_revert_pricing",
            tool_args={
                "region": region,
                "sku_list": [f"SKU-{i}" for i in range(1, 50)],
                "discount_pct": 25.0,  # will be aligned with A3 after PolicyChecker
                "side_effect_tool": "mock_draft_notification",
                "side_effect_args": {
                    "channel": "email",
                    "audience_size": 5000,
                },
            },
        ),
        Action(
            action_id="A5",
            title="Schedule 7-day campaign monitor (auto-pause if ROAS < 1.5)",
            tool="mock_schedule_monitor",
            preconditions=["A4"],
            cost_pkr=0.0,
            latency_s=1.0,
            region=region,
            rationale=(
                "Continuously watch the campaign and pull the plug if "
                "ROAS dips below the threshold."
            ),
            tool_args={
                "run_id": run_id,
                "window_days": 7,
            },
        ),
    ]


def run_planner(run_id: str) -> ActionPlan:
    """
    Build the action chain and gate every action through PolicyChecker.
    """
    workspace = _workspace_root()
    state_dir = workspace / ".state" / run_id

    insights_path = state_dir / "insights.json"
    if not insights_path.exists():
        raise FileNotFoundError(
            f"Insights file not found for run {run_id}: {insights_path}"
        )

    with open(insights_path, "r", encoding="utf-8") as fh:
        insights_data = json.load(fh)

    detected_region = insights_data.get("detected_outlier_region")

    if not detected_region:
        # Nothing to act on — return an empty, infeasible plan
        log.info(
            "Planner: no outlier detected, returning empty plan",
            agent="planner",
            phase="done",
            kind="empty_plan",
            payload={"run_id": run_id},
            level="info",
        )
        plan = ActionPlan(
            run_id=run_id,
            detected_region=None,
            actions=[],
            feasible=False,
            rationale="No outlier region detected — no action needed.",
        )
        _write_plan(state_dir, plan)
        return plan

    log.info(
        "Planner: building action chain",
        agent="planner",
        phase="build",
        kind="start",
        payload={"run_id": run_id, "region": detected_region},
        level="info",
    )

    chain = _build_baseline_chain(detected_region, run_id)
    checker = PolicyChecker()
    revisions: list[dict] = []
    feasible = True

    for action in chain:
        action_dict = action.model_dump()
        # mirror discount_pct into tool_args for the policy check
        if action.discount_pct is not None:
            action_dict["discount_pct"] = action.discount_pct
        check_result = checker.check(action_dict)

        if not check_result["ok"]:
            log.info(
                "Planner: policy violation",
                agent="planner",
                phase="check",
                kind="violation",
                payload={
                    "action_id": action.action_id,
                    "violations": check_result["violations"],
                    "suggested_revisions": check_result["suggested_revisions"],
                },
                level="info",
            )
            suggested = check_result["suggested_revisions"]
            if suggested:
                if "discount_pct" in suggested:
                    new_pct = suggested["discount_pct"]
                    revisions.append({
                        "action_id": action.action_id,
                        "field": "discount_pct",
                        "from": action.discount_pct,
                        "to": new_pct,
                        "reason": "discount cap policy",
                    })
                    action.discount_pct = new_pct
                    action.tool_args["discount_pct"] = new_pct
                if "scheduled_time" in suggested:
                    revisions.append({
                        "action_id": action.action_id,
                        "field": "scheduled_time",
                        "to": suggested["scheduled_time"],
                        "reason": "notification window policy",
                    })
                    action.tool_args["scheduled_time"] = suggested[
                        "scheduled_time"
                    ]
                # propagate A3 discount to A4
                if action.action_id == "A3" and "discount_pct" in suggested:
                    for later in chain:
                        if later.action_id == "A4":
                            later.tool_args["discount_pct"] = suggested["discount_pct"]

                # Re-check after revision
                action_dict = action.model_dump()
                if action.discount_pct is not None:
                    action_dict["discount_pct"] = action.discount_pct
                recheck = checker.check(action_dict)
                if not recheck["ok"]:
                    feasible = False
                    log.warning(
                        "Planner: revision did not resolve violations",
                        agent="planner",
                        phase="check",
                        kind="infeasible",
                        payload={
                            "action_id": action.action_id,
                            "remaining": recheck["violations"],
                        },
                        level="warning",
                    )
            else:
                feasible = False

        checker.record_usage(action.model_dump(), {"success": True})

    total_cost = sum(a.cost_pkr for a in chain)
    total_reach = sum(a.projected_reach or 0 for a in chain)

    plan = ActionPlan(
        run_id=run_id,
        detected_region=detected_region,
        actions=chain,
        total_cost_pkr=total_cost,
        total_projected_reach=total_reach,
        feasible=feasible,
        revisions_applied=revisions,
        rationale=(
            f"Plan targets {detected_region}. Five connected actions, "
            f"total budget {total_cost:,.0f} PKR, projected reach {total_reach:,}."
        ),
    )
    _write_plan(state_dir, plan)

    log.info(
        "Planner: plan complete",
        agent="planner",
        phase="done",
        kind="result",
        payload={
            "run_id": run_id,
            "actions": len(plan.actions),
            "total_cost_pkr": plan.total_cost_pkr,
            "feasible": plan.feasible,
            "revisions": len(plan.revisions_applied),
        },
        level="info",
    )
    return plan


def _write_plan(state_dir: Path, plan: ActionPlan) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "plan.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(plan.model_dump_json(indent=2))
