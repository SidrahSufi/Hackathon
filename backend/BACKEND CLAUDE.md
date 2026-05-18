# BizPulse Backend — CLAUDE.md
# Google Antigravity Hackathon 2026 | Team Role: Backend/Integration

---

## YOUR JOB IN ONE SENTENCE

Build the FastAPI backend that sits between the Flutter app and the Python agents — expose REST endpoints + a WebSocket stream, wire the existing agent pipeline, mock all external services, and make sure the app can show live trace events in real time.

---

## CRITICAL CONTEXT: WHAT ALREADY EXISTS

The agent pipeline is **already built and working**. Do NOT touch or rewrite:

```
agents/ingestion/    ← done
agents/insight/      ← done
agents/conflict/     ← done
agents/planner/      ← done
agents/executor/     ← done
agents/monitor/      ← done
agents/run_pipeline.py  ← the orchestrator, runs everything end-to-end
```

Your job is to wrap `run_pipeline.py` in a FastAPI server. The agents write JSON state to `.state/{run_id}/` — you read those files and stream them to the app.

---

## PROJECT STRUCTURE (what you're building)

```
backend/
├── main.py               ← FastAPI app entry point
├── routers/
│   ├── scenarios.py      ← POST /run, GET /runs/:id, etc.
│   └── websocket.py      ← WS /runs/:id/events
├── services/
│   ├── runner.py         ← calls run_pipeline in a background thread
│   ├── state_reader.py   ← reads .state/{run_id}/*.json files
│   └── event_streamer.py ← tails structlog output → WebSocket events
├── mock_services/
│   ├── email.py          ← mock_send_email (prints + saves .eml)
│   ├── push.py           ← mock_send_push
│   ├── campaign.py       ← mock_launch_campaign
│   ├── pricing.py        ← mock_update_pricing
│   └── monitor.py        ← mock_schedule_monitor
├── schemas/
│   └── api.py            ← Pydantic models for request/response
├── requirements.txt
└── Dockerfile
```

---

## API CONTRACT (implement exactly this — Flutter app depends on it)

### REST Endpoints

```
POST /api/scenarios/run
  body: { "scenario_id": "zarapk_regional_v1", "seed_region": "lahore" }
  resp: { "run_id": "r-<uuid>", "status": "started" }

GET /api/scenarios/runs/:run_id
  resp: { run_id, status, current_phase, detected_region, created_at }

GET /api/scenarios/runs/:run_id/sources
  resp: { sources: [...] }     ← reads .state/{run_id}/ingestion.json

GET /api/scenarios/runs/:run_id/insights
  resp: { insights: [...] }    ← reads .state/{run_id}/insights.json

GET /api/scenarios/runs/:run_id/contradictions
  resp: { contradictions: [...] }  ← reads .state/{run_id}/contradictions.json

GET /api/scenarios/runs/:run_id/plan
  resp: { actions: [...] }     ← reads .state/{run_id}/plan.json

GET /api/scenarios/runs/:run_id/execution
  resp: { ... }                ← reads .state/{run_id}/execution_logs.json

GET /api/scenarios/runs/:run_id/outcome
  resp: { before: {...}, after: {...}, ... }  ← computed from state files

GET /api/scenarios/runs/:run_id/trace.zip
  resp: zip file of all state + logs for that run_id

WS  /api/scenarios/runs/:run_id/events
  streams: { ts, agent, phase, kind, payload, level }
```

### WebSocket Event Schema

Every event the Flutter app expects looks like this:

```json
{
  "ts": "10:42:07",
  "run_id": "r-001",
  "agent": "ConflictResolver",
  "phase": "resolve",
  "kind": "contradiction_resolved",
  "level": "info",
  "message": "2 resolved, 1 needs human review",
  "payload": {}
}
```

`kind` values the Flutter app uses to color things:
- `"completed"` → green
- `"started"` → blue
- `"failed"` → red
- `"retry"` → orange
- `"fallback"` → orange

`agent` values must match exactly (case-sensitive):
`"Ingestion"`, `"Insight"`, `"ConflictResolver"`, `"ActionPlanner"`, `"Executor"`, `"Monitor"`

---

## HOW THE PIPELINE RUNS (your most important job)

When POST /api/scenarios/run is called:

1. Generate a `run_id` (e.g. `f"r-{uuid4().hex[:8]}"`)
2. Store run metadata in memory (dict) — no DB needed for demo
3. Kick off `run_pipeline.main()` (or subprocess) in a **background thread/task**
4. Return `{ run_id, status: "started" }` immediately
5. As the pipeline runs, it writes `.state/{run_id}/*.json` files
6. Your WebSocket endpoint tails those files + the agent logs and streams events

### How to stream events

The agents use `structlog` which outputs JSON lines to stderr/stdout. Capture that output as the pipeline runs and forward it to connected WebSocket clients. Simplest approach:

