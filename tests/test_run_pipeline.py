"""
Integration tests for the end-to-end pipeline runner.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_lahore_e2e():
    """
    Test the pipeline end-to-end with the 'lahore' seed.
    Asserts expected counts and outlier region from state files.
    """
    run_id = "test-lahore-run-1"
    
    # Run the pipeline module as a subprocess
    result = subprocess.run(
        [sys.executable, "-m", "agents.run_pipeline", "--seed", "lahore", "--run-id", run_id],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Verify the output contains expected logs
    assert "=== PulseAI Pipeline | seed=lahore" in result.stderr or "=== PulseAI Pipeline | seed=lahore" in result.stdout
    
    # Verify state files
    workspace = Path(__file__).resolve().parent.parent
    state_dir = workspace / ".state" / run_id
    
    insights_path = state_dir / "insights.json"
    assert insights_path.exists()
    
    contradictions_path = state_dir / "contradictions.json"
    assert contradictions_path.exists()
    
    with open(insights_path, "r", encoding="utf-8") as f:
        insights_data = json.load(f)
        
    assert insights_data["detected_outlier_region"] == "Lahore"
    assert len(insights_data["insights"]) == 5
    
    with open(contradictions_path, "r", encoding="utf-8") as f:
        contradictions_data = json.load(f)
        
    assert len(contradictions_data["contradictions"]) == 2
    
    needs_review = sum(1 for c in contradictions_data["contradictions"] if c["status"] == "needs_human_review")
    assert needs_review == 1


def test_karachi_e2e():
    """
    Test the pipeline end-to-end with the 'karachi' seed.
    Asserts expected counts and outlier region from state files to prove region-agnosticism.
    """
    run_id = "test-karachi-run-1"
    
    # Run the pipeline module as a subprocess
    subprocess.run(
        [sys.executable, "-m", "agents.run_pipeline", "--seed", "karachi", "--run-id", run_id],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Verify state files
    workspace = Path(__file__).resolve().parent.parent
    state_dir = workspace / ".state" / run_id
    
    insights_path = state_dir / "insights.json"
    assert insights_path.exists()
    
    contradictions_path = state_dir / "contradictions.json"
    assert contradictions_path.exists()
    
    with open(insights_path, "r", encoding="utf-8") as f:
        insights_data = json.load(f)
        
    assert insights_data["detected_outlier_region"] == "Karachi"
    assert len(insights_data["insights"]) == 5
    
    with open(contradictions_path, "r", encoding="utf-8") as f:
        contradictions_data = json.load(f)
        
    assert len(contradictions_data["contradictions"]) == 2
    
    needs_review = sum(1 for c in contradictions_data["contradictions"] if c["status"] == "needs_human_review")
    assert needs_review == 1


def test_state_files_exist():
    """
    Test that all three .state/<run_id>/*.json files exist after the run.
    Uses 'lahore' seed as an example.
    """
    run_id = "test-files-exist-run"
    
    subprocess.run(
        [sys.executable, "-m", "agents.run_pipeline", "--seed", "lahore", "--run-id", run_id],
        check=True
    )
    
    workspace = Path(__file__).resolve().parent.parent
    state_dir = workspace / ".state" / run_id
    
    assert (state_dir / "ingestion.json").exists()
    assert (state_dir / "insights.json").exists()
    assert (state_dir / "contradictions.json").exists()
