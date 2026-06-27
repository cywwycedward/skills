---
name: agent-history-analyzer
description: "Analyze local Codex and Claude Code conversation history and memory to infer user usage habits, with privacy-preserving corpus handling."
disable-model-invocation: true
---

# Agent History Analyzer

Use this user-invoked skill only when the user explicitly asks to analyze local agent
conversation history or memory, especially Codex and Claude Code history, to infer
usage habits, collaboration preferences, workflow patterns, privacy boundaries, or
optional assistant behavior patterns.

Before running the workflow, read these references:
- [references/source-locations.md](references/source-locations.md) — corpus discovery, include/exclude rules
- [references/script-interfaces.md](references/script-interfaces.md) — script CLI interfaces and output schemas
- [references/report-schemas.md](references/report-schemas.md) — report output structure and evidence tables
- [references/model-field-map.md](references/model-field-map.md) — model field extraction rules (read before enabling agent behavior analysis)

## Guardrails

- Analyze conversation transcripts and memory only.
- Do not analyze configuration files, rule files, project source code, git history,
  credentials, or environment files.
- Do not quote raw private transcript content by default.
- Report sensitive content by category and count, not by raw value.
- Do not infer long-term habits from one isolated conversation unless clearly marked
  as weak evidence.
- Do not output psychological profiles, personality judgments, or sensitive-attribute
  inferences.
- Treat local model fields as recorded signals, not proof of the actual backend
  model.

## Workflow

### 1. Initialize

Confirm the analysis scope:

- Agent tools: Codex, Claude Code, or both.
- Scope: current project, all projects, or user-specified paths.
- Data roots: user-provided paths first; otherwise use standard Codex and Claude
  locations from the design reference.
- Ask whether to include optional agent behavior analysis. Keep it off unless the
  user explicitly says yes.

Completion criterion: the target corpus and optional branches are clear enough to
avoid broad filesystem searches.

### 2. Inventory

Before running scripts, ensure `uv` is available. If `uv` is missing, ask the user
whether to install it and recommend an installation method for the current OS based
on the official uv documentation. Do not install uv without explicit confirmation.

When script dependencies are needed, enter the `scripts/` directory, explain the
dependencies that will be installed, ask for confirmation, then run `uv sync`.

Use `scripts/history_inventory.py` when available. If the script is not implemented
or cannot run, perform the smallest equivalent manual inventory and record the gap in
`warnings.md`.

From the skill directory, run inventory with `cd scripts && uv run python history_inventory.py --agent both --output-dir ../.output/YYYY-MM-DD-summary`.

Inventory only candidate transcript and memory files. Exclude `AGENTS.md`,
`CLAUDE.md`, `.codex/config.toml`, Claude settings, MCP configuration, source code,
and project documentation.

Completion criterion: candidate files, excluded classes, parse warnings, time range,
and size range are known before reading transcript bodies.

### 3. Plan Sampling

Create a sampling plan from the inventory. The agent, not a script, chooses samples.
Prefer coverage across agent, project bucket, time period, session size, memory files,
and unusual warning patterns.

Ask the user before deep reading when the plan is full-corpus, high-cost, unusually
sensitive, or requires persisting unredacted text.

Completion criterion: the final report can disclose what was sampled, what was not,
and why.

### 4. Profile Text

Use `scripts/text_profile.py` when useful and available. Provide an explicit
`selected_text.jsonl` extracted by the agent from selected samples. Do not let the
script discover, traverse, or parse the full history corpus.

From the skill directory, run text profiling with `cd scripts && uv run python text_profile.py --input ../.output/YYYY-MM-DD-summary/selected_text.jsonl --output-dir ../.output/YYYY-MM-DD-summary/user-habits`.

Use text statistics as cues. Counts suggest where to look; close reading decides what
it means.

Completion criterion: quantitative signals are available, or the report explains why
text profiling was skipped.

### 5. Deep Read

Read sampled transcript and memory content with privacy in mind. Analyze user habits:

- Collaboration preferences.
- Planning and autonomy expectations.
- Risk and privacy boundaries.
- Verification habits.
- Tool preferences.
- Recurring correction patterns.
- Output preferences.
- Memory quality and conflicts.

If agent behavior analysis is enabled, analyze assistant messages, tool use,
validation behavior, self-correction, and recorded model/provider signals separately.

Completion criterion: every major claim has evidence strength, source type, coverage,
and uncertainty.

### 6. Save Report Package

Create `.output/YYYY-MM-DD-summary/` inside this skill directory. Keep `summary`
short, ASCII, filename-safe, and privacy-safe.

Default files:

```text
report.md
inventory_summary.json
warnings.md
user-habits/
agent-behavior/  # only when enabled
```

Do not persist raw transcript excerpts or unredacted intermediate text unless the
user explicitly requests that higher-risk output.

## Examples

- "Analyze my current project's Codex and Claude history for my agent usage habits."
- "Analyze all projects, but do not include assistant behavior analysis."
- "Use the existing report package to generate charts and a concise preference
  profile."
