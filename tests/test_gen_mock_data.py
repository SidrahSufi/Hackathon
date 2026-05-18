"""
Tests for gen_mock_data generator.
"""
import subprocess
import sys
import pandas as pd
from pathlib import Path

def test_gen_mock_data_lahore():
    result = subprocess.run(
        [sys.executable, "-m", "agents.gen_mock_data", "--seed", "lahore"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Generator failed: {result.stderr}"
    
    workspace = Path(__file__).resolve().parent.parent
    output_dir = workspace / "sources" / "zarapk_regional_v1" / "lahore"
    
    assert output_dir.exists()
    
    files = [
        "monthly_regional_sales.pdf",
        "pos_ecom_last_30d.csv",
        "news_competitor_expansion.html",
        "analytics_by_region.json",
        "support_tickets.jsonl",
        "marketing_spend.json",
        "news_pricing_blog.html",
        "social_post_spam.json"
    ]
    
    for f in files:
        file_path = output_dir / f
        assert file_path.exists(), f"Missing {f}"
        
    df = pd.read_csv(output_dir / "pos_ecom_last_30d.csv")
    assert len(df) == 360, f"Expected 360 rows, got {len(df)}"
    
    with open(output_dir / "support_tickets.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 200, f"Expected 200 lines, got {len(lines)}"
    
    with open(output_dir / "news_competitor_expansion.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "Lahore" in html_content, "Expected 'Lahore' in HTML content"

def test_gen_mock_data_karachi():
    result = subprocess.run(
        [sys.executable, "-m", "agents.gen_mock_data", "--seed", "karachi"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Generator failed: {result.stderr}"
    
    workspace = Path(__file__).resolve().parent.parent
    output_dir = workspace / "sources" / "zarapk_regional_v1" / "karachi"
    
    assert output_dir.exists()
    
    files = [
        "monthly_regional_sales.pdf",
        "pos_ecom_last_30d.csv",
        "news_competitor_expansion.html",
        "analytics_by_region.json",
        "support_tickets.jsonl",
        "marketing_spend.json",
        "news_pricing_blog.html",
        "social_post_spam.json"
    ]
    
    for f in files:
        file_path = output_dir / f
        assert file_path.exists(), f"Missing {f}"
        
    df = pd.read_csv(output_dir / "pos_ecom_last_30d.csv")
    assert len(df) == 360
    
    with open(output_dir / "support_tickets.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 200
    
    with open(output_dir / "news_competitor_expansion.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "Karachi" in html_content, "Expected 'Karachi' in HTML content"
