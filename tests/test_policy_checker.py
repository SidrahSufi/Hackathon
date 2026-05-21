"""Tests for the PolicyChecker."""
from __future__ import annotations

from agents.common.policy import PolicyChecker


def test_under_budget_passes():
    pc = PolicyChecker()
    action = {"tool": "mock_launch_campaign", "cost_pkr": 500000, "region": "Lahore"}
    res = pc.check(action)
    assert res["ok"], res["violations"]


def test_over_budget_violation():
    pc = PolicyChecker()
    pc.record_usage(
        {"tool": "mock_launch_campaign", "cost_pkr": 600000, "region": "Lahore"},
        {"success": True},
    )
    res = pc.check(
        {"tool": "mock_launch_campaign", "cost_pkr": 300000, "region": "Lahore"}
    )
    assert not res["ok"]
    types = {v["type"] for v in res["violations"]}
    assert "budget" in types


def test_discount_over_cap_is_revised():
    pc = PolicyChecker()
    res = pc.check({"tool": "mock_launch_campaign", "discount_pct": 25.0})
    assert not res["ok"]
    assert res["suggested_revisions"]["discount_pct"] == 20.0


def test_discount_within_cap_passes():
    pc = PolicyChecker()
    res = pc.check({"tool": "mock_launch_campaign", "discount_pct": 18.0})
    assert res["ok"]


def test_notification_window_revises_outside_hours():
    pc = PolicyChecker()
    res = pc.check({
        "tool": "mock_draft_notification",
        "scheduled_time": "2026-05-20T22:00:00",
        "audience_size": 100,
    })
    assert not res["ok"]
    assert "scheduled_time" in res["suggested_revisions"]


def test_notification_window_inside_hours_passes():
    pc = PolicyChecker()
    res = pc.check({
        "tool": "mock_draft_notification",
        "scheduled_time": "2026-05-20T14:00:00",
        "audience_size": 100,
    })
    assert res["ok"]


def test_notification_rate_limit():
    pc = PolicyChecker()
    pc.record_usage(
        {"tool": "mock_draft_notification", "audience_size": 4999},
        {"success": True},
    )
    res = pc.check({"tool": "mock_draft_notification", "audience_size": 2})
    assert not res["ok"]
    types = {v["type"] for v in res["violations"]}
    assert "rate_limit" in types


def test_campaign_per_region_per_week_limit():
    pc = PolicyChecker()
    pc.record_usage(
        {"tool": "mock_launch_campaign", "region": "Lahore", "cost_pkr": 100000},
        {"success": True},
    )
    res = pc.check(
        {"tool": "mock_launch_campaign", "region": "Lahore", "cost_pkr": 100000}
    )
    types = {v["type"] for v in res["violations"]}
    assert "rate_limit_campaign" in types
