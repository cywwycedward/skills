# Model Field Map

Confirmed field mappings for displayed model and recorded/effective model signals in
Codex and Claude Code conversation records. Confirmed on 2026-06-27.

Read this reference before enabling model-grouped agent behavior analysis. During normal
skill use, use this map rather than re-researching field semantics.

## Model Signal Levels

1. **Displayed model** — UI or status-line model name. Do not use as primary grouping key.
2. **Recorded/effective model** — Model slug, alias, provider, or reasoning effort field
   in local transcript events. May be used as evidence after this map confirms semantics.
3. **Actual backend model** — The model that truly served a request. Usually cannot be
   proven from local transcripts alone.

## Current Reporting Rule

Group agent behavior by confirmed recorded/effective model signals. Local transcripts do
not prove the actual backend model for every turn — do not label these fields as
backend-truth evidence.

If a tool or version does not expose actual/effective model evidence, report that bucket
as `unknown_actual_model` instead of using displayed model.

## Confirmed Mapping Table

| Tool | Signal Type | Level | Field/Event | Extraction Rule |
|------|-------------|-------|-------------|-----------------|
| Codex | recorded/effective model | turn context | `type == "turn_context"`, `payload.model` | Use `payload.model` as primary bucket for the session until next `turn_context` changes it. If missing, use `unknown_actual_model`. |
| Codex | recorded provider | session meta | `type == "session_meta"`, `payload.model_provider` | Attach as explanatory metadata. Do not use provider alone as model bucket. |
| Codex | reasoning effort | turn context | `payload.effort`; fallback `payload.collaboration_mode.settings.reasoning_effort` | Store as effort metadata, not model id. If both missing, leave null. |
| Claude Code | recorded/effective model | assistant message | `type == "assistant"`, `message.model` | Use `message.model` as primary bucket for the assistant message. Report slugs as-is. If missing, use `unknown_actual_model`. |
| Claude Code | requested subagent model | tool call | `type == "assistant"`, `message.content[].input.model` | Treat as requested model argument, not primary grouping evidence. |
| Claude Code | resolved subagent model | tool result | `type == "user"`, `toolUseResult.resolvedModel` | Use as explanatory evidence when present. Sparse field — do not assume every run has it. |

## Runtime Validation

At execution time, inventory key counts before using this map. If the local corpus no
longer contains these fields or field paths conflict, record a `Model Signal Limits`
warning and group affected behavior as `unknown_actual_model`.

Claude Code documents its JSONL shape as internal and subject to change between versions.
Scripts must be format-tolerant and warnings-first.
