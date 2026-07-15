# Model Field Map

Status: locally confirmed on 2026-06-27 for recorded/effective model signals.
Actual backend model proof remains unconfirmed.

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
- Document both displayed model fields and recorded/effective model fields, when they
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

Agent behavior may be grouped by confirmed recorded/effective model signals. Local
transcripts do not prove the actual backend model for every turn, so reports must not
label these fields as backend-truth evidence unless a future provider-level source is
added.

## Confirmed Mapping Table

Confirmed from official documentation and local inspection on 2026-06-27. See
`research-confirmations.md` for source URLs and aggregate counts.

| Tool | Version/Surface | Signal Type | Level | Field/Event | Scope | Extraction Rule | Alias/Fallback Handling | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | CLI/local session JSONL, inspected 2026-06-27 | recorded/effective model | turn/session context | `type == "turn_context"`, `payload.model` | Turn context rows; observed in all 142 inspected session files | Use `payload.model` as the primary Codex model bucket for rows in the same turn context until a later `turn_context` changes it | Do not resolve aliases locally. Report the recorded slug as-is. If missing, use `unknown_actual_model`. | medium | Observed local value: `gpt-5.5`. This is a recorded local signal, not backend proof. |
| Codex | CLI/local session JSONL, inspected 2026-06-27 | recorded provider | session metadata | `type == "session_meta"`, `payload.model_provider` | Session metadata rows | Attach provider as explanatory metadata for the session; do not use provider alone as model bucket | Values are provider ids such as `custom` or `openai`; do not infer backend model from provider id | medium | Present in all inspected session metadata records. |
| Codex | CLI/local session JSONL, inspected 2026-06-27 | reasoning effort | turn/session context | `type == "turn_context"`, `payload.effort`; fallback `payload.collaboration_mode.settings.reasoning_effort` | Turn context rows | Store with the model bucket as effort metadata, not as a model id | If `payload.effort` is missing, use `payload.collaboration_mode.settings.reasoning_effort`; if both missing, leave null | medium | Observed values included `medium`, `high`, `xhigh`, and null-like records. |
| Codex | CLI/local session JSONL, inspected 2026-06-27 | duplicate model setting | turn/session context | `type == "turn_context"`, `payload.collaboration_mode.settings.model` | Turn context rows | Use only as a consistency check against `payload.model`; do not create a separate bucket | If it disagrees with `payload.model`, record a model signal warning | medium | Matched `payload.model` in inspected corpus. |
| Claude Code | CLI/local transcript JSONL, inspected 2026-06-27 | recorded/effective model | assistant message | `type == "assistant"`, `message.model` | Assistant message rows; turn-level for assistant output | Use `message.model` as the primary Claude Code model bucket for the assistant message | Report recorded slugs as-is. Do not resolve aliases unless official docs and local fields provide the resolved value. If missing, use `unknown_actual_model`. | high | Present on all 19,632 inspected assistant records. Claude docs state JSONL format is internal and may change. |
| Claude Code | CLI/local transcript JSONL, inspected 2026-06-27 | requested subagent/tool model | assistant tool call | `type == "assistant"`, `message.content[].input.model` | Tool-call content rows | Treat as a requested model argument for subagents/tools, not the assistant message model bucket | Values may be aliases such as `sonnet`, `haiku`, or `opus`; do not treat as resolved model | medium | Useful for tool trajectory notes. Not primary grouping evidence. |
| Claude Code | CLI/local transcript JSONL, inspected 2026-06-27 | resolved subagent/tool model | tool result | `type == "user"`, `toolUseResult.resolvedModel` | Tool-result rows | Use as explanatory evidence for subagent/tool execution when present | Report as recorded; suffixes such as `[1M]` or `[1m]` should be preserved or normalized only in a separate display field | medium | Sparse field. Do not assume every subagent/tool run has it. |
| Claude Code | status line command input, official docs checked 2026-06-27 | displayed/status model | live status-line JSON | `model.id`, `model.display_name` | Status-line command input, not transcript JSONL | Use only if the skill explicitly captures status-line input or the user provides it; otherwise do not rely on it for transcript grouping | `model.display_name` is displayed label; `model.id` is stronger than display name but still not transcript evidence unless captured | medium | Official docs confirm this field, but local transcript grouping should use `message.model`. |

## Confirmed Online Notes

- Codex official configuration docs document `model`, `model_provider`, and reasoning
  effort settings.
- Claude Code official model configuration docs document model aliases, model
  settings, fallback chains, and automatic fallback behavior.
- Claude Code official status-line docs document `model.id` and `model.display_name`
  in status-line command input.
- Claude Code official session docs warn that transcript JSONL entries are internal
  and can change between versions.

## Runtime Validation Rule

At execution time, still inventory key counts before using this map. If the local
corpus no longer contains these fields, or if field paths conflict with this map,
record a `Model Signal Limits` warning and group affected behavior as
`unknown_actual_model`.
