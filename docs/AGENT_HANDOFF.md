# Agent Pipeline Handoff

## What's built
- [cite_start]Ingestion Agent (agents/ingestion/) — parses 8 source files, scores credibility/recency, filters noise.
- [cite_start]Insight Agent (agents/insight/) — detects outlier region via cross-region temporal analysis (Python, not LLM)[cite: 3].
- [cite_start]ConflictResolver Agent (agents/conflict/) — resolves source disagreements; flags unresolvable conflicts as needs_human_review[cite: 4].
- [cite_start]End-to-end runner: `python -m agents.run_pipeline --seed <lahore|karachi> --run-id <id>`[cite: 5].

## Output contract — files the next agents must read

After `run_pipeline` finishes, three files exist at `.state/<run_id>/`:

### ingestion.json
[cite_start]Schema: IngestionResult (agents/ingestion/schemas.py)[cite: 5].
[cite_start]Fields: `run_id, seed_region, signals[], sources_processed, sources_discarded, discarded_summary[]`[cite: 6].

### insights.json
[cite_start]Schema: InsightResult (agents/insight/schemas.py)[cite: 6]. [cite_start]Fields: `run_id, seed_region, detected_outlier_region, insights[]`[cite: 6].
[cite_start]The Planner Agent should read `detected_outlier_region` and target all actions to that region[cite: 7].

### contradictions.json
[cite_start]Schema: ConflictResult (agents/conflict/schemas.py)[cite: 7].
[cite_start]Fields: `run_id, contradictions[], not_a_conflict_log[]`[cite: 8].
[cite_start]Contradictions with `status="needs_human_review"` should be surfaced in the UI but NOT acted on by the Executor[cite: 8].

## How to test the chain end-to-end
1. [cite_start]`python -m agents.run_pipeline --seed lahore --run-id r-demo-1` — produces Lahore outlier 
2. [cite_start]`python -m agents.run_pipeline --seed karachi --run-id r-demo-2` — produces Karachi outlier (proves region-agnosticism) 
3. [cite_start]`pytest tests/ -v` — runs all agent tests 

## Known properties (already test-enforced)
- [cite_start]No invented numbers: every metric in insights.json traces to a Python computation in agents/insight/temporal.py[cite: 9, 10].
- [cite_start]No forced resolutions: ConflictResolver never picks a winner when sources are equally credible AND equally recent[cite: 10].
- [cite_start]Region-agnostic: same code paths produce different outlier regions based purely on input data[cite: 11].

## Where the Planner should plug in
[cite_start]Read `.state/<run_id>/insights.json` + `.state/<run_id>/contradictions.json` → produce a 3-5 action chain targeting `detected_outlier_region` → write to `.state/<run_id>/plan.json`[cite: 12].