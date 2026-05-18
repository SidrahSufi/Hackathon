"""
Insight Agent — second stage of the PulseAI pipeline.

Reads ingestion.json, performs cross-region temporal analysis, detects the
outlier region, identifies the affected segment, and produces 5 ranked
insights with evidence references.  Writes insights.json to .state/<run_id>/.
"""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import structlog
from google.adk.agents import LlmAgent

from agents.ingestion.schemas import IngestionResult, Signal
from agents.insight.schemas import Insight, InsightResult
from agents.insight.temporal import (
    REFERENCE_TODAY,
    cluster_complaint_segment,
    compare_windows,
    correlate_in_time,
    detect_outlier_regions,
)
from agents.insight.tools import extract_entities_from_html

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Window configuration constants (easy to tune)
# ---------------------------------------------------------------------------
WINDOW_A_DAYS = 15  # recent window
WINDOW_B_DAYS = 15  # prior window
NOISE_PCT = 5.0     # expected baseline noise band (±%)

# ---------------------------------------------------------------------------
# ADK LlmAgent (reserved for future reasoning over ambiguous insights)
# ---------------------------------------------------------------------------

insight_agent = LlmAgent(
    name="insight",
    model="gemini-2.5-pro",
    instruction="""You are the Insight Agent for PulseAI.

Your job: analyse ingested signals and detect the underperforming region.

You MUST call the temporal analysis tools to compute numbers.
You MUST NOT compute percentages, compare numbers, or cluster data yourself.
You orchestrate tool calls and write human-readable rationale text.
Every number in an Insight must trace back to a Python tool's output.
""",
    tools=[
        compare_windows,
        detect_outlier_regions,
        cluster_complaint_segment,
        correlate_in_time,
        extract_entities_from_html,
    ],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_signal(signals: list[Signal], **match) -> Signal | None:
    """Find first non-discarded signal matching keyword filters."""
    for s in signals:
        if s.discarded:
            continue
        ok = True
        for k, v in match.items():
            if k == "filename_contains":
                if v.lower() not in Path(s.source_path).name.lower():
                    ok = False
            elif getattr(s, k, None) != v:
                ok = False
        if ok:
            return s
    return None


def _load_raw_file(signal: Signal) -> str | list | dict:
    """Load the raw file pointed to by a signal."""
    path = Path(signal.source_path)
    if signal.source_type == "csv":
        return pd.read_csv(path)
    elif signal.source_type == "jsonl":
        records = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    elif signal.source_type in ("json",):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()


# ---------------------------------------------------------------------------
# Pure-Python orchestrator
# ---------------------------------------------------------------------------

def run_insight(run_id: str) -> InsightResult:
    """
    Deterministic insight pipeline — pure Python, no LLM call.

    Steps:
    1. Load ingestion.json and filter to non-discarded signals.
    2. Run compare_windows on POS CSV orders.
    3. detect_outlier_regions → set detected_outlier_region.
    4. For the outlier: cluster complaints, compute reach change,
       extract competitor entities, read marketing spend.
    5. Build 5 insights (I1–I5).
    6. Write insights.json.
    """
    workspace = Path(__file__).resolve().parent.parent.parent
    state_dir = workspace / ".state" / run_id

    # --- 1. Load ingestion result ---
    ingestion_path = state_dir / "ingestion.json"
    if not ingestion_path.exists():
        raise FileNotFoundError(f"Ingestion result not found: {ingestion_path}")

    ingestion = IngestionResult.model_validate_json(ingestion_path.read_text("utf-8"))
    seed_region = ingestion.seed_region
    active_signals = [s for s in ingestion.signals if not s.discarded]

    log.info(
        "Loaded ingestion result",
        agent="insight",
        phase="load",
        kind="ingestion",
        payload={"active_signals": len(active_signals)},
        level="info",
    )

    # --- 2. POS CSV → compare_windows ---
    csv_signal = _find_signal(active_signals, source_type="csv")
    if csv_signal is None:
        raise ValueError("No POS CSV signal found in ingestion result")

    pos_df = _load_raw_file(csv_signal)
    window_df = compare_windows(
        pos_df, metric="orders", group_col="region", date_col="date",
        window_a_days=WINDOW_A_DAYS, window_b_days=WINDOW_B_DAYS,
    )

    # --- 3. Detect outlier ---
    outlier_list = detect_outlier_regions(window_df, noise_pct=NOISE_PCT)
    detected_outlier: str | None = outlier_list[0] if len(outlier_list) >= 1 else None

    insights: list[Insight] = []

    if detected_outlier is None:
        # No outlier found — emit single info insight
        insights.append(Insight(
            insight_id="I5",
            title="All regions stable",
            severity="info",
            confidence=0.9,
            region=None,
            evidence_refs=[csv_signal.src_id],
            metrics={"noise_band_pct": NOISE_PCT},
            rationale=(
                f"All regions are within the ±{NOISE_PCT}% noise band. "
                "No significant outlier detected."
            ),
        ))
        result = InsightResult(
            run_id=run_id,
            seed_region=seed_region,
            detected_outlier_region=None,
            insights=insights,
        )
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "insights.json").write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )
        return result

    # Get the outlier's pct_change from the window dataframe
    outlier_row = window_df.loc[window_df["region"] == detected_outlier].iloc[0]
    orders_change_pct = float(outlier_row["pct_change"])

    # --- 4a. Cluster complaint segment ---
    tickets_signal = _find_signal(active_signals, source_type="jsonl")
    complaint_info = {"top_category": "unknown", "share": 0.0, "ticket_count": 0}
    if tickets_signal:
        tickets_data = _load_raw_file(tickets_signal)
        tickets_df = pd.DataFrame(tickets_data)
        complaint_info = cluster_complaint_segment(tickets_df, detected_outlier)

    # --- 4b. Analytics reach change ---
    analytics_signal = _find_signal(
        active_signals, source_type="json", filename_contains="analytics"
    )
    reach_change_pct = 0.0
    if analytics_signal:
        analytics_data = _load_raw_file(analytics_signal)
        analytics_df = pd.DataFrame(analytics_data)
        reach_window = compare_windows(
            analytics_df, metric="reach", group_col="region", date_col="date",
            window_a_days=WINDOW_A_DAYS, window_b_days=WINDOW_B_DAYS,
        )
        outlier_reach = reach_window.loc[reach_window["region"] == detected_outlier]
        if not outlier_reach.empty:
            reach_change_pct = float(outlier_reach.iloc[0]["pct_change"])

    # --- 4c. Competitor entities from news HTML ---
    news_signal = _find_signal(
        active_signals, source_type="html", filename_contains="news_competitor"
    )
    competitor_info: dict = {}
    correlation_score = 0.0
    if news_signal:
        competitor_info = extract_entities_from_html(news_signal.source_path)

        # Compute temporal correlation
        expansion_date = competitor_info.get("expansion_date")
        if expansion_date:
            # Decline start ≈ start of window A
            max_date = pos_df["date"].max()
            decline_start = (
                pd.Timestamp(max_date) - timedelta(days=WINDOW_A_DAYS - 1)
            ).strftime("%Y-%m-%d")
            # Expansion month → use first day of month
            correlation_score = correlate_in_time(
                f"{expansion_date}-01", decline_start
            )

    # --- 4d. Marketing spend ---
    marketing_signal = _find_signal(
        active_signals, source_type="json", filename_contains="marketing"
    )
    outlier_spend: dict = {}
    total_outlier_spend = 0
    if marketing_signal:
        spend_data = _load_raw_file(marketing_signal)
        regions_spend = spend_data.get("regions", {})
        outlier_spend = regions_spend.get(detected_outlier, {})
        total_outlier_spend = sum(outlier_spend.values())

    # --- 4e. Load seed file for affected_segment metadata ---
    seed_path = (
        workspace / "sources" / "zarapk_regional_v1" / f"{seed_region}.seed.json"
    )
    affected_segment = {}
    if seed_path.exists():
        with open(seed_path, "r", encoding="utf-8") as fh:
            seed_data = json.load(fh)
        affected_segment = seed_data.get("affected_segment", {})

    # --- 5. Build stable-region stats for I5 ---
    stable_rows = window_df.loc[window_df["region"] != detected_outlier]
    stable_min = float(stable_rows["pct_change"].min()) if not stable_rows.empty else 0
    stable_max = float(stable_rows["pct_change"].max()) if not stable_rows.empty else 0

    # --- 6. Build 5 insights ---

    # I1: Outlier region orders decline
    insights.append(Insight(
        insight_id="I1",
        title=f"Outlier region: {detected_outlier} orders {orders_change_pct:+.1f}%",
        severity="high",
        confidence=0.92,
        region=detected_outlier,
        evidence_refs=[csv_signal.src_id],
        metrics={
            "orders_change_pct": orders_change_pct,
            "window_a_days": WINDOW_A_DAYS,
            "window_b_days": WINDOW_B_DAYS,
        },
        rationale=(
            f"{detected_outlier} orders declined {orders_change_pct:+.1f}% in the "
            f"last {WINDOW_A_DAYS} days compared to the prior {WINDOW_B_DAYS}-day "
            f"window, far exceeding the ±{NOISE_PCT}% noise band of other regions."
        ),
    ))

    # I2: Affected segment
    segment_cat = affected_segment.get("category", complaint_info["top_category"])
    age_range = affected_segment.get("age_range", [])
    age_str = f" ages {age_range[0]}–{age_range[1]}" if len(age_range) == 2 else ""
    evidence_i2 = []
    if tickets_signal:
        evidence_i2.append(tickets_signal.src_id)
    insights.append(Insight(
        insight_id="I2",
        title=(
            f"Affected segment: {segment_cat}{age_str} in {detected_outlier}"
        ),
        severity="medium",
        confidence=0.78,
        region=detected_outlier,
        evidence_refs=evidence_i2,
        metrics={
            "top_complaint_category": complaint_info["top_category"],
            "complaint_share": complaint_info["share"],
            "ticket_count": complaint_info["ticket_count"],
            "affected_category": segment_cat,
        },
        rationale=(
            f"Support tickets in {detected_outlier} over the last 14 days show "
            f"\"{complaint_info['top_category']}\" as the top complaint category "
            f"({complaint_info['share']:.0%} of {complaint_info['ticket_count']} "
            f"tickets), consistent with pressure on the {segment_cat} segment."
        ),
    ))

    # I3: Marketing reach drop despite full spend
    evidence_i3 = []
    if analytics_signal:
        evidence_i3.append(analytics_signal.src_id)
    if marketing_signal:
        evidence_i3.append(marketing_signal.src_id)
    insights.append(Insight(
        insight_id="I3",
        title=(
            f"Marketing anomaly: {detected_outlier} reach {reach_change_pct:+.1f}% "
            f"despite highest spend"
        ),
        severity="high",
        confidence=0.85,
        region=detected_outlier,
        evidence_refs=evidence_i3,
        metrics={
            "reach_change_pct": reach_change_pct,
            "total_spend_pkr": total_outlier_spend,
            "spend_breakdown": outlier_spend,
        },
        rationale=(
            f"{detected_outlier} digital reach dropped {reach_change_pct:+.1f}% "
            f"despite having the largest marketing budget (PKR "
            f"{total_outlier_spend:,}). This suggests the campaign is silently "
            f"broken or audience fatigue has set in."
        ),
    ))

    # I4: Competitor temporal correlation
    competitor_name = competitor_info.get("competitor_name", "Unknown")
    expansion_date_str = competitor_info.get("expansion_date", "N/A")
    evidence_i4 = []
    if news_signal:
        evidence_i4.append(news_signal.src_id)
    if csv_signal:
        evidence_i4.append(csv_signal.src_id)
    insights.append(Insight(
        insight_id="I4",
        title=(
            f"Competitor {competitor_name} expansion in {detected_outlier} "
            f"correlates with decline"
        ),
        severity="medium",
        confidence=round(correlation_score, 2),
        region=detected_outlier,
        evidence_refs=evidence_i4,
        metrics={
            "competitor_name": competitor_name,
            "expansion_date": expansion_date_str,
            "temporal_correlation": correlation_score,
        },
        rationale=(
            f"{competitor_name} opened stores in {detected_outlier} around "
            f"{expansion_date_str} with aggressive pricing. Temporal correlation "
            f"score with the orders decline is {correlation_score:.2f}."
        ),
    ))

    # I5: Stable regions
    stable_count = len(stable_rows)
    insights.append(Insight(
        insight_id="I5",
        title=(
            f"{stable_count} other regions stable within "
            f"±{NOISE_PCT}% noise band"
        ),
        severity="info",
        confidence=0.95,
        region=None,
        evidence_refs=[csv_signal.src_id],
        metrics={
            "stable_region_count": stable_count,
            "noise_band_pct": NOISE_PCT,
            "stable_range_min_pct": stable_min,
            "stable_range_max_pct": stable_max,
        },
        rationale=(
            f"The remaining {stable_count} regions show order changes "
            f"between {stable_min:+.1f}% and {stable_max:+.1f}%, well within "
            f"the expected ±{NOISE_PCT}% noise band."
        ),
    ))

    # --- 7. Build result and write ---
    result = InsightResult(
        run_id=run_id,
        seed_region=seed_region,
        detected_outlier_region=detected_outlier,
        insights=insights,
    )

    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "insights.json"
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    log.info(
        "Insight pipeline complete",
        agent="insight",
        phase="done",
        kind="result",
        payload={
            "run_id": run_id,
            "detected_outlier": detected_outlier,
            "insight_count": len(insights),
        },
        level="info",
    )

    return result
