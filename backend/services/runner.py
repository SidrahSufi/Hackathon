"""
runner.py — runs the pipeline in a background thread (no asyncio subprocess).

Windows-safe approach: uses threading + subprocess.Popen instead of
asyncio.create_subprocess_exec (which breaks on Windows with SelectorEventLoop).

Flow
----
POST /run → asyncio.create_task(run_and_stream(...))
           → runs _run_pipeline_thread() in ThreadPoolExecutor
           → reads stdout/stderr line-by-line with Popen
           → puts events into asyncio.Queue via loop.call_soon_threadsafe
           → WS endpoint reads from queue → streams to Flutter
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import structlog

from backend.services.event_streamer import parse_line

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Shared in-memory state
# ---------------------------------------------------------------------------

runs: dict[str, dict] = {}
event_queues: dict[str, asyncio.Queue] = {}

# One shared thread pool for all pipeline runs
_executor = ThreadPoolExecutor(max_workers=4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_ts() -> str:
    return datetime.now(tz=timezone.utc).strftime("%H:%M:%S")


def _synthetic(run_id: str, agent: str, phase: str, kind: str, message: str) -> dict:
    return {
        "ts": _now_ts(),
        "run_id": run_id,
        "agent": agent,
        "phase": phase,
        "kind": kind,
        "level": "info",
        "message": message,
        "payload": {},
    }


_PHASE_KEYWORDS: list[tuple[str, str]] = [
    ("ingest", "ingestion"),
    ("insight", "insight"),
    ("conflict", "conflict"),
    ("planner", "planning"),
    ("plan", "planning"),
    ("executor", "execution"),
    ("execute", "execution"),
    ("monitor", "monitoring"),
]


def _detect_phase(event: dict) -> str | None:
    text = (event.get("message", "") + " " + event.get("agent", "")).lower()
    for kw, phase in _PHASE_KEYWORDS:
        if kw in text:
            return phase
    return None


# ---------------------------------------------------------------------------
# Thread worker — runs synchronously inside ThreadPoolExecutor
# ---------------------------------------------------------------------------

def _run_pipeline_thread(
    run_id: str,
    seed_region: str,
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
    repo_root: Path,
):
    """
    Blocking function executed in a thread.  Uses subprocess.Popen to launch
    the pipeline and reads stdout+stderr line by line, forwarding to the queue.
    """

    def put(event: dict):
        """Thread-safe queue put."""
        loop.call_soon_threadsafe(queue.put_nowait, event)

    cmd = [sys.executable, "-u", "-m", "agents.run_pipeline",
           "--seed", seed_region, "--run-id", run_id]

    log.info("pipeline_thread_starting", run_id=run_id, cmd=" ".join(cmd))
    put(_synthetic(run_id, "Ingestion", "start", "started",
                   f"Pipeline starting | seed={seed_region}"))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(repo_root),
            text=False,          # binary mode; parse_line handles decoding
        )
        log.info("subprocess_spawned", run_id=run_id, pid=proc.pid)

        def drain(stream):
            for raw_line in stream:
                event = parse_line(raw_line, run_id)
                if event:
                    phase = _detect_phase(event)
                    if phase:
                        runs[run_id]["current_phase"] = phase
                    put(event)

        # Read stdout and stderr concurrently via two threads
        t_out = threading.Thread(target=drain, args=(proc.stdout,), daemon=True)
        t_err = threading.Thread(target=drain, args=(proc.stderr,), daemon=True)
        t_out.start()
        t_err.start()
        t_out.join()
        t_err.join()

        proc.wait()
        rc = proc.returncode

        if rc == 0:
            runs[run_id]["status"] = "completed"
            put(_synthetic(run_id, "Executor", "complete", "completed",
                           "Pipeline completed successfully."))
            log.info("pipeline_completed", run_id=run_id)
        else:
            runs[run_id]["status"] = "failed"
            put(_synthetic(run_id, "Executor", "error", "failed",
                           f"Pipeline exited with code {rc}."))
            log.error("pipeline_failed", run_id=run_id, return_code=rc)

    except Exception as exc:
        import traceback
        runs[run_id]["status"] = "failed"
        put(_synthetic(run_id, "Executor", "error", "failed",
                       f"Pipeline error: {exc}"))
        log.error("pipeline_exception", run_id=run_id,
                  error=str(exc), traceback=traceback.format_exc())

    finally:
        # Sentinel — tells WS endpoint the stream is done
        loop.call_soon_threadsafe(queue.put_nowait, None)


# ---------------------------------------------------------------------------
# Async entry point (called from FastAPI background task)
# ---------------------------------------------------------------------------

async def run_and_stream(run_id: str, seed_region: str):
    """
    Kick off the pipeline in a thread and return immediately.
    The thread writes events to the asyncio queue via call_soon_threadsafe.
    """
    queue = event_queues.setdefault(run_id, asyncio.Queue())
    loop = asyncio.get_event_loop()
    repo_root = Path(__file__).resolve().parent.parent.parent

    # Submit blocking work to thread pool — does NOT block the event loop
    loop.run_in_executor(
        _executor,
        _run_pipeline_thread,
        run_id, seed_region, queue, loop, repo_root,
    )
