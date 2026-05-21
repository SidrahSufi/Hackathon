"""
Scenarios router — all REST endpoints for running and inspecting agent runs,
plus the WebSocket for live event streaming.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import structlog
from fastapi import APIRouter, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

from api.models import RunRequest, RunStarted, RunStatus
from api.pipeline_runner import (
    _state_dir,
    all_run_ids,
    get_run_state,
    start_pipeline,
)
from api.trace_packer import pack_trace
from api.ws.hub import manager

log = structlog.get_logger()

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESOURCE_NAMES = (
    "ingestion", "insights", "contradictions",
    "plan", "execution", "monitor", "outcome",
)


def _read_resource(run_id: str, name: str) -> dict | None:
    path = _state_dir(run_id) / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _available(run_id: str) -> list[str]:
    sd = _state_dir(run_id)
    if not sd.exists():
        return []
    have = {f.stem for f in sd.iterdir() if f.suffix == ".json"}
    return [n for n in RESOURCE_NAMES if n in have]


def _current_phase(run_id: str) -> str:
    state = get_run_state(run_id)
    if state and state.get("status") == "completed":
        return "done"
    if state and state.get("status") == "failed":
        return "failed"
    avail = _available(run_id)
    if not avail:
        return "starting"
    # the latest completed resource maps to the current phase
    return avail[-1]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/run", response_model=RunStarted)
async def post_run(req: RunRequest) -> RunStarted:
    """Start a new pipeline run."""
    run_id = f"r-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    await start_pipeline(run_id, req.scenario_id, req.seed_region)
    return RunStarted(run_id=run_id, status="started")


@router.get("/runs")
async def list_runs() -> dict:
    """List recent runs (in-memory)."""
    ids = all_run_ids()[-20:]
    return {"runs": [get_run_state(r) for r in ids if get_run_state(r)]}


@router.get("/runs/{run_id}", response_model=RunStatus)
async def get_run(run_id: str) -> RunStatus:
    state = get_run_state(run_id)
    if state is None and not _state_dir(run_id).exists():
        raise HTTPException(404, f"Run {run_id} not found")

    if state is None:
        # On-disk-only run (e.g. produced by CLI). Synthesize a state.
        state = {
            "status": "completed" if "outcome" in _available(run_id) else "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "detected_region": None,
            "error": None,
        }
        insights = _read_resource(run_id, "insights")
        if insights:
            state["detected_region"] = insights.get("detected_outlier_region")

    return RunStatus(
        run_id=run_id,
        status=state["status"],
        current_phase=_current_phase(run_id),
        detected_region=state.get("detected_region"),
        started_at=state["started_at"],
        completed_at=state.get("completed_at"),
        available_resources=_available(run_id),
        error=state.get("error"),
    )


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str) -> dict:
    import shutil

    sd = _state_dir(run_id)
    if sd.exists():
        shutil.rmtree(sd)
    return {"run_id": run_id, "deleted": True}


def _serve_resource(run_id: str, name: str) -> Response:
    """Helper used by every sub-resource endpoint."""
    if not _state_dir(run_id).exists():
        raise HTTPException(404, f"Run {run_id} not found")
    data = _read_resource(run_id, name)
    if data is None:
        return JSONResponse(
            status_code=202,
            content={
                "status": "not_ready",
                "current_phase": _current_phase(run_id),
                "run_id": run_id,
            },
        )
    return JSONResponse(content=data)


@router.get("/runs/{run_id}/sources")
async def get_sources(run_id: str) -> Response:
    return _serve_resource(run_id, "ingestion")


@router.get("/runs/{run_id}/insights")
async def get_insights(run_id: str) -> Response:
    return _serve_resource(run_id, "insights")


@router.get("/runs/{run_id}/contradictions")
async def get_contradictions(run_id: str) -> Response:
    return _serve_resource(run_id, "contradictions")


@router.get("/runs/{run_id}/plan")
async def get_plan(run_id: str) -> Response:
    return _serve_resource(run_id, "plan")


@router.get("/runs/{run_id}/execution")
async def get_execution(run_id: str) -> Response:
    return _serve_resource(run_id, "execution")


@router.get("/runs/{run_id}/monitor")
async def get_monitor(run_id: str) -> Response:
    return _serve_resource(run_id, "monitor")


@router.get("/runs/{run_id}/outcome")
async def get_outcome(run_id: str) -> Response:
    return _serve_resource(run_id, "outcome")


@router.get("/runs/{run_id}/trace.zip")
async def get_trace_zip(run_id: str):
    try:
        blob = pack_trace(run_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))

    headers = {"Content-Disposition": f'attachment; filename="trace-{run_id}.zip"'}
    return StreamingResponse(
        iter([blob]),
        media_type="application/zip",
        headers=headers,
    )


@router.websocket("/runs/{run_id}/events")
async def ws_events(websocket: WebSocket, run_id: str) -> None:
    await manager.connect(run_id, websocket)
    try:
        # Replay any events that already exist (resources already on disk)
        sd = _state_dir(run_id)
        if sd.exists():
            for name in RESOURCE_NAMES:
                if (sd / f"{name}.json").exists():
                    await websocket.send_json({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "run_id": run_id,
                        "agent": name,
                        "phase": "phase_complete",
                        "kind": "resource_ready_replay",
                        "level": "info",
                        "payload": {"resource": name},
                    })
        # Keep the connection alive — server pushes events via manager.broadcast()
        while True:
            # Reading lets us detect client disconnect promptly
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(run_id, websocket)
    except Exception:  # noqa: BLE001
        log.exception("ws_error", run_id=run_id)
        await manager.disconnect(run_id, websocket)
