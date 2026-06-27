# Report Schemas

This reference owns output directory layout, report sections, evidence table schemas,
data category schemas, and warning sections.

## Default Output

Default output: a privacy-safe research package.

The default package includes:

- Root privacy-safe written overview.
- Detailed `user-habits/` report directory.
- Optional detailed `agent-behavior/` report directory.
- Evidence tables with strength, source type, coverage, and uncertainty.
- Data categorization files that organize findings by analysis-specific categories.

The default package is the base artifact. After producing it, the skill may generate
additional analysis or presentation artifacts when the user asks for them, such as:

- User preference profile.
- Recommended updates to agent instructions or memory, without applying them.
- Frequency tables.
- Time trends.
- Bar charts from CSV/JSON data.
- Word cloud, only as an illustrative artifact, not core evidence.
- Agent behavior report directory, if explicitly requested.

## Persistent Output

- Save the default report package under
  `skills/public/agent-history-analyzer/.output/<report-name>/`.
- Treat `.output/` as a skill-local generated output directory, not source.
- Add a skill-local `.gitignore` that ignores `.output/`.
- Use report name format `YYYY-MM-DD-summary`.
- Let the agent choose `summary` from the analysis topic, but keep it short, ASCII,
  filename-safe, and privacy-safe.
- Do not include raw private names, repository names, customer names, account names,
  or secret-like values in the report directory name.
- Store only the privacy-safe report package by default.
- Do not persist raw transcript excerpts or unredacted intermediate text unless the
  user explicitly asks for that higher-risk output.
- Script outputs that contain only inventory, aggregate metrics, warnings, or
  redacted text statistics may be saved inside the same report directory.

## Directory Structure

```text
skills/public/agent-history-analyzer/.output/YYYY-MM-DD-summary/
|-- report.md
|-- inventory_summary.json
|-- warnings.md
|-- user-habits/
|   |-- report.md
|   |-- evidence-table.csv
|   |-- data-categories.json
|   `-- text_profile_summary.json
`-- agent-behavior/
    |-- report.md
    |-- evidence-table.csv
    |-- data-categories.json
    `-- text_profile_summary.json
```

Create `agent-behavior/` only when optional agent behavior analysis is enabled.

Root `report.md` is the combined overview. The detailed user habit analysis lives in
`user-habits/`. The detailed assistant/agent behavior analysis lives in
`agent-behavior/` only when requested.

Root `report.md` is an executive overview, navigation surface, and caveat summary. It
should not duplicate all details from child reports.

The user habit analysis and optional agent behavior analysis use different research
designs. Keep their report structures, evidence tables, and data category schemas
separate.

## Root Report

Root `report.md` required sections:

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

If agent behavior analysis is enabled, add:

```md
## Agent Behavior Appendix
```

## User Habits Evidence Table

`user-habits/evidence-table.csv` columns:

- `claim_id`
- `claim`
- `category`
- `preference_source_type`
- `preference_scope_type`
- `drift_status`
- `memory_status`
- `strength`
- `evidence_types`
- `agent_scope`
- `project_scope`
- `time_scope`
- `sample_count`
- `supporting_refs`
- `uncertainty`
- `privacy_note`

`supporting_refs` should use inventory IDs, path hashes, or segment IDs. Do not put
full local paths or raw transcript text in `supporting_refs`.

## Agent Behavior Evidence Table

`agent-behavior/evidence-table.csv` columns:

- `finding_id`
- `actual_model_bucket`
- `displayed_model_signal`
- `agent_tool`
- `behavior_dimension`
- `observed_pattern`
- `frequency_or_rate`
- `strength`
- `supporting_refs`
- `failure_modes`
- `limits`
- `privacy_note`

Use this schema for agent behavior findings. Do not reuse the user preference evidence
schema for agent behavior.

## User Habits Data Categories

`user-habits/data-categories.json` top-level structure:

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

Use `data-categories.json` as the machine-readable classification framework and
summary, not as a raw evidence dump. Category entries should include concise summaries,
evidence references, and uncertainty notes without full local paths or raw transcript
text.

## Agent Behavior Data Categories

`agent-behavior/data-categories.json` top-level structure:

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

Use this separate structure for agent behavior rather than the user preference
classification structure.

## Warnings

`warnings.md` required sections:

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

## Optional Derived Artifacts

Optional derived artifacts may add:

- `charts/`
- `tables/`
- `word-cloud.*`
