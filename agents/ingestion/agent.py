"""
Ingestion Agent — first stage of the PulseAI pipeline.

Reads source files, normalises them into Signal records, scores credibility
and recency, filters noise, and writes ingestion.json to .state/<run_id>/.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import structlog
from google.adk.agents import LlmAgent

from agents.ingestion.schemas import IngestionResult, Signal, SourceType
from agents.ingestion.tools import (
    REFERENCE_TODAY,
    is_spam,
    parse_csv,
    parse_html,
    parse_json,
    parse_jsonl,
    parse_pdf,
    score_credibility,
    score_recency,
)

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# ADK LlmAgent (reserved for future ambiguous-source reasoning)
# ---------------------------------------------------------------------------

ingestion_agent = LlmAgent(
    name="ingestion",
    model="gemini-2.5-pro",
    instruction="""You are the Ingestion Agent for PulseAI.

Your job: orchestrate parsing of source files and produce a clean list of
Signal records.

For each file in the source directory:
1. Detect the file type from its extension.
2. Call the matching parser tool.
3. Score its credibility and recency using the scoring tools.
4. Decide if it should be discarded (low credibility AND no corroboration,
   OR matches spam patterns).

You MUST NOT invent content. If a parser fails, mark the signal discarded
with discard_reason="parser_error: <message>".
You MUST NOT score credibility yourself — always call score_credibility.
""",
    tools=[
        parse_pdf,
        parse_csv,
        parse_html,
        parse_json,
        parse_jsonl,
        score_credibility,
        score_recency,
        is_spam,
    ],
)


# ---------------------------------------------------------------------------
# Extension → parser mapping
# ---------------------------------------------------------------------------

_PARSER_MAP: dict[str, tuple[callable, SourceType]] = {
    ".pdf": (parse_pdf, "pdf"),
    ".csv": (parse_csv, "csv"),
    ".html": (parse_html, "html"),
    ".json": (parse_json, "json"),
    ".jsonl": (parse_jsonl, "jsonl"),
}


def _extract_timestamp(source_type: SourceType, parsed: dict) -> datetime:
    """Best-effort timestamp extraction from parsed content."""
    if source_type == "pdf":
        cd = parsed.get("creation_date")
        if cd:
            try:
                return datetime.fromisoformat(cd)
            except (ValueError, TypeError):
                pass

    if source_type == "html":
        ds = parsed.get("date_str")
        if ds:
            try:
                return datetime.strptime(ds, "%B %d, %Y").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

    # Fallback: use reference today (source has no embedded date)
    return REFERENCE_TODAY


def _extract_title(source_type: SourceType, parsed: dict, filename: str) -> str:
    """Derive a human-readable title."""
    if source_type == "html":
        title = parsed.get("title")
        if title:
            return title
    return filename


def _extract_text_for_spam_check(source_type: SourceType, parsed: dict) -> str:
    """Pull a text blob suitable for spam / credibility analysis."""
    if source_type == "html":
        return parsed.get("text", "")
    if source_type == "json":
        data = parsed.get("data", {})
        if isinstance(data, dict):
            return data.get("text", "")
    if source_type == "jsonl":
        texts = [r.get("text", "") for r in parsed.get("records", [])]
        return " ".join(texts)
    if source_type == "pdf":
        return parsed.get("text", "")
    return ""


# ---------------------------------------------------------------------------
# Pure-Python orchestrator (MVP — no LLM call needed)
# ---------------------------------------------------------------------------

def run_ingestion(run_id: str, seed_region: str) -> IngestionResult:
    """
    Deterministic ingestion pipeline.

    1. List all files in sources/zarapk_regional_v1/<seed_region>/.
    2. For each file, invoke the parser based on extension.
    3. Build Signal objects with src-1 … src-N ids.
    4. Compute credibility + recency for each.
    5. Apply discard rules: credibility < 0.35 OR is_spam.
    6. Build IngestionResult and write to .state/<run_id>/ingestion.json.
    7. Return the IngestionResult.
    """
    workspace = Path(__file__).resolve().parent.parent.parent
    source_dir = workspace / "sources" / "zarapk_regional_v1" / seed_region

    if not source_dir.exists():
        log.error("Source directory not found", path=str(source_dir))
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # Sort for deterministic src-id assignment
    files = sorted(
        f for f in source_dir.iterdir()
        if f.is_file() and f.suffix in _PARSER_MAP
    )

    signals: list[Signal] = []
    now = REFERENCE_TODAY

    for idx, filepath in enumerate(files, start=1):
        src_id = f"src-{idx}"
        ext = filepath.suffix
        parser_fn, source_type = _PARSER_MAP[ext]

        log.info(
            "Parsing source",
            agent="ingestion",
            phase="parse",
            kind="file",
            payload={"src_id": src_id, "file": filepath.name},
            level="info",
        )

        try:
            parsed = parser_fn(str(filepath))
        except Exception as exc:
            log.warning(
                "Parser failed",
                agent="ingestion",
                phase="parse",
                kind="error",
                payload={"src_id": src_id, "error": str(exc)},
                level="warning",
            )
            signals.append(Signal(
                src_id=src_id,
                source_type=source_type,
                source_path=str(filepath),
                title=filepath.name,
                timestamp=now,
                ingested_at=now,
                credibility=0.0,
                recency=0.0,
                content={},
                discarded=True,
                discard_reason=f"parser_error: {exc}",
            ))
            continue

        timestamp = _extract_timestamp(source_type, parsed)
        title = _extract_title(source_type, parsed, filepath.name)
        text_blob = _extract_text_for_spam_check(source_type, parsed)

        metadata = {
            "filename": filepath.name,
            "text": text_blob,
            "byline": parsed.get("byline"),
        }

        cred = score_credibility(source_type, metadata)
        rec = score_recency(timestamp)
        spam = is_spam(text_blob)

        discarded = cred < 0.35 or spam
        reason: str | None = None
        if discarded:
            parts: list[str] = []
            if cred < 0.35:
                parts.append(f"low credibility ({cred})")
            if spam:
                parts.append("spam detected")
            reason = "; ".join(parts)

        signals.append(Signal(
            src_id=src_id,
            source_type=source_type,
            source_path=str(filepath),
            title=title,
            timestamp=timestamp,
            ingested_at=now,
            credibility=cred,
            recency=rec,
            content=parsed,
            discarded=discarded,
            discard_reason=reason,
        ))

    discarded_signals = [s for s in signals if s.discarded]
    result = IngestionResult(
        run_id=run_id,
        seed_region=seed_region,
        signals=signals,
        sources_processed=len(signals),
        sources_discarded=len(discarded_signals),
        discarded_summary=[
            {
                "src_id": s.src_id,
                "reason": s.discard_reason,
                "details": s.title,
            }
            for s in discarded_signals
        ],
    )

    # Write to .state/<run_id>/ingestion.json
    state_dir = workspace / ".state" / run_id
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "ingestion.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(result.model_dump_json(indent=2))

    log.info(
        "Ingestion complete",
        agent="ingestion",
        phase="done",
        kind="result",
        payload={
            "run_id": run_id,
            "sources_processed": result.sources_processed,
            "sources_discarded": result.sources_discarded,
        },
        level="info",
    )

    return result
