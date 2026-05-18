"""
websocket.py — WebSocket endpoint for real-time pipeline event streaming.

WS /api/scenarios/runs/{run_id}/events

Flow
----
1. Client connects → accept, register in ws_clients hub.
2. Replay any events already queued (pipeline might have started already).
3. Wait on the per-run asyncio.Queue; forward each event to the client.
4. When the queue sentinel (None) arrives, send a final "completed" event and close.
5. On disconnect, silently remove the client.
"""
from __future__ import annotations

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services import runner as runner_svc

log = structlog.get_logger()

router = APIRouter(tags=["websocket"])

# run_id → list of active WebSocket connections
ws_clients: dict[str, list[WebSocket]] = {}


async def _send_safe(ws: WebSocket, data: dict) -> bool:
    """Send JSON; return False on disconnect / error."""
    try:
        await ws.send_json(data)
        return True
    except Exception:
        return False


@router.websocket("/api/scenarios/runs/{run_id}/events")
async def ws_events(websocket: WebSocket, run_id: str):
    await websocket.accept()

    # Register client
    ws_clients.setdefault(run_id, []).append(websocket)
    log.info("ws_client_connected", run_id=run_id, total=len(ws_clients[run_id]))

    # Ensure a queue exists even if the run hasn't started yet
    queue = runner_svc.event_queues.setdefault(run_id, asyncio.Queue())

    try:
        # Drain the queue and forward to this client
        while True:
            try:
                # Poll with a short timeout so we can detect WS disconnects
                event: Any = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # Check if client is still alive (ping)
                run_status = runner_svc.runs.get(run_id, {}).get("status", "running")
                if run_status not in ("running",):
                    # Pipeline done, nothing more to stream
                    break
                continue

            if event is None:
                # Sentinel: pipeline finished
                run_status = runner_svc.runs.get(run_id, {}).get("status", "unknown")
                final_kind = "completed" if run_status == "completed" else "failed"
                await _send_safe(websocket, {
                    "ts": _now_ts(),
                    "run_id": run_id,
                    "agent": "Executor",
                    "phase": "complete",
                    "kind": final_kind,
                    "level": "info",
                    "message": f"Pipeline {run_status}.",
                    "payload": {},
                })
                # Re-put sentinel so other connected clients also see it
                await queue.put(None)
                break

            ok = await _send_safe(websocket, event)
            if not ok:
                break

            # Re-queue event for other connected clients on the same run
            await queue.put(event)

    except WebSocketDisconnect:
        log.info("ws_client_disconnected", run_id=run_id)
    finally:
        clients = ws_clients.get(run_id, [])
        if websocket in clients:
            clients.remove(websocket)


def _now_ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
