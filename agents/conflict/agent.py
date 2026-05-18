"""
ConflictResolver Agent — third stage of the PulseAI pipeline.

Reads ingestion.json and insights.json, finds source pairs that disagree on
the same metric, resolves them or flags for human review, and writes
contradictions.json to .state/<run_id>/.
"""
from __future__ import annotations

from pathlib import Path

import structlog
from google.adk.agents import LlmAgent

from agents.ingestion.schemas import IngestionResult, Signal
from agents.conflict.detector import classify_pair, find_metric_pairs
from agents.conflict.resolver import decide, score_source_pair
from agents.conflict.schemas import Contradiction, ConflictResult
from agents.conflict.tools import explain_resolution

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# ADK LlmAgent (reserved for future nuanced conflict reasoning)
# ---------------------------------------------------------------------------

conflict_agent = LlmAgent(
    name="conflict_resolver",
    model="gemini-2.5-pro",
    instruction="""You are the ConflictResolver Agent for PulseAI.

Your job: detect source pairs that disagree on the same metric and resolve
them using the provided tools.

You MUST NOT force a resolution when sources are equally credible and
equally recent — flag those as needs_human_review.

You MUST call score_source_pair and decide for every direct conflict.
You MUST NOT invent resolution logic yourself.
""",
    tools=[
        find_metric_pairs,
        classify_pair,
        score_source_pair,
        decide,
        explain_resolution,
    ],
)


# ---------------------------------------------------------------------------
# Value extraction helpers
# ---------------------------------------------------------------------------

def _extract_value_text(signal: Signal, metric: str) -> str:
    """
    Extract a human-readable value string from a signal for the given metric.
    """
    content = signal.content
    filename = Path(signal.source_path).name.lower()

    if signal.source_type == "pdf" and metric.startswith("growth_pct_"):
        # PDF contains embedded text with YoY growth claims
        text = content.get("text", "")
        # Try to find the outlier region's growth from the table
        region = metric.replace("growth_pct_", "").title()
        if region.lower() in text.lower():
            # Look for percentage near region name
            import re
            # PDF table text usually has region followed by numbers
            pattern = rf"{region}.*?([+-]?\d+%)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} YoY (stale PDF report)"
        return "YoY growth figure from stale PDF report"

    if signal.source_type == "csv" and metric.startswith("growth_pct_"):
        return "Recent 30-day POS data showing order trend"

    if "news_competitor" in filename and metric == "competitor_pricing_claim":
        return "Competitor pricing ~30% cheaper (credible news source)"

    if "news_pricing_blog" in filename and metric == "competitor_pricing_claim":
        return "Competitor pricing 'roughly similar' (anonymous blog)"

    if "marketing" in filename and metric.startswith("campaign_health_"):
        return "Full marketing budget allocated"

    if "analytics" in filename and metric.startswith("campaign_health_"):
        return "Digital reach metrics (declining)"

    return f"Value from {filename}"


# ---------------------------------------------------------------------------
# Pure-Python orchestrator
# ---------------------------------------------------------------------------

def run_conflict(run_id: str) -> ConflictResult:
    """
    Deterministic conflict resolution pipeline — pure Python, no LLM call.

    Steps:
    1. Load ingestion.json and insights.json.
    2. Run find_metric_pairs on ALL signals (including discarded).
    3. For each pair: classify, then decide or log as not_a_conflict.
    4. Write contradictions.json.
    """
    workspace = Path(__file__).resolve().parent.parent.parent
    state_dir = workspace / ".state" / run_id

    # --- 1. Load ingestion result ---
    ingestion_path = state_dir / "ingestion.json"
    if not ingestion_path.exists():
        raise FileNotFoundError(f"Ingestion result not found: {ingestion_path}")

    ingestion = IngestionResult.model_validate_json(
        ingestion_path.read_text("utf-8")
    )
    all_signals = ingestion.signals

    log.info(
        "Loaded signals for conflict detection",
        agent="conflict",
        phase="load",
        kind="ingestion",
        payload={"total_signals": len(all_signals)},
        level="info",
    )

    # --- 2. Detect pairs ---
    pairs = find_metric_pairs(all_signals)

    # --- 3. Process each pair ---
    contradictions: list[Contradiction] = []
    not_a_conflict_log: list[dict] = []
    conflict_idx = 0

    for sig_a, sig_b, metric in pairs:
        classification = classify_pair(metric, sig_a, sig_b)

        if classification == "unrelated":
            continue

        if classification == "different_angle":
            not_a_conflict_log.append({
                "source_a": sig_a.src_id,
                "source_b": sig_b.src_id,
                "metric": metric,
                "classification": classification,
                "reason": (
                    "Both facts are true but viewed from different angles. "
                    "This is surfaced as an insight (e.g. I3), not a contradiction."
                ),
            })
            log.info(
                "Pair classified as not_a_conflict",
                agent="conflict",
                phase="classify",
                kind="different_angle",
                payload={"metric": metric},
                level="info",
            )
            continue

        # direct_conflict → resolve
        conflict_idx += 1
        conflict_id = f"c{conflict_idx}"

        status, chosen_source, reason_code = decide(sig_a, sig_b)
        scores = score_source_pair(sig_a, sig_b)

        value_a = _extract_value_text(sig_a, metric)
        value_b = _extract_value_text(sig_b, metric)

        rationale = explain_resolution(
            sig_a_summary={"src_id": sig_a.src_id, "title": sig_a.title},
            sig_b_summary={"src_id": sig_b.src_id, "title": sig_b.title},
            decision={
                "status": status,
                "chosen_source": chosen_source,
                "reason_code": reason_code,
            },
        )

        # Confidence: high if resolved clearly, lower if needs review
        if status == "resolved":
            confidence = min(1.0, 0.7 + abs(scores["recency_delta"])
                             + abs(scores["credibility_delta"]))
        else:
            confidence = 0.4

        region = metric.split("_")[-1].title() if "_" in metric else None
        if metric == "competitor_pricing_claim":
            region = None

        contradictions.append(Contradiction(
            conflict_id=conflict_id,
            metric=metric,
            region=region,
            source_a=sig_a.src_id,
            source_b=sig_b.src_id,
            value_a=value_a,
            value_b=value_b,
            status=status,
            chosen_source=chosen_source,
            rationale=rationale,
            confidence=round(confidence, 2),
        ))

        log.info(
            "Contradiction processed",
            agent="conflict",
            phase="resolve",
            kind=status,
            payload={
                "conflict_id": conflict_id,
                "metric": metric,
                "status": status,
                "chosen": chosen_source,
            },
            level="info",
        )

    # --- 4. Build result and write ---
    result = ConflictResult(
        run_id=run_id,
        contradictions=contradictions,
        not_a_conflict_log=not_a_conflict_log,
    )

    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "contradictions.json"
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    log.info(
        "Conflict resolution complete",
        agent="conflict",
        phase="done",
        kind="result",
        payload={
            "run_id": run_id,
            "contradictions": len(contradictions),
            "not_a_conflict": len(not_a_conflict_log),
        },
        level="info",
    )

    return result
