"""
Pure-Python temporal analysis for the Insight Agent.

ALL math lives here — the LLM never computes percentages, never compares
numbers, never clusters.  Every number in an Insight must trace back to a
function in this module.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import structlog

log = structlog.get_logger()

# Fixed reference date — same as gen_mock_data and ingestion tools.
REFERENCE_TODAY = datetime(2026, 5, 17, tzinfo=timezone.utc)
REFERENCE_TODAY_STR = REFERENCE_TODAY.strftime("%Y-%m-%d")


def compare_windows(
    df: pd.DataFrame,
    metric: str,
    group_col: str,
    date_col: str,
    window_a_days: int = 15,
    window_b_days: int = 15,
) -> pd.DataFrame:
    """
    Per-group percentage change between two trailing windows.

    Window A (recent) = last *window_a_days* of data.
    Window B (prior)  = the *window_b_days* immediately before Window A.

    Returns
    -------
    DataFrame with columns [group_col, window_a, window_b, pct_change],
    sorted ascending by pct_change (biggest decliner first).
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    max_date = df[date_col].max()
    window_a_start = max_date - timedelta(days=window_a_days - 1)
    window_b_end = window_a_start - timedelta(days=1)
    window_b_start = window_b_end - timedelta(days=window_b_days - 1)

    mask_a = (df[date_col] >= window_a_start) & (df[date_col] <= max_date)
    mask_b = (df[date_col] >= window_b_start) & (df[date_col] <= window_b_end)

    agg_a = df.loc[mask_a].groupby(group_col)[metric].sum().rename("window_a")
    agg_b = df.loc[mask_b].groupby(group_col)[metric].sum().rename("window_b")

    result = pd.concat([agg_a, agg_b], axis=1).reset_index()
    result["pct_change"] = (
        (result["window_a"] - result["window_b"]) / result["window_b"] * 100
    ).round(2)

    result = result.sort_values("pct_change", ascending=True).reset_index(drop=True)

    log.info(
        "Window comparison complete",
        agent="insight",
        phase="temporal",
        kind="compare_windows",
        payload={"metric": metric, "rows": len(result)},
        level="info",
    )
    return result


def detect_outlier_regions(
    window_df: pd.DataFrame,
    group_col: str = "region",
    noise_pct: float = 5.0,
) -> list[str]:
    """
    Regions whose absolute pct_change exceeds 2× the noise band.

    Parameters
    ----------
    window_df : output of compare_windows
    noise_pct : expected baseline noise (±%)

    Returns
    -------
    List of outlier region names (may be empty).
    """
    threshold = 2.0 * noise_pct
    outliers = window_df.loc[
        window_df["pct_change"].abs() > threshold, group_col
    ].tolist()

    log.info(
        "Outlier detection complete",
        agent="insight",
        phase="temporal",
        kind="detect_outlier",
        payload={"threshold": threshold, "outliers": outliers},
        level="info",
    )
    return outliers


def cluster_complaint_segment(
    tickets_df: pd.DataFrame,
    region: str,
    recent_days: int = 14,
) -> dict:
    """
    For a given region in the last *recent_days*, cluster tickets by category.

    Returns
    -------
    {"top_category": str, "share": float, "ticket_count": int}
    """
    tickets_df = tickets_df.copy()
    tickets_df["date"] = pd.to_datetime(tickets_df["date"])

    cutoff = pd.Timestamp(REFERENCE_TODAY - timedelta(days=recent_days)).tz_localize(None)
    mask = (tickets_df["region"] == region) & (tickets_df["date"] >= cutoff)
    subset = tickets_df.loc[mask]

    if subset.empty:
        return {"top_category": "none", "share": 0.0, "ticket_count": 0}

    counts = subset["category"].value_counts()
    top_cat = counts.index[0]
    share = round(counts.iloc[0] / len(subset), 2)

    result = {
        "top_category": top_cat,
        "share": share,
        "ticket_count": len(subset),
    }

    log.info(
        "Complaint clustering complete",
        agent="insight",
        phase="temporal",
        kind="cluster_complaints",
        payload=result,
        level="info",
    )
    return result


def correlate_in_time(event_date: str, decline_start_date: str) -> float:
    """
    Temporal correlation score ∈ [0.0, 1.0] based on proximity.

    - Event within 30 days BEFORE decline start → 0.8 – 1.0
    - Event AFTER decline start → 0.3 – 0.5
    - More than 90 days apart → 0.1
    """
    event = pd.Timestamp(event_date)
    decline = pd.Timestamp(decline_start_date)

    delta_days = (decline - event).days  # positive = event before decline

    if abs(delta_days) > 90:
        return 0.1

    if 0 <= delta_days <= 30:
        # event happened 0-30 days before decline — strong correlation
        return round(0.8 + 0.2 * (1 - delta_days / 30), 2)

    if delta_days < 0:
        # event after decline
        return round(0.5 - 0.2 * min(abs(delta_days) / 30, 1.0), 2)

    # event 31-90 days before decline
    return round(0.5 - 0.4 * ((delta_days - 30) / 60), 2)
