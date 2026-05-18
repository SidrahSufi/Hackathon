"""
event_streamer.py — normalises structlog JSON lines from the subprocess
into the WebSocket event schema expected by the Flutter app.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

# Map structlog event strings / agent keywords → canonical agent names
_AGENT_MAP: dict[str, str] = {
    "ingestion": "Ingestion",
    "ingest": "Ingestion",
    "run_ingestion": "Ingestion",
    "insight": "Insight",
    "run_insight": "Insight",
    "conflict": "ConflictResolver",
    "run_conflict": "ConflictResolver",
    "planner": "ActionPlanner",
    "plan": "ActionPlanner",
    "executor": "Executor",
    "execute": "Executor",
    "monitor": "Monitor",
}

# Map log levels to kind values for the Flutter colour coding
_LEVEL_KIND_MAP: dict[str, str] = {
    "error": "failed",
    "critical": "failed",
    "warning": "retry",
    "warn": "retry",
    "info": "info",
    "debug": "info",
}


def _detect_agent(raw: dict) -> str:
    """Best-effort agent detection from a structlog record."""
    # Explicit 'agent' key wins
    agent_field = str(raw.get("agent", "")).lower()
    for key, canonical in _AGENT_MAP.items():
        if key in agent_field:
            return canonical

    # Fall back to scanning the event string
    event = str(raw.get("event", "")).lower()
    for key, canonical in _AGENT_MAP.items():
        if key in event:
            return canonical

    return "Ingestion"  # safe default


def _detect_phase(raw: dict, agent: str) -> str:
    """Derive a human-readable phase from agent + event."""
    event = str(raw.get("event", "")).lower()
    if "start" in event:
        return "start"
    if "complet" in event or "finish" in event or "success" in event:
        return "complete"
    if "fail" in event or "error" in event:
        return "error"
    if "rollback" in event:
        return "rollback"
    if "retry" in event:
        return "retry"
    # Phase map by agent
    phase_map = {
        "Ingestion": "parse",
        "Insight": "analyze",
        "ConflictResolver": "resolve",
        "ActionPlanner": "plan",
        "Executor": "execute",
        "Monitor": "monitor",
    }
    return phase_map.get(agent, "process")


def _detect_kind(raw: dict, level: str) -> str:
    """Map log level + event content to a Flutter-consumed kind value."""
    event = str(raw.get("event", "")).lower()
    if "start" in event:
        return "started"
    if "complet" in event or "finish" in event or "success" in event:
        return "completed"
    if "fail" in event or "error" in event:
        return "failed"
    if "rollback" in event:
        return "fallback"
    if "retry" in event:
        return "retry"
    return _LEVEL_KIND_MAP.get(level, "info")


def normalize_event(raw: dict, run_id: str) -> dict[str, Any]:
    """
    Convert a raw structlog JSON line into the WebSocket event schema.

    Expected output shape:
    {
        "ts": "10:42:07",
        "run_id": "r-001",
        "agent": "ConflictResolver",
        "phase": "resolve",
        "kind": "contradiction_resolved",
        "level": "info",
        "message": "...",
        "payload": {}
    }
    """
    level = str(raw.get("level", "info")).lower()
    agent = _detect_agent(raw)
    phase = _detect_phase(raw, agent)
    kind = _detect_kind(raw, level)
    message = str(raw.get("event", ""))

    # Timestamp: prefer structlog's timestamp field, else now
    ts_raw = raw.get("timestamp") or raw.get("ts") or raw.get("time")
    try:
        if ts_raw:
            # structlog may emit ISO or epoch; try strptime
            if isinstance(ts_raw, (int, float)):
                dt = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        else:
            dt = datetime.now(tz=timezone.utc)
    except Exception:
        dt = datetime.now(tz=timezone.utc)

    ts_str = dt.strftime("%H:%M:%S")

    # Build payload from remaining fields (exclude known top-level keys)
    _skip = {"event", "level", "timestamp", "ts", "time", "agent", "logger"}
    payload = {k: v for k, v in raw.items() if k not in _skip}

    return {
        "ts": ts_str,
        "run_id": run_id,
        "agent": agent,
        "phase": phase,
        "kind": kind,
        "level": level,
        "message": message,
        "payload": payload,
    }


def parse_line(line: bytes | str, run_id: str) -> dict | None:
    """
    Try to parse a raw stdout/stderr line from the pipeline subprocess.
    Returns None for non-JSON lines (plain print() output etc.).
    """
    text = line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line
    text = text.strip()
    if not text:
        return None
    try:
        raw = json.loads(text)
        if not isinstance(raw, dict):
            return None
        return normalize_event(raw, run_id)
    except json.JSONDecodeError:
        return None