```python
import subprocess, json, asyncio

async def run_and_stream(run_id, seed_region, ws_clients):
    proc = await asyncio.create_subprocess_exec(
        "python", "-m", "agents.run_pipeline",
        "--seed", seed_region, "--run-id", run_id,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    async for line in proc.stderr:
        try:
            event = json.loads(line)
            # normalize to WS schema
            ws_event = normalize_event(event, run_id)
            for client in ws_clients[run_id]:
                await client.send_json(ws_event)
        except json.JSONDecodeError:
            pass
    await proc.wait()
```

---

## STATE FILES — what each contains

After `run_pipeline` finishes, these files exist at `.state/{run_id}/`:

| File | Contains |
|------|----------|
| `ingestion.json` | `IngestionResult` — signals[], sources_processed, discarded_summary |
| `insights.json` | `InsightResult` — detected_outlier_region, insights[] |
| `contradictions.json` | `ConflictResult` — contradictions[], not_a_conflict_log[] |
| `plan.json` | `ActionChain` — plan_id, target_region, actions[] |
| `execution_logs.json` | `ExecutionResult` — final_status, completed_steps, rollback_triggered |

Read them with `json.loads(Path(f".state/{run_id}/{filename}").read_text())`

---

## MOCK SERVICES (implement all 5)

The Executor calls these. They should print to logs + save a file so we can show "simulated execution" to judges. **No real outgoing requests.**

```python
# mock_services/email.py
def mock_send_email(to: str, subject: str, body: str, run_id: str) -> dict:
    eml_path = Path(f".state/{run_id}/email_{to}.eml")
    eml_path.write_text(f"To: {to}\nSubject: {subject}\n\n{body}")
    log.info("mock_email_sent", to=to, subject=subject)
    return {"status": "sent", "message_id": f"mock-{uuid4().hex[:8]}"}

# mock_services/campaign.py  
def mock_launch_campaign(region: str, segment: str, discount_pct: int, run_id: str) -> dict:
    # Simulate A4 notification failure for demo drama
    # Executor handles retry → fallback
    log.info("mock_campaign_launched", region=region, discount_pct=discount_pct)
    return {"campaign_id": f"camp_{region.lower()}_{uuid4().hex[:4]}", "status": "active"}
```

The A4 notification failure demo: in `executor/agent.py` there's already a `raise RuntimeError("Simulated external API execution failure on A4.")` — don't touch it. The Executor already handles retry/rollback.

---

## OUTCOME ENDPOINT — how to compute it

The `/outcome` endpoint needs to return before/after metrics. Compute from state files:

```python
def compute_outcome(run_id: str) -> dict:
    insights = load_json(run_id, "insights.json")
    execution = load_json(run_id, "execution_logs.json")
    plan = load_json(run_id, "plan.json")
    
    outlier = insights.get("detected_outlier_region", "Unknown")
    
    # Find I1 (orders decline insight) for before metric
    i1 = next((i for i in insights["insights"] if i["insight_id"] == "I1"), {})
    orders_before = 142  # from I1 metrics if available
    
    # Compute campaign cost from plan
    campaign_cost = sum(
        a["cost_pkr"] for a in plan.get("actions", [])
    )
    
    return {
        "detected_region": outlier,
        "orders_per_day_before": orders_before,
        "orders_per_day_after": 186,  # projected
        "projected_reach": 5200,
        "revenue_at_risk_pkr": 1400000,
        "revenue_recovered_pkr": 990000,
        "campaign_cost_pkr": campaign_cost,
        "roas": 2.8,
        "chain_latency_s": 4.9,
        "other_regions_status": "All 5 other regions unchanged",
        "execution_status": execution.get("final_status", "UNKNOWN"),
        "rollback_triggered": execution.get("rollback_triggered", False),
    }
```

---

## RUN HISTORY (in-memory is fine for demo)

```python
# In main.py or a simple store
runs: dict[str, dict] = {}

# When run starts:
runs[run_id] = {
    "run_id": run_id,
    "status": "running",
    "current_phase": "ingestion",
    "seed_region": seed_region,
    "detected_region": None,
    "created_at": datetime.utcnow().isoformat(),
}

# Update as pipeline progresses (from WS events)
# When done: runs[run_id]["status"] = "completed"
```

No Firestore needed for the demo — in-memory dict is fine.

---

## CORS (REQUIRED — Flutter needs this)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## WEBSOCKET HUB PATTERN

```python
# One dict to track connected clients per run_id
ws_clients: dict[str, list[WebSocket]] = {}

@app.websocket("/api/scenarios/runs/{run_id}/events")
async def ws_events(websocket: WebSocket, run_id: str):
    await websocket.accept()
    ws_clients.setdefault(run_id, []).append(websocket)
    try:
        # Send any already-finished events from state files
        await send_historical_events(websocket, run_id)
        # Then keep alive until run completes
        while True:
            await asyncio.sleep(1)
            if runs.get(run_id, {}).get("status") == "completed":
                await websocket.send_json({"kind": "completed", "agent": "Executor"})
                break
    except WebSocketDisconnect:
        ws_clients[run_id].remove(websocket)
```

