# Report Schemas

Reference for output directory layout, report sections, evidence tables, and data category schemas.
Read before saving the final report package.

## Output Location

Save under `skills/public/agent-history-analyzer/.output/YYYY-MM-DD-summary/`.

- `YYYY-MM-DD`: date of analysis
- `summary`: short, ASCII, filename-safe, privacy-safe label (do not use raw private names)
- `.output/` is git-ignored

## Report Language And Translation

The initial reports use the language chosen during Initialize and keep the default
filenames `report.md` and `warnings.md`.

When the user later requests another language, create derived files beside the source
report: `report-{lang}.md` for reports and `warnings-{lang}.md` for root warnings,
where `{lang}` is an ASCII filename-safe language tag such as `en` or `zh-CN`.

Derived language outputs translate existing report content only. Do not re-inventory,
resample, deep read, rerun profiling, reinterpret evidence, add conclusions, remove
conclusions, or strengthen claims during translation. Preserve technical fields,
JSON and CSV field names, claim IDs, finding IDs, evidence IDs, supporting ref IDs,
filenames, directory names, model names, tool names, agent names, and command names.
If explanation is needed, label it as explanation, not translation.

## Directory Structure

Use this artifact layout. Keep intermediate files and place them by derivation role:
`inventory/` for corpus discovery and sampling, `analysis/` for selected text and
derived profile or event intermediates, `evidence/` for files cited by reports, and
`runtime/` for warnings or run-state records.

`inventory/inventory.jsonl` retains detailed inventory fields such as `path` and
`content_sha256`. Branch `analysis/selected_text.jsonl` files retain selected
`redacted_text`; `agent-behavior/analysis/behavior_events.jsonl` retains event-level
behavior records.

Canonical artifact paths:

| Path | Role | Required when |
|------|------|---------------|
| `report.md` | root report | always |
| `report-{lang}.md` | translated root report | requested |
| `warnings.md` | root warnings report | always |
| `warnings-{lang}.md` | translated root warnings report | requested |
| `inventory/inventory_summary.json` | inventory evidence | always after inventory |
| `inventory/sampling_plan.json` | sampling audit trail | always after sampling |
| `inventory/inventory.jsonl` | retained inventory detail | always after inventory |
| `inventory/warnings.json` | inventory runtime status | always after inventory |
| `user-habits/report.md` | user habit report | always |
| `user-habits/report-{lang}.md` | translated user habit report | requested |
| `user-habits/evidence/evidence-table.csv` | user habit evidence | always |
| `user-habits/evidence/data-categories.json` | user habit data categories | always |
| `user-habits/evidence/text_profile_summary.json` | user habit profile summary | text profiling run |
| `user-habits/analysis/selected_text.jsonl` | user habit profile input | text profiling run |
| `user-habits/analysis/term_frequency.csv` | user habit profile output | text profiling run |
| `user-habits/analysis/ngram_frequency.csv` | user habit profile output | text profiling run |
| `user-habits/analysis/tfidf_terms.csv` | user habit profile output | text profiling run |
| `user-habits/analysis/cooccurrence.csv` | user habit profile output | text profiling run |
| `user-habits/runtime/text_profile_warnings.json` | user habit profile runtime status | text profiling run |
| `agent-behavior/report.md` | agent behavior report | agent behavior enabled |
| `agent-behavior/report-{lang}.md` | translated agent behavior report | requested |
| `agent-behavior/evidence/evidence-table.csv` | agent behavior evidence | agent behavior enabled |
| `agent-behavior/evidence/data-categories.json` | agent behavior data categories | agent behavior enabled |
| `agent-behavior/evidence/text_profile_summary.json` | agent behavior profile summary | agent behavior text profiling run |
| `agent-behavior/analysis/selected_text.jsonl` | agent behavior profile input | agent behavior text profiling run |
| `agent-behavior/analysis/behavior_events.jsonl` | agent behavior event coding input | agent behavior enabled |
| `agent-behavior/analysis/term_frequency.csv` | agent behavior profile output | agent behavior text profiling run |
| `agent-behavior/analysis/ngram_frequency.csv` | agent behavior profile output | agent behavior text profiling run |
| `agent-behavior/analysis/tfidf_terms.csv` | agent behavior profile output | agent behavior text profiling run |
| `agent-behavior/analysis/cooccurrence.csv` | agent behavior profile output | agent behavior text profiling run |
| `agent-behavior/runtime/text_profile_warnings.json` | agent behavior profile runtime status | agent behavior text profiling run |

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
`## Method` must answer:

