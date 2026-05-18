"""
Tools for the ConflictResolver Agent.

Wrappers around detector and resolver functions, plus a template-based
rationale builder.
"""
from __future__ import annotations

import structlog

from agents.ingestion.schemas import Signal
from agents.conflict.detector import classify_pair, find_metric_pairs  # noqa: F401
from agents.conflict.resolver import decide, score_source_pair  # noqa: F401

log = structlog.get_logger()


def explain_resolution(
    sig_a_summary: dict,
    sig_b_summary: dict,
    decision: dict,
) -> str:
    """
    Build a 1-2 sentence plain-English rationale from the inputs.

    Template-based — no LLM call needed for MVP.
    """
    reason = decision.get("reason_code", "unknown")
    status = decision.get("status", "unknown")
    winner = decision.get("chosen_source", None)

    a_name = sig_a_summary.get("title", sig_a_summary.get("src_id", "Source A"))
    b_name = sig_b_summary.get("title", sig_b_summary.get("src_id", "Source B"))

    if status == "resolved" and reason == "recency":
        loser = b_name if winner == sig_a_summary.get("src_id") else a_name
        winner_name = a_name if winner == sig_a_summary.get("src_id") else b_name
        return (
            f"Resolved in favour of '{winner_name}' because it is significantly "
            f"more recent than '{loser}'."
        )

    if status == "resolved" and reason == "credibility":
        loser = b_name if winner == sig_a_summary.get("src_id") else a_name
        winner_name = a_name if winner == sig_a_summary.get("src_id") else b_name
        return (
            f"Resolved in favour of '{winner_name}' because it has higher "
            f"credibility than '{loser}'."
        )

    if status == "needs_human_review" and reason == "involves_discarded_source":
        return (
            f"Flagged for human review: one source ('{a_name}' or '{b_name}') "
            f"was previously discarded but still contradicts a trusted source."
        )

    if status == "needs_human_review" and reason == "equal_sources":
        return (
            f"Both '{a_name}' and '{b_name}' have similar credibility and "
            f"recency — a human must decide which is correct."
        )

    return f"Conflict between '{a_name}' and '{b_name}' with status '{status}'."
