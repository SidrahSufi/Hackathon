<div align="center">

# 🎯 PulseAI

### Autonomous Content-to-Action Agent

*Multi-region operations co-pilot — finds the problem, plans the fix, executes it.*

<br />

![AISeekho 2026](https://img.shields.io/badge/AISeekho-2026-7B2CBF?style=for-the-badge&labelColor=2D1B4E)
![Challenge 1](https://img.shields.io/badge/Challenge-1-FF6B35?style=for-the-badge&labelColor=2D1B4E)
![Business Insights](https://img.shields.io/badge/Domain-Business%20Insights-06A77D?style=for-the-badge&labelColor=2D1B4E)
![Tests](https://img.shields.io/badge/tests-65%20passing-22c55e?style=for-the-badge&logo=pytest&logoColor=white&labelColor=2D1B4E)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Google ADK](https://img.shields.io/badge/Google_ADK-Agents-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Cloud Run](https://img.shields.io/badge/Cloud_Run-Deployed-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)
![Built with Antigravity](https://img.shields.io/badge/Built_with-Antigravity-FF6B00?style=for-the-badge&logo=google&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

</div>

---

## 🎬 Demo Video

<div align="center">

<!--
  📹 PASTE YOUR DEMO LINK HERE
  Three options for embedding — pick whichever you use:
  
  Option A — YouTube unlisted (RECOMMENDED): replace the URL below
  Option B — Google Drive: paste a sharable preview link
  Option C — Loom or other host: paste the share URL
-->

[![PulseAI Demo](https://img.shields.io/badge/▶_Watch_Demo-3_minutes-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE)

**🔗 Demo URL:** _https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE_

</div>

> 💡 **What the video shows:** Live run of the full 6-stage pipeline against the ZaraPK scenario.
> Mid-video the seed is swapped from Lahore → Karachi to prove the system isn't hardcoded to one
> region. Includes the live notification-API failure + automatic recovery moment, the
> needs-human-review contradiction handling, and the final outcome dashboard.

---

## About

**PulseAI is an autonomous operations co-pilot for multi-region retail brands.** Plug in your
sales, marketing, analytics, and customer-feedback signals from every region you operate in —
PulseAI ingests the mess, finds the underperforming region, diagnoses the root cause, plans a
targeted response, and executes the full action chain end-to-end. Constraint checking,
contradiction handling between conflicting sources, and graceful failure recovery are built in.

The system is **region-agnostic by design** — the same code that flags Lahore today will flag
Karachi tomorrow if that's where the numbers say to look. No hardcoded answers; the detection
emerges from the data.

**Demo scenario:** ZaraPK Regional Sales Anomaly → Region-targeted Discount Campaign.
PulseAI ingests multi-type signals across all 6 regions, detects the outlier, resolves
contradictions, plans a connected action chain, executes it (with retry/fallback/rollback),
and projects the outcome.

---

## 📐 Architecture Overview

PulseAI is a three-layer system: a mobile app (built by teammates), a FastAPI backend on Cloud
Run, and a six-stage agent pipeline. Each stage is single-purpose and writes its output as JSON
to a shared `.state/<run_id>/` directory. The backend tails that directory and pushes live
WebSocket events to the mobile app, so the UI shows agent progress in real time.

```
┌────────────────────────────────────────────────────────────────────┐
│              Mobile App (Flutter) — separate component             │
│   Home · Sources · Insights · Contradictions · Plan · Live · Outcome
└──────────────────────────┬─────────────────────────────────────────┘
                           │  REST + WebSocket
┌──────────────────────────▼─────────────────────────────────────────┐
│        Backend  (FastAPI · Cloud Run · Docker · WebSocket hub)     │
│                                                                    │
│  POST  /api/scenarios/run              → kick off a pipeline run   │
│  GET   /api/scenarios/runs/{id}        → status + current phase    │
│  GET   /api/scenarios/runs/{id}/{rsc}  → per-stage JSON output     │
│  GET   /api/scenarios/runs/{id}/trace.zip → download whole bundle  │
│  WS    /api/scenarios/runs/{id}/events → live agent events stream  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │  background thread
┌──────────────────────────▼─────────────────────────────────────────┐
│              6-Stage Agent Pipeline (Google ADK + Python)          │
│                                                                    │
│  ┌──────────┐  ┌─────────┐  ┌────────────┐  ┌─────────┐            │
│  │Ingestion │→ │ Insight │→ │ Conflict   │→ │ Planner │→           │
│  │   (1)    │  │   (2)   │  │ Resolver   │  │   (4)   │            │
│  └──────────┘  └─────────┘  │   (3)      │  └────┬────┘            │
│                              └────────────┘       │                 │
│                              ┌──────────┐  ┌──────▼─────┐          │
│                              │ Monitor  │← │ Executor   │          │
│                              │   (6)    │  │   (5)      │          │
│                              └──────────┘  └────────────┘          │
│                                     │                              │
│                              ┌──────▼─────────┐                    │
│                              │   Outcome      │                    │
│                              │  Computation   │                    │
│                              └────────────────┘                    │
│                                                                    │
│  Each stage writes .state/<run_id>/<stage>.json — file appearance   │
│  triggers a WebSocket "resource_ready" event to subscribed clients. │
└────────────────────────────────────────────────────────────────────┘
```

### Design principles

| Principle | How it's enforced |
|---|---|
| **No invented numbers** | All math (percentages, comparisons, clustering, projections) is in pure Python. LLMs only orchestrate and write rationale text. Tests assert that metric values trace to a computed function. |
| **No forced decisions** | When two sources are equally credible AND equally recent, the ConflictResolver flags `needs_human_review` rather than picking. A property test enforces this. |
| **Constraints are first-class** | Every action goes through `PolicyChecker.check()` before execution. The check is pure Python. Violations get suggested revisions; if a revision can't fix it, the action is skipped, not silently dropped. |
| **Failures are normal** | A4's notification API is wired to fail on first call. The Executor retries with batching, falls back to in-app banner, and would rollback prior actions if the chain couldn't recover. |
| **Region-agnostic** | The detected region comes from cross-region temporal analysis on the POS CSV. Swap the seed file, get a different answer with zero code changes. |
| **Built inside Antigravity** | Custom skills in `.agents/skills/`, plan/implementation artifacts in `docs/antigravity-traces/`, manager screenshots showing parallel scaffolding agents. |

---

## 🤖 Agents Developed

Six purpose-built agents, each owning one phase. All agents share schemas via pydantic v2 and
share state via `.state/<run_id>/*.json` files.

### 1. Ingestion Agent (`agents/ingestion/`)

**Input:** raw files in `sources/zarapk_regional_v1/<seed_region>/`
**Output:** `.state/<run_id>/ingestion.json` — list of `Signal` records.

Reads 8 source files (PDF, CSV, JSON, JSONL, HTML × 2, social JSON × 2), normalizes each into a
typed `Signal` record, scores credibility (0.0–1.0) and recency (0.0–1.0), and applies a noise
filter that discards low-credibility-no-corroboration and obvious-spam sources.

**Key tools:** `parse_pdf`, `parse_csv`, `parse_html`, `parse_json`, `parse_jsonl`,
`score_credibility`, `score_recency`, `is_spam`.

### 2. Insight Agent (`agents/insight/`)

**Input:** `ingestion.json`
**Output:** `insights.json` — 5 ranked `Insight` records + `detected_outlier_region`.

Runs cross-region temporal analysis on the POS CSV to detect the outlier region (last 15 days
vs prior 15 days, against a ±5% noise band). For the outlier, clusters support tickets to find
the affected segment, cross-checks analytics for reach drops, parses news articles for
competitor entities, and aligns competitor expansion dates with the decline start. Produces
exactly 5 insights with severity, confidence, evidence references, and computed metrics.

**Key module:** `agents/insight/temporal.py` contains all the math. **The LLM never computes
a percentage** — tests assert this.

### 3. ConflictResolver Agent (`agents/conflict/`)

**Input:** `ingestion.json` + `insights.json`
**Output:** `contradictions.json` — resolved or escalated contradictions.

Finds source pairs that report the same metric with different values. For each pair, decides:
- `resolved` — picks a winner using a deterministic recency-then-credibility rule
- `not_a_conflict` — surfaces "both true but different angles" (e.g. full budget + low reach is
  a campaign issue, not a contradiction). Logged separately, not in the contradictions list.
- `needs_human_review` — equally credible AND equally recent. Must NOT pick a side.

**Property:** the competitor-pricing conflict (credible news vs anonymous blog) always ends up
as `needs_human_review`. Tests enforce this across 100 random pairs.

### 4. Action Planner Agent (`agents/planner/`)

**Input:** `insights.json`
**Output:** `plan.json` — 5-action DAG targeting the detected region.

Builds the canonical 5-action chain (Diagnose → Notify → Launch Campaign → Update Pricing →
Schedule Monitor). Pipes every action through `PolicyChecker` and applies any suggested
revisions before publishing the plan. The demo run starts with a 25% discount in A3 and the
PolicyChecker silently revises it to 20% to fit the discount cap — the revision is logged in
`revisions_applied`.

**Output guarantees:** every action has a `tool` name in the mock registry, `preconditions`
form a valid DAG, `total_cost_pkr` ≤ budget cap, `total_projected_reach` ≥ 5,000.

### 5. Executor Agent (`agents/executor/`)

**Input:** `plan.json`
**Output:** `execution.json` — per-step status + cumulative metrics.

Runs the action chain step by step. For each action:
1. Re-checks the action with `PolicyChecker` against the live counters.
2. Calls the action's tool from `agents/tools/mocks.py`.
3. On failure: retry once with smaller batch — succeed if possible, else fallback to a paired
   tool (e.g. notification → in-app banner).
4. On final failure: runs `compensating_action` for every previously successful step in reverse
   (rollback chain).

Records every tool call with args summary, result summary, latency, and timestamp. Step status
is one of: `success | failed_then_recovered | failed_then_rolled_back | skipped`.

### 6. Monitor Agent (`agents/monitor/`)

**Input:** `execution.json` + `plan.json`
**Output:** `monitor.json` — 7-day ROAS series + auto-pause status.

Simulates 7 days of post-launch campaign performance, compressed into ~0.5 seconds for the demo.
If any simulated day's ROAS drops below 1.5, calls `mock_pause_campaign` and records the pause
day. The demo seed produces a healthy curve; passing a `r-bad-*` run_id triggers a declining
series for the failure-path test.

### + Outcome Computation (`agents/outcome/compute.py`)

Final stage. Reads all upstream artifacts and produces `outcome.json` with the before/after
metrics the mobile app's Outcome screen consumes: orders/day 14-day average, projected 7-day
uplift, 30-day revenue at risk vs recovery projection, campaign cost, projected ROAS, chain
latency, and notes flagging anything that required human review.

Projections are grounded in observed POS data — the uplift model uses a linear elasticity
approximation against the actual prior-window revenue, not a hand-waved number.

---

## 🔌 APIs and Integrations

### REST API (FastAPI, backend/api/routes/scenarios.py)

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/healthz` | Cloud Run liveness probe |
| `POST` | `/api/scenarios/run` | Start a new pipeline run; returns `run_id` |
| `GET`  | `/api/scenarios/runs` | List recent runs |
| `GET`  | `/api/scenarios/runs/{run_id}` | Status, current phase, available resources |
| `DEL`  | `/api/scenarios/runs/{run_id}` | Remove `.state/<run_id>/` directory |
| `GET`  | `/api/scenarios/runs/{run_id}/sources` | Ingestion output JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/insights` | Insight output JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/contradictions` | ConflictResolver output JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/plan` | Action plan JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/execution` | Execution result JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/monitor` | 7-day monitor result JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/outcome` | Before/after metrics JSON |
| `GET`  | `/api/scenarios/runs/{run_id}/trace.zip` | Bundled zip of all state files + metadata |

Sub-resource endpoints return **202 Accepted** with `{"status": "not_ready", "current_phase": ...}`
when the file doesn't exist yet, and **200** with the full JSON once written.

### WebSocket (backend/api/ws/)

```
WS  /api/scenarios/runs/{run_id}/events
```

Client subscribes by run_id. Server pushes events keyed by file appearance in `.state/`. Event
shape:

```json
{
  "ts": "2026-05-20T10:42:07Z",
  "run_id": "r-...",
  "agent": "insight",
  "phase": "phase_complete",
  "kind": "resource_ready",
  "level": "info",
  "payload": { "resource": "insights",
               "summary": {"detected_outlier_region": "Lahore", "count": 5} }
}
```

The mobile app's "Live Run" screen renders these as a timeline.

### Mock external services (`agents/tools/mocks.py`)

Ten mock external services the Executor calls — they mirror real-world counterparts but return
deterministic results so the demo is reproducible:

| Mock tool | Stands in for | Used by |
|---|---|---|
| `mock_segment_breakdown` | analytics product (Mixpanel, Amplitude) | A1 |
| `mock_send_email` | SendGrid / SES | A2 |
| `mock_send_push` | FCM / OneSignal | A2 fallback |
| `mock_launch_campaign` | Google Ads / Meta Ads | A3 |
| `mock_pause_campaign` | same — compensating action | A3 rollback |
| `mock_update_pricing` | Shopify / commerce backend | A4 |
| `mock_revert_pricing` | same — compensating action | A4 rollback |
| `mock_draft_notification` | customer messaging API (Braze, Klaviyo) | A4 side-effect — **has built-in failure injection** |
| `mock_in_app_banner` | in-app messaging SDK | A4 fallback |
| `mock_schedule_monitor` | internal cron / Cloud Scheduler | A5 |

`mock_draft_notification` fails on the first call deliberately. The retry path with batching
succeeds, demonstrating live failure recovery in every demo run. Real production would swap
these for the actual APIs without changing the agent code.

### Real integrations used in development

- **Google ADK** — agent framework (`google.adk.agents.LlmAgent`)
- **Google Gemini (planned)** — referenced in agent definitions, MVP runs without LLM calls so
  the demo is quota-free and deterministic
- **Google Cloud Build** — CI/CD via `backend/cloudbuild.yaml`
- **Google Cloud Run** — production deployment target
- **Google Antigravity** — entire development environment (planning, scaffolding, testing,
  recovery traces, knowledge base, browser sub-agent verification)

---

## 🔗 Integration: how everything fits together

```
[User taps "Run" in mobile app]
        │
        ▼
[Mobile app]  ── POST /api/scenarios/run ──►  [Backend (Cloud Run)]
                                                       │
                                                       │ spawns daemon thread
                                                       ▼
                                              [Agent pipeline]
                                                       │ writes
                                                       ▼
                                              .state/<run_id>/ingestion.json
                                              .state/<run_id>/insights.json
                                              .state/<run_id>/contradictions.json
                                              .state/<run_id>/plan.json
                                              .state/<run_id>/execution.json
                                              .state/<run_id>/monitor.json
                                              .state/<run_id>/outcome.json
                                                       ▲
                                                       │ tails directory
                                              [WebSocket hub]
                                                       │ broadcasts
                                                       ▼
[Mobile app]  ◄─ WS /api/scenarios/runs/{id}/events ─  [Backend]
        │
        │ renders live timeline, then fetches each
        │ resource via GET as it becomes ready
        ▼
[User sees: Sources tab → Insights tab → Contradictions tab → Plan → Live trace → Outcome]
```

The mobile app and backend stay decoupled — the backend doesn't push UI state, just events.
The mobile app decides what to render. The same backend API can drive the planned web app
without changes.

---

## 🚀 Run locally (30 seconds)

```bash
# 1. Install
python3.11 -m venv .venv
source .venv/bin/activate     # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .              # installs the `agents` package
pip install -e backend        # installs the FastAPI backend

# 2. Run the pipeline from the CLI
python -m agents.run_pipeline --seed lahore --run-id r-demo-1
python -m agents.run_pipeline --seed karachi --run-id r-demo-2

# 3. Or boot the API
cd backend
uvicorn api.main:app --reload --port 8080
```

API smoke test:

```bash
curl -X POST http://localhost:8080/api/scenarios/run \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"zarapk_regional_v1","seed_region":"lahore"}'

curl http://localhost:8080/api/scenarios/runs/<run_id>/outcome
```

---

## 📱 Run the mobile app

```bash
cd mobile
flutter pub get

# Point the app at your backend - edit ONE line in:
# lib/services/api_config.dart
#   - Android emulator + local backend:  http://10.0.2.2:8080
#   - iOS simulator + local backend:     http://localhost:8080
#   - Real phone on same WiFi:           http://<your-laptop-LAN-ip>:8080
#   - Cloud Run:                         https://pulseai-backend-XXXXXX-uc.a.run.app

flutter run            # on a connected device or emulator
flutter build apk      # produces an APK to share
flutter build web      # produces a static web build under build/web
```

See `mobile/INTEGRATION_NOTES.md` for a full diagram of which screen calls
which backend endpoint, and which files were changed during integration.

### Host the web build on Firebase Hosting

```bash
npm install -g firebase-tools
firebase login
cd mobile
firebase init hosting    # use existing GCP project; public dir = build/web; SPA = yes
flutter build web --release
firebase deploy --only hosting
```

Output prints a URL like `https://pulseai-aiseekho-2026.web.app` — paste it
in the demo section above.

---

## ☁️ Deploy backend to Cloud Run

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# From the repo root:
gcloud builds submit --config backend/cloudbuild.yaml
```

The full URL is printed at the end. Smoke-test it:

```bash
curl https://pulseai-backend-XXXXX-uc.a.run.app/healthz
```

---

## 🧪 Tests

```bash
pytest tests/ backend/tests/ -v
# 65 tests, ~17 seconds
```

| Test file | What it covers |
|---|---|
| `tests/test_temporal.py` | Outlier detection math, both seeds, flat-data case |
| `tests/test_ingestion_agent.py` | Parsing per type, credibility scoring, spam filter |
| `tests/test_insight_agent.py` | 5 insights, region-agnostic, **no invented numbers** |
| `tests/test_conflict_agent.py` | C1 resolved, C2 not-a-conflict, C3 needs human review |
| `tests/test_policy_checker.py` | Budget, discount, window, rate-limit enforcement |
| `tests/test_planner.py` | 5 actions, discount revision applied, no-outlier returns empty |
| `tests/test_executor.py` | A4 notification recovery, cost accounting, latency |
| `tests/test_monitor_outcome.py` | 7-day sim, auto-pause path, outcome fields, reach ≥ 5000 |
| `tests/test_full_pipeline.py` | E2E both seeds, region-agnostic property |
| `backend/tests/test_api.py` | Every REST endpoint, trace.zip, DELETE, 202 handling |
| `backend/tests/test_trace_packer.py` | Zip contents, missing-run error path |

---

## 📁 Repository Layout

```
pulse-ai/
├── .agents/skills/              ← Antigravity custom skills (3 files)
├── agents/                       ← 6 agents + mock tools + pipeline runner
│   ├── ingestion/                  ingestion agent
│   ├── insight/                    insight + temporal.py (the math)
│   ├── conflict/                   conflict resolver
│   ├── planner/                    action planner
│   ├── executor/                   executor with retry/fallback/rollback
│   ├── monitor/                    7-day monitor simulator
│   ├── outcome/                    before/after computation
│   ├── common/policy.py            PolicyChecker (constraints)
│   ├── tools/mocks.py              10 mock external services
│   ├── gen_mock_data.py            deterministic data generator
│   └── run_pipeline.py             end-to-end CLI entry point
├── backend/                      ← FastAPI + Cloud Run deploy
│   ├── api/main.py                 FastAPI app
│   ├── api/routes/scenarios.py     all REST endpoints + WebSocket
│   ├── api/routes/health.py        /healthz
│   ├── api/ws/hub.py               WebSocket connection manager
│   ├── api/ws/tailer.py            .state directory watcher
│   ├── api/pipeline_runner.py      background thread launcher
│   ├── api/trace_packer.py         trace.zip builder
│   ├── Dockerfile                  multi-stage image
│   ├── cloudbuild.yaml             gcloud builds submit config
│   └── tests/                      backend API tests
├── mobile/                       ← Flutter app (Android + iOS + Web)
│   ├── lib/screens/                7 screens (splash, home, insights,
│   │                                contradictions, action plan, live trace,
│   │                                outcome)
│   ├── lib/services/api_config.dart    backend URL config (edit one place)
│   ├── lib/services/api_services.dart  REST client to FastAPI
│   ├── lib/services/websocket_service.dart  live agent event stream
│   ├── lib/widgets/                reusable cards + nav
│   ├── INTEGRATION_NOTES.md        how mobile connects to backend
│   └── pubspec.yaml                Flutter deps
├── config/policies.yaml          ← all constraint thresholds
├── sources/zarapk_regional_v1/   ← 8 mock files × 2 seeds (lahore, karachi)
├── tests/                        ← agent-level tests
├── docs/
│   ├── antigravity-traces/         screenshots + plan artifacts
│   └── artifacts/                  implementation plans (markdown)
├── README.md                     ← this file
└── pyproject.toml                ← agents package definition
```

---

## 📊 Data Sources

All under `sources/zarapk_regional_v1/<region>/`:

| # | Type | File | Role in scenario |
|---|---|---|---|
| 1 | PDF | `monthly_regional_sales.pdf` | Stale (30d old) — claims outlier region is +5% YoY (the trap) |
| 2 | CSV | `pos_ecom_last_30d.csv` | Fresh — the ground truth (outlier −14% to −25%) |
| 3 | HTML | `news_competitor_expansion.html` | Credible (Reuters byline) — competitor opened 3 stores |
| 4 | JSON | `analytics_by_region.json` | Reach in outlier region dropped 40% |
| 5 | JSONL | `support_tickets.jsonl` | Pricing complaints concentrated in outlier region |
| 6 | JSON | `marketing_spend.json` | Highest spend in outlier region (campaign silently broken) |
| 7 | HTML | `news_pricing_blog.html` | **Throw-in:** anonymous low-credibility blog, gets filtered |
| 8 | JSON | `social_post_spam.json` | **Throw-in:** obvious spam, gets filtered |

---

## ⚙️ Action Chain & Constraints

| ID | Action | Tool | Cost | Latency | Compensating |
|---|---|---|---|---|---|
| A1 | Diagnose affected SKUs + segments | `mock_segment_breakdown` | 0 | 30s | — |
| A2 | Notify regional sales + marketing | `mock_send_email` | 0 | 5s | — |
| A3 | Launch discount campaign | `mock_launch_campaign` | 720,000 PKR | 12s | `mock_pause_campaign` |
| A4 | Update pricing + draft notifications | `mock_update_pricing` + `mock_draft_notification` | 0 | 120s | `mock_revert_pricing` |
| A5 | Schedule 7-day monitor | `mock_schedule_monitor` | 0 | 1s | — |

Constraints (`config/policies.yaml`):

- Budget cap: **800,000 PKR**
- Discount cap: **20%** (margin floor 18%)
- Notification window: **09:00–21:00 Asia/Karachi**
- Rate limit: 5,000 notifications / hour
- Rate limit: 1 campaign / region / week

---

## 🛠️ Built with Google Antigravity

The entire project was developed inside **Google Antigravity** — see `docs/antigravity-traces/`:

| Artifact | What it shows |
|---|---|
| `00-antigravity-empty-workspace.png` | First-time setup |
| `01-manager-empty.png` | Agent Manager view |
| `02-skills-folder.png` | Custom skills registered (`.agents/skills/`) |
| `03-mock-data-plan.png` | Plan artifact for the data generator |
| `04-ingestion-recovery.png` | Agent recovers from a test failure |
| `05-insight-recovery.png` | Same, on the Insight Agent |
| `06-conflict-tests-passing.png` | Final ConflictResolver tests green |
| `07-planner-agent-execution.png` | Creation of Planner Agent |
| `08-executor-rollback.png` | Creation of Executor Agent |
| `09-monitor-agent-lifecycle.png` | Creation of Monitor Agent |
| `10-action-plan-screen.png` | S5 Action Plan screen — initial build |
| `11-action-screen-completion.png` | S5 Action Plan — Antigravity marks complete |
| `12-action-screen-bottom-nav-fix.png` | S5 — bottom nav bug fixed by Antigravity |
| `13-live-trace-screen.png` | S6 Live Trace — initial build |
| `14-live-trace-fix.png` | S6 — unused import lint fix |
| `15-action-screen-nav-fix.png` | S5 — Home tab routing bug fixed |
| `16-live-trace-nav-fix.png` | S6 — navigation bug fixed by Antigravity |
| `17-current-problem-fix.png` | S6 — build compilation failures resolved |

Plus implementation plan markdown files in `docs/artifacts/`.

---

## ⚠️ Limitations

- Mobile app built using Flutter
- LLM-callable tool definitions exist for all agents, but the MVP run path is **pure Python**
  for determinism and zero LLM quota dependency. Switching on LLM rationale generation is a
  one-line change in each agent.
- Monitor's 7-day simulation is compressed to ~0.5 seconds for demo purposes.
- Backend state persistence is file-based (`.state/<run_id>/`); production would back this with
  Firestore so multiple Cloud Run instances could share state.

---

## 📜 License

MIT — submitted for AISeekho 2026.