- How many samples were selected?
- Which agent tools, time spans, and project buckets were covered?
- Which mandatory coverage slots were sampled or waived?
- Which conditional high-value events were sampled?
- What was not sampled?
- Why was full-corpus reading not performed?
- How do sampling limits affect claim strength, drift, memory validation, and
  optional agent-behavior comparison?

`## Quantitative Signals` must explain that counts are pattern signals, not literal
user preference counts. Put the strongest useful counts in prose and link them to
evidence rows so readers do not have to inspect CSV files to understand support.

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

## Sampling Plan Schema

`inventory/sampling_plan.json` records the audit trail for sample selection:

```json
{
  "inventory_summary_ref": "inventory/inventory_summary.json",
  "mandatory_coverage": [],
  "conditional_coverage": [],
  "selected_samples": [],
  "not_sampled": [],
  "full_corpus_reading": {"performed": false, "reason": ""}
}
```

Mandatory coverage slots:

- all memory files in scope
- history file if available
- each in-scope agent tool with recent sessions
- each in-scope agent tool with oldest sessions
- each in-scope agent tool with largest sessions
- requested project buckets with candidates

Each mandatory slot must be represented as sampled or waived with a reason.

Conditional coverage slots:

- warning-heavy sessions
- correction-heavy sessions
- verification-heavy sessions
- privacy/security-related sessions
- failed, retried, reverted, interrupted, or resumed sessions
- project bucket coverage gaps
- high-value preference events
- model bucket coverage when agent behavior is enabled
- comparable task coverage when agent behavior comparison is requested

Each `selected_samples` entry includes `inventory_id`, `agent_tool`,
`source_type`, `project_bucket`, `time_bucket`, `size_bucket`, `sample_reason`,
and `supporting_ref`. Use one or more `sample_reason` values from this set:

```text
recent
oldest
largest
small
memory
history_file
project_bucket_coverage
warning_pattern
correction_pattern
verification_pattern
privacy_security_pattern
failed_retried_interrupted
high_value_preference_event
agent_tool_coverage
model_bucket_coverage
comparable_task_coverage
```

## Report Package Verification

Before the final response:

- Required reports exist: root `report.md`, `warnings.md`,
  `inventory/inventory_summary.json`, `inventory/sampling_plan.json`,
  `user-habits/report.md`, `user-habits/evidence/evidence-table.csv`, and
  `user-habits/evidence/data-categories.json`; agent behavior files exist when
  that branch is enabled.
- JSON files parse.
- CSV evidence tables have headers and at least one data row unless the branch was
  explicitly skipped and recorded in `warnings.md`.
- `warnings.md` contains every required section.
- Generated files are in the declared `inventory/`, `analysis/`, `evidence/`, or
  `runtime/` directory for their branch. No generated intermediate files remain loose
  in the package root or branch root.
- If agent behavior is enabled, model signal limits are stated.
- The final response links the report files and states this verification evidence.

## User Habits Evidence Table

`user-habits/evidence/evidence-table.csv` columns:

`claim_id`, `claim`, `category`, `preference_source_type`, `preference_scope_type`,
`drift_status`, `memory_status`, `strength`, `evidence_types`, `agent_scope`,
`project_scope`, `time_scope`, `sample_count`, `supporting_refs`, `uncertainty`, `privacy_note`

Use `id`, `path_hash`, or segment IDs in `supporting_refs` — not full local paths or raw text.

## Agent Behavior Evidence Table

`agent-behavior/evidence/evidence-table.csv` columns:

`finding_id`, `actual_model_bucket`, `displayed_model_signal`, `agent_tool`,
`behavior_dimension`, `observed_pattern`, `frequency_or_rate`, `strength`,
`completion_vs_verification`, `supporting_refs`, `failure_modes`, `limits`,
`privacy_note`

Use this separate schema, not the user preference schema.

## Data Categories

`user-habits/evidence/data-categories.json`:
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

`agent-behavior/evidence/data-categories.json`:
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
