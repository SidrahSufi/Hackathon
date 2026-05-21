"""
Pipeline runner — kicks off the agent pipeline as a background thread.

We use a real OS thread (not asyncio.create_task) because in some hosting
contexts (e.g. FastAPI's TestClient) the event loop is short-lived per
request and would kill an asyncio background task. A thread persists.

For the live-event WebSocket experience, the route file kicks off the
tailer separately when a client subscribes.
"""
from __future__ import annotations

import asyncio
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from agents.run_pipeline import run_pipeline as agent_run_pipeline
from api.ws.hub import manager

log = structlog.get_logger()

_runs: dict[str, dict[str, Any]] = {}
_runs_lock = threading.Lock()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _state_dir(run_id: str) -> Path:
    return _workspace_root() / ".state" / run_id


def get_run_state(run_id: str) -> dict | None:
    with _runs_lock:
        return _runs.get(run_id)


def all_run_ids() -> list[str]:
    with _runs_lock:
        return list(_runs.keys())


def _set_state(rid: str, **updates: Any) -> None:
    with _runs_lock:
        _runs.setdefault(rid, {})
        _runs[rid].update(updates)


async def start_pipeline(run_id: str, scenario_id: str, seed_region: str) -> None:
    """
    Launch the agent pipeline in a background thread. Returns immediately.
    """
    started_at = datetime.now(timezone.utc).isoformat()
    _set_state(
        run_id,
        run_id=run_id,
        scenario_id=scenario_id,
        seed_region=seed_region,
        status="running",
        started_at=started_at,
        completed_at=None,
        detected_region=None,
        error=None,
    )
    _state_dir(run_id).mkdir(parents=True, exist_ok=True)

    thread = threading.Thread(
        target=_thread_run_pipeline,
        args=(run_id, seed_region),
        daemon=True,
        name=f"pulseai-pipeline-{run_id}",
    )
    thread.start()


def _thread_run_pipeline(run_id: str, seed_region: str) -> None:
    """Background thread body — runs the pipeline and finalizes run state."""
    try:
        summary = agent_run_pipeline(run_id, seed_region)
        _set_state(
            run_id,
            status="completed",
            detected_region=summary.get("detected_outlier_region"),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        # Best-effort broadcast (only matters if a WS client is subscribed)
        _safe_async_broadcast(run_id, {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "agent": "pipeline",
            "phase": "done",
            "kind": "pipeline_done",
            "level": "info",
            "payload": {
                "detected_region": summary.get("detected_outlier_region"),
                "execution_status": summary.get("execution_status"),
            },
        })
    except Exception as exc:  # noqa: BLE001
        log.exception("pipeline_failed", run_id=run_id)
        _set_state(
            run_id,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            (_state_dir(run_id) / "error.json").write_text(
                f'{{"error": {exc!r}, "traceback": {traceback.format_exc()!r}}}',
                encoding="utf-8",
            )
        except Exception:
            pass


def _safe_async_broadcast(run_id: str, event: dict) -> None:
    """Schedule a broadcast on the main event loop if one is running."""
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        return
    if loop.is_running():
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(manager.broadcast(run_id, event))
        )
