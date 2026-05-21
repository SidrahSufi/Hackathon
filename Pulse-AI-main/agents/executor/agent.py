"""
Executor Agent — fourth stage of the PulseAI pipeline.

Runs the action chain produced by the Planner. Handles retry, fallback,
and rollback when things fail. Reads .state/<run_id>/plan.json and
writes .state/<run_id>/execution.json.

Decision logic is pure Python — no LLM in the failure-recovery loop.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from agents.common.policy import PolicyChecker
from agents.executor.schemas import ExecutionResult, ExecutionStep, ToolCall
from agents.tools import mocks as mock_tools

log = structlog.get_logger()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summarize(d: dict, max_chars: int = 300) -> dict:
    """Compact a dict for logging — truncate long values."""
    out: dict = {}
    for k, v in d.items():
        if isinstance(v, str) and len(v) > max_chars:
            out[k] = v[:max_chars] + "…"
        else:
            out[k] = v
    return out


def _call_tool(tool_name: str, args: dict) -> dict:
    """Look up the tool in the registry and invoke it."""
    fn = mock_tools.TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return {
            "success": False,
            "latency_ms": 0,
            "details": {"error": f"unknown_tool: {tool_name}"},
        }
    try:
        return fn(**args)
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "latency_ms": 0,
            "details": {"error": f"tool_exception: {exc}"},
        }


def _execute_with_retry_and_fallback(
    action: dict,
    primary_tool: str,
    primary_args: dict,
    fallback_tool: str | None = None,
) -> tuple[bool, int, list[ToolCall], str]:
    """
    Run a tool with one retry (with reduced batch_size for notification-type tools)
    and a fallback if both attempts fail.

    Returns: (success, attempts, tool_calls, rationale)
    """
    tool_calls: list[ToolCall] = []
    attempts = 1
    result = _call_tool(primary_tool, primary_args)
    tool_calls.append(ToolCall(
        tool=primary_tool,
        args_summary=_summarize(primary_args),
        result_summary=_summarize(result.get("details", {})) if isinstance(
            result.get("details"), dict
        ) else {"raw": str(result.get("details"))[:300]},
        ts=_now_iso(),
        latency_ms=int(result.get("latency_ms", 0)),
    ))

    if result["success"]:
        return True, attempts, tool_calls, "Primary call succeeded."

    # ---- Retry path ----
    attempts = 2
    retry_args = dict(primary_args)
    # If the tool is a notification tool, reduce audience_size (batching).
    if "audience_size" in retry_args and retry_args["audience_size"]:
        retry_args["audience_size"] = min(
            int(retry_args["audience_size"]) // 3, 1500
        )
    # For notification tools, allow the retry by NOT injecting failure again
    if primary_tool == "mock_draft_notification":
        retry_args["inject_failure"] = False

    result = _call_tool(primary_tool, retry_args)
    tool_calls.append(ToolCall(
        tool=primary_tool,
        args_summary=_summarize(retry_args),
        result_summary=_summarize(result.get("details", {})) if isinstance(
            result.get("details"), dict
        ) else {"raw": str(result.get("details"))[:300]},
        ts=_now_iso(),
        latency_ms=int(result.get("latency_ms", 0)),
    ))

    if result["success"]:
        return True, attempts, tool_calls, "Primary failed; retry with smaller batch succeeded."

    # ---- Fallback path ----
    if fallback_tool:
        attempts = 3
        fallback_args = {
            "message": (
                f"PulseAI fallback: {primary_args.get('channel', 'notice')} "
                f"could not be delivered. In-app banner used instead."
            ),
            "region": primary_args.get("region", "unknown"),
        }
        result = _call_tool(fallback_tool, fallback_args)
        tool_calls.append(ToolCall(
            tool=fallback_tool,
            args_summary=_summarize(fallback_args),
            result_summary=_summarize(result.get("details", {})) if isinstance(
                result.get("details"), dict
            ) else {"raw": str(result.get("details"))[:300]},
            ts=_now_iso(),
            latency_ms=int(result.get("latency_ms", 0)),
        ))
        if result["success"]:
            return (
                True,
                attempts,
                tool_calls,
                f"Primary and retry failed; fallback {fallback_tool} succeeded.",
            )

    return (
        False,
        attempts,
        tool_calls,
        "Primary, retry, and fallback all failed.",
    )


def run_executor(run_id: str) -> ExecutionResult:
    """
    Execute the action chain. Returns ExecutionResult and writes execution.json.

    Key behaviors:
    - Every step gates through PolicyChecker.
    - A4 has a side-effect tool (mock_draft_notification) with built-in failure
      injection; the executor retries with batching, then falls back to
      mock_in_app_banner.
    - If a step fails after all recovery paths, compensating actions for all
      previously successful steps are run in reverse (rollback).
    """
    mock_tools.reset_counters()
    workspace = _workspace_root()
    state_dir = workspace / ".state" / run_id

    plan_path = state_dir / "plan.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan not found for run {run_id}: {plan_path}")

    with open(plan_path, "r", encoding="utf-8") as fh:
        plan_data = json.load(fh)

    detected_region = plan_data.get("detected_region")
    actions: list[dict] = plan_data.get("actions", [])

    if not plan_data.get("feasible", False) or not actions:
        result = ExecutionResult(
            run_id=run_id,
            detected_region=detected_region,
            steps=[],
            overall_status="partial",
        )
        _write_execution(state_dir, result)
        return result

    checker = PolicyChecker()
    steps: list[ExecutionStep] = []
    cumulative_cost = 0.0
    total_latency_ms = 0
    successful_actions: list[dict] = []
    overall: str = "completed"

    for action in actions:
        action_id = action["action_id"]
        tool_name = action["tool"]
        tool_args = dict(action.get("tool_args", {}))

        # ---- Policy check ----
        check = checker.check(action)
        if not check["ok"]:
            # Apply suggested revisions
            sug = check.get("suggested_revisions", {})
            if "discount_pct" in sug:
                tool_args["discount_pct"] = sug["discount_pct"]
            recheck = checker.check({**action, **sug})
            if not recheck["ok"]:
                log.warning(
                    "Executor: skipping action due to policy",
                    action_id=action_id,
                    violations=recheck["violations"],
                )
                steps.append(ExecutionStep(
                    action_id=action_id,
                    status="skipped",
                    attempts=0,
                    rationale=f"Policy violation: {recheck['violations']}",
                ))
                overall = "partial"
                continue

        log.info(
            "Executor: starting action",
            agent="executor",
            phase="execute",
            kind="action_start",
            payload={"action_id": action_id, "tool": tool_name},
            level="info",
        )

        # ---- Run primary tool ----
        result = _call_tool(tool_name, tool_args)
        attempts = 1
        tool_calls = [ToolCall(
            tool=tool_name,
            args_summary=_summarize(tool_args),
            result_summary=_summarize(result.get("details", {})) if isinstance(
                result.get("details"), dict
            ) else {"raw": str(result.get("details"))[:300]},
            ts=_now_iso(),
            latency_ms=int(result.get("latency_ms", 0)),
        )]
        total_latency_ms += int(result.get("latency_ms", 0))

        step_status: str = "success"
        step_rationale = "Tool call succeeded."

        if not result["success"]:
            # primary failed — try retry once
            attempts = 2
            retry_args = dict(tool_args)
            retry_result = _call_tool(tool_name, retry_args)
            tool_calls.append(ToolCall(
                tool=tool_name,
                args_summary=_summarize(retry_args),
                result_summary=_summarize(retry_result.get("details", {})) if isinstance(
                    retry_result.get("details"), dict
                ) else {"raw": str(retry_result.get("details"))[:300]},
                ts=_now_iso(),
                latency_ms=int(retry_result.get("latency_ms", 0)),
            ))
            total_latency_ms += int(retry_result.get("latency_ms", 0))

            if retry_result["success"]:
                step_status = "failed_then_recovered"
                step_rationale = "Primary failed; retry succeeded."
                result = retry_result
            else:
                # rollback path
                step_status = "failed_then_rolled_back"
                step_rationale = "Primary and retry failed; rolling back successful steps."
                # rollback in reverse order
                for prev in reversed(successful_actions):
                    comp = prev.get("compensating_action")
                    if comp:
                        comp_args = {
                            "region": prev.get("region", "unknown"),
                            "campaign_id": prev.get("tool_args", {}).get(
                                "campaign_id", "unknown"
                            ),
                        }
                        comp_result = _call_tool(comp, comp_args)
                        log.info(
                            "Executor: rollback action",
                            agent="executor",
                            phase="rollback",
                            kind="compensate",
                            payload={
                                "for": prev["action_id"],
                                "via": comp,
                                "success": comp_result["success"],
                            },
                            level="info",
                        )
                overall = "rolled_back"
                steps.append(ExecutionStep(
                    action_id=action_id,
                    status=step_status,
                    attempts=attempts,
                    tool_calls=tool_calls,
                    compensating_action_run=None,
                    rationale=step_rationale,
                ))
                break

        # ---- Handle A4's side-effect (mock_draft_notification) ----
        if (
            tool_name == "mock_update_pricing"
            and tool_args.get("side_effect_tool") == "mock_draft_notification"
        ):
            side_args = dict(tool_args.get("side_effect_args", {}))
            side_args.setdefault("region", action.get("region"))
            success, side_attempts, side_calls, side_rationale = (
                _execute_with_retry_and_fallback(
                    action,
                    primary_tool="mock_draft_notification",
                    primary_args=side_args,
                    fallback_tool="mock_in_app_banner",
                )
            )
            tool_calls.extend(side_calls)
            for c in side_calls:
                total_latency_ms += c.latency_ms
            attempts = max(attempts, side_attempts)
            if not success:
                step_status = "failed_then_rolled_back"
                step_rationale = (
                    "Notification side-effect failed in primary + retry + fallback."
                )
                overall = "partial"
            elif side_attempts > 1:
                step_status = "failed_then_recovered"
                step_rationale = side_rationale

        # ---- Record success ----
        checker.record_usage(action, result)
        cumulative_cost += float(action.get("cost_pkr", 0) or 0)
        successful_actions.append(action)
        steps.append(ExecutionStep(
            action_id=action_id,
            status=step_status,
            attempts=attempts,
            tool_calls=tool_calls,
            rationale=step_rationale,
        ))

    final = ExecutionResult(
        run_id=run_id,
        detected_region=detected_region,
        steps=steps,
        cumulative_cost_pkr=cumulative_cost,
        total_latency_s=round(total_latency_ms / 1000.0, 2),
        overall_status=overall,  # type: ignore[arg-type]
    )
    _write_execution(state_dir, final)

    log.info(
        "Executor: complete",
        agent="executor",
        phase="done",
        kind="result",
        payload={
            "run_id": run_id,
            "overall_status": final.overall_status,
            "steps": len(final.steps),
            "cumulative_cost_pkr": final.cumulative_cost_pkr,
            "total_latency_s": final.total_latency_s,
        },
        level="info",
    )
    return final


def _write_execution(state_dir: Path, result: ExecutionResult) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "execution.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(result.model_dump_json(indent=2))
