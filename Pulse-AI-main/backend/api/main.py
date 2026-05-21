"""
PulseAI Backend — FastAPI app.

Exposes the agent pipeline as REST + WebSocket endpoints for the mobile app.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, scenarios

log = structlog.get_logger()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    state_dir = _workspace_root() / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)
    log.info("PulseAI backend ready", state_dir=str(state_dir))
    yield


app = FastAPI(
    title="PulseAI Backend",
    version="0.1.0",
    description=(
        "Backend for PulseAI — autonomous multi-region operations agent. "
        "Wraps the agent pipeline as REST + WebSocket endpoints."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(scenarios.router)


@app.get("/")
async def root() -> dict:
    return {
        "name": "PulseAI Backend",
        "version": "0.1.0",
        "endpoints": [
            "GET  /healthz",
            "POST /api/scenarios/run",
            "GET  /api/scenarios/runs",
            "GET  /api/scenarios/runs/{run_id}",
            "DEL  /api/scenarios/runs/{run_id}",
            "GET  /api/scenarios/runs/{run_id}/sources",
            "GET  /api/scenarios/runs/{run_id}/insights",
            "GET  /api/scenarios/runs/{run_id}/contradictions",
            "GET  /api/scenarios/runs/{run_id}/plan",
            "GET  /api/scenarios/runs/{run_id}/execution",
            "GET  /api/scenarios/runs/{run_id}/monitor",
            "GET  /api/scenarios/runs/{run_id}/outcome",
            "GET  /api/scenarios/runs/{run_id}/trace.zip",
            "WS   /api/scenarios/runs/{run_id}/events",
        ],
    }
