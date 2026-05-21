"""Backend API tests — using FastAPI TestClient."""
from __future__ import annotations

import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make sure both packages are importable
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from api.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def _wait_for(client, run_id: str, resource: str, timeout: float = 60.0) -> None:
    """Poll until a resource is ready AND the run is marked completed."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/scenarios/runs/{run_id}/{resource}")
        if r.status_code == 200:
            # also wait for the run state to flip to completed
            s = client.get(f"/api/scenarios/runs/{run_id}").json()
            if s.get("status") in ("completed", "failed"):
                return
        time.sleep(0.3)
    raise TimeoutError(f"resource {resource} not ready in {timeout}s")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_healthz_returns_ok(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "0.1.0"}


def test_root_returns_endpoint_listing(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "PulseAI Backend"
    assert "endpoints" in body


# ---------------------------------------------------------------------------
# POST run + status
# ---------------------------------------------------------------------------

def test_post_run_returns_run_id(client):
    r = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "zarapk_regional_v1", "seed_region": "lahore"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "started"
    assert body["run_id"].startswith("r-")


def test_status_404_for_unknown_run(client):
    r = client.get("/api/scenarios/runs/r-nonexistent-99")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Full run — end-to-end including outcome
# ---------------------------------------------------------------------------

def test_full_lahore_run(client):
    r = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "zarapk_regional_v1", "seed_region": "lahore"},
    )
    run_id = r.json()["run_id"]

    _wait_for(client, run_id, "outcome", timeout=60.0)

    status = client.get(f"/api/scenarios/runs/{run_id}").json()
    assert status["status"] == "completed"
    assert status["detected_region"] == "Lahore"
    assert "outcome" in status["available_resources"]

    outcome = client.get(f"/api/scenarios/runs/{run_id}/outcome").json()
    assert outcome["detected_region"] == "Lahore"
    assert outcome["after"]["projected_reach"] >= 5000


def test_full_karachi_run(client):
    r = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "zarapk_regional_v1", "seed_region": "karachi"},
    )
    run_id = r.json()["run_id"]
    _wait_for(client, run_id, "outcome", timeout=60.0)
    outcome = client.get(f"/api/scenarios/runs/{run_id}/outcome").json()
    assert outcome["detected_region"] == "Karachi"


def test_sub_resources_return_202_before_ready(client):
    # Hit immediately after POST — most resources should still be 202
    r = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "zarapk_regional_v1", "seed_region": "lahore"},
    )
    run_id = r.json()["run_id"]
    # Tiny window before pipeline starts touching files
    early = client.get(f"/api/scenarios/runs/{run_id}/outcome")
    # 202 or 200 are both legitimate depending on timing — but never 404
    assert early.status_code in (200, 202)
    # Wait for it to complete so we don't leave a stuck background task
    _wait_for(client, run_id, "outcome", timeout=60.0)


def test_trace_zip_download(client):
    r = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "zarapk_regional_v1", "seed_region": "lahore"},
    )
    run_id = r.json()["run_id"]
    _wait_for(client, run_id, "outcome", timeout=60.0)

    resp = client.get(f"/api/scenarios/runs/{run_id}/trace.zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    # Inspect the zip
    zf = zipfile.ZipFile(BytesIO(resp.content))
    names = zf.namelist()
    assert any(n.endswith("outcome.json") for n in names)
    assert any(n.endswith("metadata.json") for n in names)
    assert any(n.endswith("README.txt") for n in names)


def test_trace_zip_404_for_unknown_run(client):
    r = client.get("/api/scenarios/runs/r-nonexistent-99/trace.zip")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_run_removes_state(client):
    r = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "zarapk_regional_v1", "seed_region": "lahore"},
    )
    run_id = r.json()["run_id"]
    _wait_for(client, run_id, "outcome", timeout=60.0)

    d = client.delete(f"/api/scenarios/runs/{run_id}")
    assert d.status_code == 200
    assert d.json()["deleted"] is True

    # Subsequent trace.zip should 404
    z = client.get(f"/api/scenarios/runs/{run_id}/trace.zip")
    assert z.status_code == 404
