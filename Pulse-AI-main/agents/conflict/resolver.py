"""
Pure-Python resolution rules for the ConflictResolver Agent.

All decision logic lives here — the LLM is never in the decision loop.
"""
from __future__ import annotations

import structlog

from agents.ingestion.schemas import Signal

log = structlog.get_logger()


def score_source_pair(sig_a: Signal, sig_b: Signal) -> dict:
    """
    Compute deltas between two signals.

    Returns
    -------
    {"recency_delta": float, "credibility_delta": float}

    Positive delta means signal A is ahead of signal B.
    """
    return {
        "recency_delta": round(sig_a.recency - sig_b.recency, 4),
        "credibility_delta": round(sig_a.credibility - sig_b.credibility, 4),
    }


def decide(sig_a: Signal, sig_b: Signal) -> tuple[str, str | None, str]:
    """
    Decide the resolution status for a conflicting pair.

    Returns
    -------
    (status, chosen_source_id, decision_reason_code)

    Rules (in priority order):
    0. If either signal is discarded → needs_human_review.
       Rationale: a discarded source contradicting a trusted source may
       indicate the discarding was wrong; a human should verify.
    1. |recency_delta| >= 0.3 → pick the more recent source.
    2. |credibility_delta| >= 0.2 → pick the more credible source.
    3. Otherwise → needs_human_review (sources are too close to call).
    """
    scores = score_source_pair(sig_a, sig_b)
    rec_delta = scores["recency_delta"]
    cred_delta = scores["credibility_delta"]

    # Rule 0: discarded source involved
    if sig_a.discarded or sig_b.discarded:
        log.info(
            "Conflict involves discarded source",
            agent="conflict",
            phase="decide",
            kind="discarded",
            payload={"a": sig_a.src_id, "b": sig_b.src_id},
            level="info",
        )
        return ("needs_human_review", None, "involves_discarded_source")

    # Rule 1: recency
    if abs(rec_delta) >= 0.3:
        winner = sig_a.src_id if rec_delta > 0 else sig_b.src_id
        log.info(
            "Resolved by recency",
            agent="conflict",
            phase="decide",
            kind="recency",
            payload={"winner": winner, "delta": rec_delta},
            level="info",
        )
        return ("resolved", winner, "recency")

    # Rule 2: credibility
    if abs(cred_delta) >= 0.2:
        winner = sig_a.src_id if cred_delta > 0 else sig_b.src_id
        log.info(
            "Resolved by credibility",
            agent="conflict",
            phase="decide",
            kind="credibility",
            payload={"winner": winner, "delta": cred_delta},
            level="info",
        )
        return ("resolved", winner, "credibility")

    # Rule 3: too close to call
    log.info(
        "Conflict needs human review — sources too close",
        agent="conflict",
        phase="decide",
        kind="equal_sources",
        payload={"rec_delta": rec_delta, "cred_delta": cred_delta},
        level="info",
    )
    return ("needs_human_review", None, "equal_sources")
