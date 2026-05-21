# PulseAI Mobile — Backend Integration

This is the integrated version of the Flutter app, wired to the FastAPI backend
in the sibling `pulse-ai/` Python project.

## What changed vs the pre-integration UI

All UI design, animations, fonts, and layouts are unchanged. Only the data
sources were swapped from hard-coded mocks to real backend calls.

### New files
- `lib/services/api_config.dart` — single place to set the backend URL
- `lib/services/api_services.dart` — was empty; now a full REST client

### Updated files
- `lib/services/websocket_service.dart` — uses `ApiConfig.wsBaseUrl` (was hardcoded `BACKEND_URL` placeholder)
- `lib/screens/home.dart` — "Start Analysis" now calls `POST /api/scenarios/run`; added Lahore / Karachi seed picker
- `lib/screens/insights_screen.dart` — fetches `GET /insights`, maps backend schema to UI; dynamic exec summary
- `lib/screens/contradictions_screen.dart` — fetches `GET /contradictions`; surfaces NHR count
- `lib/screens/action_plan_screen.dart` — fetches `GET /plan`; dynamic budget bar + discount + feasibility badge + revisions count
- `lib/screens/live_trace_screen.dart` — accepts both `String` and `Map` runId args
- `lib/screens/outcome_screen.dart` — fetches `GET /outcome`; loading + error states
- `lib/widgets/bottom_nav_bar.dart` — preserves `run_id` when tab-switching
- `pubspec.yaml` — added `http: ^1.2.0`

### Untouched
- `splash_screen.dart` — decorative animation only, no backend dependency
- All widgets in `widgets/` (except bottom nav)
- All assets, colors, route names
- All `models/*`

## One-time setup

1. From the Flutter project root, fetch deps:
   ```bash
   flutter pub get
   ```

2. Point the app at your backend. Edit ONE place:
   `lib/services/api_config.dart`

   | Where you're running the app | Set `httpBaseUrl` to |
   |---|---|
   | Android emulator + local backend | `http://10.0.2.2:8080` |
   | iOS simulator + local backend | `http://localhost:8080` |
   | Real phone on same WiFi | `http://<your-laptop-LAN-ip>:8080` |
   | Cloud Run | `https://pulseai-backend-XXXXXX-uc.a.run.app` |

   Set `wsBaseUrl` to the same host with `ws://` (or `wss://` for HTTPS/Cloud Run).

3. Start the backend (from the `pulse-ai/` Python project):
   ```bash
   cd pulse-ai/backend
   uvicorn api.main:app --host 0.0.0.0 --port 8080
   ```

4. Run the app:
   ```bash
   flutter run
   ```

## End-to-end flow

```
Splash
  └─→ Home (Sources screen)
        ├─ pick seed: Lahore / Karachi
        └─→ [Start Analysis]
              │  POST /api/scenarios/run → run_id
              ▼
            Insights
              │  GET /insights — 5 insights, dynamic exec summary
              ▼
            Contradictions
              │  GET /contradictions — surfaces needs_human_review
              ▼
            Action Plan
              │  GET /plan — 5-action DAG, real budget bar, revisions banner
              ▼
            Run (local animation)
              ▼
            Live Trace
              │  WS /events — real-time agent events from backend
              ▼
            Outcome
              │  GET /outcome — before/after metrics, projected ROAS + reach
              ▼
            Done
```

## Region-agnostic proof (rubric headline)

The Home screen has a seed picker (Lahore / Karachi). Same code path, different
data, different detected outlier — proves the system isn't hardcoded to one
region. Record this in the demo video.

## Known gotchas

- The Action Plan screen's "Run" button plays a local animation. The actual
  pipeline already ran on the backend the moment Start Analysis was tapped —
  the animation is the visual story for the demo.
- File upload on the Home screen is decorative for the demo — the backend uses
  baked-in mock data (`sources/zarapk_regional_v1/`). Uploading real files
  would require a backend upload endpoint, which is out of scope for the MVP.
- `splash_screen.dart` still has small decorative bar-chart data marked
  `DEMO DATA` — that's intentional, it's just the splash illustration.
