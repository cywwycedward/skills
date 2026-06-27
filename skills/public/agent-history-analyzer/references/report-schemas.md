# Report Schemas

Reference for output directory layout, report sections, evidence tables, and data category schemas.
Read before saving the final report package.

## Output Location

Save under `skills/public/agent-history-analyzer/.output/YYYY-MM-DD-summary/`.

- `YYYY-MM-DD`: date of analysis
- `summary`: short, ASCII, filename-safe, privacy-safe label (do not use raw private names)
- `.output/` is git-ignored

## Directory Structure

```text
.output/YYYY-MM-DD-summary/
|-- report.md
|-- inventory_summary.json
|-- warnings.md
|-- user-habits/
|   |-- report.md
|   |-- evidence-table.csv
|   |-- data-categories.json
|   `-- text_profile_summary.json
`-- agent-behavior/          # only when enabled
    |-- report.md
    |-- evidence-table.csv
    |-- data-categories.json
    `-- text_profile_summary.json
```

## Root report.md

Required sections:

```md
# Agent History Analysis Report

## Scope
## Method
## Executive Summary
## User Habit Findings
## Quantitative Signals
## Memory Quality
## Privacy And Risk Notes
## Evidence Strength Summary
## Recommendations
## Limits And Next Steps
```

If agent behavior analysis enabled, add `## Agent Behavior Appendix`.

Root `report.md` is an executive overview. Details live in child reports.

## warnings.md

Required sections:

```md
# Warnings

## Source Coverage
## Parse Warnings
## Privacy Warnings
## Sampling Limits
## Dependency Warnings
## Model Signal Limits
## Skipped Steps
```

## User Habits Evidence Table

`user-habits/evidence-table.csv` columns:

`claim_id`, `claim`, `category`, `preference_source_type`, `preference_scope_type`,
`drift_status`, `memory_status`, `strength`, `evidence_types`, `agent_scope`,
`project_scope`, `time_scope`, `sample_count`, `supporting_refs`, `uncertainty`, `privacy_note`

Use `id`, `path_hash`, or segment IDs in `supporting_refs` — not full local paths or raw text.

## Agent Behavior Evidence Table

`agent-behavior/evidence-table.csv` columns:

`finding_id`, `actual_model_bucket`, `displayed_model_signal`, `agent_tool`,
`behavior_dimension`, `observed_pattern`, `frequency_or_rate`, `strength`,
`supporting_refs`, `failure_modes`, `limits`, `privacy_note`

Use this separate schema, not the user preference schema.

## Data Categories

`user-habits/data-categories.json`:
```json
{
  "analysis_scope": {},
  "user_habit_categories": [],
  "negative_preference_categories": [],
  "quantitative_signal_categories": [],
  "memory_quality_categories": [],
  "privacy_categories": [],
  "derived_artifact_options": []
}
```

`agent-behavior/data-categories.json`:
```json
{
  "model_grouping": {},
  "behavior_dimensions": [],
  "model_buckets": [],
  "cross_model_patterns": [],
  "failure_modes": [],
  "not_comparable_notes": [],
  "privacy_and_boundary_notes": []
}
```

Category entries should include concise summaries and evidence references — no raw full paths or transcript text.
