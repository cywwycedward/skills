# Agent History Analyzer Implementation Design

Status: split design index for a public Codex skill.

This file is the overview and navigation layer. Detailed rules live in the linked
reference files. Avoid duplicating rules across files; update the owning reference
when a decision changes.

## Purpose

Build a user-invoked skill that analyzes local Codex and Claude Code conversation
history and memory to infer usage habits. Version 1 covers Codex and Claude Code.
Other agent tools may be added later through the same corpus model.

Primary output: a privacy-safe report package under the skill-local `.output/`
directory. The default analysis is user habits; optional agent behavior analysis is
off by default and must be explicitly enabled by the user.

## Runtime Flow

1. Confirm scope: Codex, Claude Code, or both; current project, all projects, or
   user-specified paths; ask whether to enable agent behavior analysis.
2. Inventory only transcript and memory candidates.
3. Let the agent create the sampling plan.
4. Extract selected, redacted text into working files.
5. Use text profiling as quantitative support when useful.
6. Deep read sampled content.
7. Save the privacy-safe report package.

## Reference Files

- [source-locations.md](source-locations.md): corpus model, path discovery, Codex and
  Claude Code source locations, and local/online confirmation gates.
- [script-interfaces.md](script-interfaces.md): uv setup, script dependency policy,
  `history_inventory.py`, `text_profile.py`, and working-file schemas.
- [user-habits-design.md](user-habits-design.md): research design for user
  collaboration preferences and habit reporting.
- [agent-behavior-design.md](agent-behavior-design.md): optional trace-based agent
  behavior design grouped by actual/effective model.
- [model-field-map.md](model-field-map.md): implementation gate for displayed model
  and actual/effective model field mapping.
- [report-schemas.md](report-schemas.md): output directory layout, report sections,
  evidence tables, data category schemas, and warnings format.
- [research-confirmations.md](research-confirmations.md): online and local research
  confirmations captured on 2026-06-27.

## Core Guardrails

- Analyze conversation transcripts and memory only.
- Exclude configuration files, rule files, project source code, git history,
  credentials, and environment files.
- Do not quote raw private transcript content by default.
- Report sensitive content by category and count, not by raw value.
- Do not output psychological profiles, personality judgments, or
  sensitive-attribute inferences.
- Treat local model fields as recorded signals unless the confirmed model field map
  classifies them as actual/effective model evidence.

## Implementation Gates

Before implementation is considered complete:

- Refresh online documentation for Codex, Claude Code, uv, text analysis methods,
  privacy/redaction methods, and agent trajectory evaluation methods. Current
  confirmation date: 2026-06-27; see `research-confirmations.md`.
- Inspect local Codex and Claude transcript shapes. Current local inspection date:
  2026-06-27; see `research-confirmations.md`.
- Create and validate the canonical `model-field-map.md` reference before enabling
  model-grouped agent behavior analysis.
- Create `scripts/pyproject.toml` and commit `scripts/uv.lock`.
- Implement scripts without committing `scripts/.venv/`.
- Validate that default report outputs do not persist raw transcript text.

## Current Decisions

- Skill invocation: user-invoked with `disable-model-invocation: true`.
- Output location: `skills/public/agent-history-analyzer/.output/YYYY-MM-DD-summary/`.
- `.output/` and `scripts/.venv/` are ignored by the skill-local `.gitignore`.
- User habits and agent behavior use separate research designs, report structures,
  evidence tables, and data category schemas.
- `text_profile.py` reads agent-extracted `selected_text.jsonl`; it does not parse
  raw Codex or Claude transcript schemas.

When the user answers a new design question, update the owning reference file and
adjust this index only if navigation or top-level status changes.
