"""
WebSocket connection manager — fans events out to clients subscribed by run_id.

This is the in-process hub. The file tailer (ws/tailer.py) calls broadcast()
when new state files appear; clients subscribed to that run_id get the event.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict

import structlog
from fastapi import WebSocket

log = structlog.get_logger()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, run_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[run_id].add(ws)
        log.info("ws_connect", run_id=run_id, total=len(self._connections[run_id]))

    async def disconnect(self, run_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[run_id].discard(ws)
            if not self._connections[run_id]:
                del self._connections[run_id]
        log.info("ws_disconnect", run_id=run_id)

    async def broadcast(self, run_id: str, event: dict) -> None:
        """Send `event` (JSON dict) to every client subscribed to run_id."""
        async with self._lock:
            clients = list(self._connections.get(run_id, set()))

        if not clients:
            return

        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(event)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[run_id].discard(ws)


# Module-level singleton — pipeline_runner and routes import this.
manager = ConnectionManager()
