# Model Field Map

Status: implementation gate. The actual field mapping is not yet confirmed.

This reference will own confirmed field mappings for displayed model and
actual/effective model signals in Codex and Claude Code conversation records.

## Purpose

Agent behavior reporting is expected to group behavior by actual/effective model. This
reference must document how to extract that grouping from supported transcript formats
before model-grouped agent behavior analysis is enabled.

During normal skill use, the agent should read this confirmed mapping rather than
re-researching field semantics.

## Model Signal Levels

1. Displayed model
   - A user-interface or status-line model name.
   - Do not use it as the primary model grouping key.

2. Recorded/effective model
   - A model slug, alias, provider, reasoning effort, or related field recorded in
     local transcript events.
   - May be usable as actual/effective model evidence only after this map confirms
     the semantics.

3. Actual backend model
   - The model that truly served a request on the provider backend.
   - Usually cannot be proven from local transcripts alone unless documentation and
     local traces provide a reliable signal.

## Research Requirement

Before the skill is considered implemented:

- Research and document whether Codex and Claude Code conversation records contain
  model-related fields.
- Document both displayed model fields and actual/effective model fields, when they
  exist.
- Document exact field names, event names, extraction logic, alias/fallback handling,
  and whether each signal is session-level or turn-level.
- Confirm the mapping with online documentation research and local transcript
  inspection.
- Store the confirmed mapping in this file before enabling model-grouped agent
  behavior analysis.
- If the confirmed mapping says a tool or version does not expose actual/effective
  model evidence, report that bucket as `unknown_actual_model` instead of using
  displayed model.

## Current Reporting Rule

Agent behavior may correlate with recorded model signals, but local transcripts
usually cannot prove the actual backend model for every turn.

## Placeholder Mapping Table

Fill this table during implementation.

| Tool | Version/Surface | Signal Type | Level | Field/Event | Scope | Extraction Rule | Alias/Fallback Handling | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | unknown | Pending |
| Claude Code | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | NEEDS_LOCAL_CONFIRMATION | unknown | Pending |

NEEDS_ONLINE_CONFIRMATION: refresh Codex and Claude documentation for current model
configuration, alias, fallback, hook, and status-line behavior.

NEEDS_LOCAL_CONFIRMATION: inspect local transcripts to determine whether per-session
or per-turn model fields exist in the user's actual data.
