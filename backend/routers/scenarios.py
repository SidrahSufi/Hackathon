"""
scenarios.py — REST endpoints for the scenario / run lifecycle.

Endpoints
---------
POST  /api/scenarios/run
GET   /api/scenarios/runs/{run_id}
GET   /api/scenarios/runs/{run_id}/sources
GET   /api/scenarios/runs/{run_id}/insights
GET   /api/scenarios/runs/{run_id}/contradictions
GET   /api/scenarios/runs/{run_id}/plan
GET   /api/scenarios/runs/{run_id}/execution
GET   /api/scenarios/runs/{run_id}/outcome
GET   /api/scenarios/runs/{run_id}/trace.zip
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.api import (
    RunRequest,
    RunStartResponse,
    RunStatusResponse,
    SourcesResponse,
    InsightsResponse,
    ContradictionsResponse,
    PlanResponse,
    ExecutionResponse,
    OutcomeResponse,
)
from backend.services import runner as runner_svc
from backend.services import state_reader

log = structlog.get_logger()

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

WORKSPACE = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_run_or_404(run_id: str) -> dict:
    run = runner_svc.runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run_id '{run_id}' not found")
    return run


# ---------------------------------------------------------------------------
# POST /api/scenarios/run
# ---------------------------------------------------------------------------

@router.post("/run", response_model=RunStartResponse, status_code=202)
async def start_run(body: RunRequest, background_tasks: BackgroundTasks):
    """
    Kick off the PulseAI pipeline for a given scenario and seed region.
    Returns immediately with run_id; the pipeline runs in a background task.
    """
    run_id = f"r-{uuid4().hex[:8]}"

    runner_svc.runs[run_id] = {
        "run_id": run_id,
        "status": "running",
        "current_phase": "ingestion",
        "scenario_id": body.scenario_id,
        "seed_region": body.seed_region,
        "detected_region": None,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    # Ensure the event queue exists before background task starts
    import asyncio
    runner_svc.event_queues[run_id] = asyncio.Queue()

    background_tasks.add_task(runner_svc.run_and_stream, run_id, body.seed_region)

    log.info("run_started", run_id=run_id, seed_region=body.seed_region)
    return RunStartResponse(run_id=run_id, status="started")


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(run_id: str):
    run = _get_run_or_404(run_id)

    # Try to populate detected_region from state file if not set yet
    if not run.get("detected_region"):
        insights = state_reader.load_json(run_id, "insights.json")
        region = insights.get("detected_outlier_region")
        if region:
            run["detected_region"] = region

    return RunStatusResponse(
        run_id=run["run_id"],
        status=run["status"],
        current_phase=run.get("current_phase"),
        detected_region=run.get("detected_region"),
        seed_region=run.get("seed_region"),
        created_at=run.get("created_at"),
    )


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/sources
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/sources", response_model=SourcesResponse)
def get_sources(run_id: str):
    _get_run_or_404(run_id)
    return SourcesResponse(sources=state_reader.get_sources(run_id))


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/insights
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/insights", response_model=InsightsResponse)
def get_insights(run_id: str):
    _get_run_or_404(run_id)
    return InsightsResponse(insights=state_reader.get_insights(run_id))


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/contradictions
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/contradictions", response_model=ContradictionsResponse)
def get_contradictions(run_id: str):
    _get_run_or_404(run_id)
    return ContradictionsResponse(contradictions=state_reader.get_contradictions(run_id))


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/plan
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/plan", response_model=PlanResponse)
def get_plan(run_id: str):
    _get_run_or_404(run_id)
    return PlanResponse(actions=state_reader.get_plan(run_id))


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/execution
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/execution", response_model=ExecutionResponse)
def get_execution(run_id: str):
    _get_run_or_404(run_id)
    data = state_reader.get_execution(run_id)
    return ExecutionResponse(**data) if data else ExecutionResponse()


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/outcome
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/outcome", response_model=OutcomeResponse)
def get_outcome(run_id: str):
    _get_run_or_404(run_id)
    outcome = state_reader.compute_outcome(run_id)
    return OutcomeResponse(**outcome)


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs/{run_id}/trace.zip
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}/trace.zip")
def download_trace(run_id: str):
    _get_run_or_404(run_id)
    state_dir = WORKSPACE / ".state" / run_id

    if not state_dir.exists():
        raise HTTPException(status_code=404, detail="No state files found for this run yet.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in state_dir.glob("*.json"):
            zf.write(f, f.name)
        for f in state_dir.glob("*.eml"):
            zf.write(f, f.name)
        for f in state_dir.glob("*.log"):
            zf.write(f, f.name)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=trace_{run_id}.zip"},
    )


# ---------------------------------------------------------------------------
# GET /api/scenarios/runs  (bonus: list recent runs)
# ---------------------------------------------------------------------------

@router.get("/runs")
def list_runs():
    """Return all in-memory runs (most recent first)."""
    all_runs = list(runner_svc.runs.values())
    all_runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return {"runs": all_runs}
