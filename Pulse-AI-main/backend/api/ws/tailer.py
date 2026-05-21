"""
File tailer — watches .state/<run_id>/ for new state files and broadcasts
synthetic "resource_ready" events to WebSocket clients.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import structlog
from watchfiles import Change, awatch

from api.ws.hub import manager

log = structlog.get_logger()

# Map filename -> the "agent" attribution shown in the event
FILE_TO_AGENT = {
    "ingestion.json": "ingestion",
    "insights.json": "insight",
    "contradictions.json": "conflict",
    "plan.json": "planner",
    "execution.json": "executor",
    "monitor.json": "monitor",
    "outcome.json": "outcome",
}


def _summary_for(path: Path) -> dict:
    """Build a tiny, UI-friendly summary by peeking at the file content."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    name = path.name
    if name == "ingestion.json":
        return {
            "processed": data.get("sources_processed"),
            "discarded": data.get("sources_discarded"),
        }
    if name == "insights.json":
        return {
            "detected_outlier_region": data.get("detected_outlier_region"),
            "count": len(data.get("insights", [])),
        }
    if name == "contradictions.json":
        nhr = sum(
            1 for c in data.get("contradictions", [])
            if c.get("status") == "needs_human_review"
        )
        return {
            "surfaced": len(data.get("contradictions", [])),
            "needs_human_review": nhr,
        }
    if name == "plan.json":
        return {
            "actions": len(data.get("actions", [])),
            "total_cost_pkr": data.get("total_cost_pkr"),
            "feasible": data.get("feasible"),
        }
    if name == "execution.json":
        recoveries = sum(
            1 for s in data.get("steps", [])
            if s.get("status") == "failed_then_recovered"
        )
        return {
            "overall_status": data.get("overall_status"),
            "steps": len(data.get("steps", [])),
            "recoveries": recoveries,
            "total_latency_s": data.get("total_latency_s"),
        }
    if name == "monitor.json":
        return {
            "status": data.get("status"),
            "auto_paused": data.get("auto_paused"),
            "pause_day": data.get("pause_day"),
        }
    if name == "outcome.json":
        return {
            "projected_roas": data.get("projected_roas"),
            "projected_reach": data.get("after", {}).get("projected_reach"),
            "campaign_cost_pkr": data.get("campaign_cost_pkr"),
        }
    return {}


async def tail_run(run_id: str, state_dir: Path) -> None:
    """
    Watch state_dir for file changes. For each new/modified known file,
    broadcast a `resource_ready` event to subscribers.

    This coroutine is cancelled by pipeline_runner when the run completes.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()

    # First pass: emit events for files that already exist
    for f in state_dir.iterdir():
        if f.is_file() and f.name in FILE_TO_AGENT:
            seen.add(f.name)
            await _emit(run_id, f)

    try:
        async for changes in awatch(str(state_dir), recursive=False):
            for change, fp in changes:
                p = Path(fp)
                if p.name not in FILE_TO_AGENT:
                    continue
                if change in (Change.added, Change.modified) and p.name not in seen:
                    seen.add(p.name)
                    await _emit(run_id, p)
    except asyncio.CancelledError:
        log.info("tailer_cancelled", run_id=run_id)
        raise


async def _emit(run_id: str, path: Path) -> None:
    agent = FILE_TO_AGENT.get(path.name, "unknown")
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "agent": agent,
        "phase": "phase_complete",
        "kind": "resource_ready",
        "level": "info",
        "payload": {
            "resource": path.stem,
            "summary": _summary_for(path),
        },
    }
    await manager.broadcast(run_id, event)