---

## TRACE.ZIP ENDPOINT

```python
import zipfile, io

@router.get("/runs/{run_id}/trace.zip")
def download_trace(run_id: str):
    state_dir = Path(f".state/{run_id}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for f in state_dir.glob("*.json"):
            zf.write(f, f.name)
        for f in state_dir.glob("*.eml"):
            zf.write(f, f.name)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=trace_{run_id}.zip"}
    )
```

---

## REQUIREMENTS.TXT

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic>=2.7
structlog>=24.1
python-multipart==0.0.9
websockets==12.0
```

The agents' deps (pandas, pypdf, etc.) are in the repo's `pyproject.toml` already.

---

## HOW TO RUN LOCALLY

```bash
# From repo root
pip install -e ".[dev]"
pip install fastapi uvicorn[standard]

# Start server
uvicorn backend.main:app --reload --port 8000

# Test it
curl -X POST http://localhost:8000/api/scenarios/run \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "zarapk_regional_v1", "seed_region": "lahore"}'
```

---

## RULES — DO NOT BREAK THESE

1. **Never modify agent code** — only call it, never change it
2. **State files are the source of truth** — read `.state/{run_id}/*.json` for all GET endpoints
3. **Mock services only** — zero real external HTTP calls
4. **The run_id must match** — agents write to `.state/{run_id}/`, your WebSocket listens on `runs/{run_id}/events`
5. **agent names in WS events must match exactly** — `"ConflictResolver"` not `"conflict_resolver"`
6. **CORS must be open** — Flutter on Android emulator needs it
7. **Background execution** — POST /run returns instantly, pipeline runs async

---

## WHAT CONNECTS WHERE (Flutter → Backend → Agents)

```
Flutter app
  └─ POST /api/scenarios/run  →  FastAPI  →  background task
                                              └─ subprocess: python -m agents.run_pipeline
                                                 └─ writes .state/{run_id}/*.json

Flutter app
  └─ WS /api/scenarios/runs/{run_id}/events
       ↑
       FastAPI WS hub ← tails subprocess stderr (structlog JSON lines)

Flutter app
  └─ GET /api/scenarios/runs/{run_id}/insights
       ↑
       FastAPI reads .state/{run_id}/insights.json → returns it
```

---

## PRIORITY ORDER (do these first, in order)

**Day 1 (do this NOW, before loadshedding hits):**
1. `backend/main.py` — FastAPI app skeleton with CORS
2. `POST /api/scenarios/run` — generates run_id, kicks off subprocess, returns immediately
3. `WS /api/scenarios/runs/:id/events` — streams subprocess stderr as JSON events
4. Test: run a scenario, verify Flutter Live Trace screen gets events

**Day 2:**
5. All GET endpoints — read state files, return JSON
6. `/outcome` endpoint with computed metrics
7. Mock services (email, push, campaign, pricing)

**Day 3:**
8. `/trace.zip` download
9. CORS + deployment prep (Dockerfile)
10. Test with Flutter pointing at real backend

**Only if Day 3 finishes early:**
11. Firestore persistence (replace in-memory dict)
12. Run history endpoint (list of recent runs)

---

## DEBUGGING TIPS

- If pipeline fails: check `.state/{run_id}/` for partial files
- If WS events don't reach Flutter: check CORS, check event schema matches exactly
- If `run_pipeline` import fails: run from repo root with `python -m agents.run_pipeline`
- Agents expect `sources/zarapk_regional_v1/{seed}/` to exist — if not, they auto-generate it

---

## DEMO SCRIPT (know this — judges will ask)

1. POST /run with `seed_region: "lahore"` → run_id back
2. Flutter connects WS → sees live agent trace events streaming
3. Ingestion: 6 sources parsed, 2 discarded (spam + blog)
4. Insight: Lahore flagged as -25% outlier
5. Conflict: C1 resolved (POS > PDF), C3 needs human review
6. Planner: 5-action chain generated
7. Executor: A1-A3 succeed, A4 fails → retry → fallback, A5 schedules monitor
8. Flutter Outcome screen shows before/after metrics
9. Swap seed to `"karachi"` → same system finds different outlier (proves region-agnostic)

---

## QUICK REFERENCE: KEY FILES YOU'LL TOUCH

```
backend/main.py           ← you create this
backend/routers/          ← you create this
agents/run_pipeline.py    ← you call this, never edit
.state/{run_id}/*.json    ← agents write, you read
config/policies.yaml      ← PolicyChecker reads this (don't touch)
.agents/skills/api-contract.md  ← your contract (read it)
```

---

*Last updated: May 2026 | Hackathon deadline: May 20*