from __future__ import annotations

import sys
import asyncio

# ---------------------------------------------------------------------------
# Windows Subprocess Fix (MUST BE TOP-LEVEL)
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import scenarios as scenarios_router
from backend.routers import websocket as ws_router

# ---------------------------------------------------------------------------
# Configure structlog (simple console output for dev)
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BizPulse API",
    description=(
        "FastAPI backend for the PulseAI multi-agent retail intelligence platform. "
        "Exposes REST endpoints and a WebSocket stream for the Flutter frontend."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — open for demo; Flutter on Android emulator needs this
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(scenarios_router.router)
app.include_router(ws_router.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "bizpulse-backend"}


@app.get("/", tags=["health"])
def root():
    return {
        "service": "BizPulse API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Startup log
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup():
    log.info("bizpulse_api_started", port=8000)
