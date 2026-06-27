# Research Confirmations

Status: confirmed on 2026-06-27 from online documentation and local inspection.

This file records research that should not be repeated during normal skill use unless
the local environment or upstream tool versions have changed materially.

## Online Sources Checked

- Codex manual: `https://developers.openai.com/codex/codex-manual.md`
- Codex CLI features: `https://developers.openai.com/codex/cli/features`
- Codex memories: `https://developers.openai.com/codex/memories`
- Codex advanced configuration: `https://developers.openai.com/codex/config-advanced`
- Codex configuration reference: `https://developers.openai.com/codex/config-reference`
- Claude Code sessions: `https://code.claude.com/docs/en/sessions`
- Claude Code memory: `https://code.claude.com/docs/en/memory`
- Claude Code model configuration: `https://code.claude.com/docs/en/model-config`
- Claude Code status line: `https://code.claude.com/docs/en/statusline`
- uv installation: `https://docs.astral.sh/uv/getting-started/installation/`
- scikit-learn text feature extraction and `TfidfVectorizer` API:
  `https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction`
  and
  `https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html`
- pandas CSV output:
  `https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html`
- jieba tokenizer:
  `https://github.com/fxsjy/jieba`
- Microsoft Presidio:
  `https://microsoft.github.io/presidio/` and
  `https://microsoft.github.io/presidio/analyzer/`
- ReAct:
  `https://arxiv.org/abs/2210.03629`
- Agent evaluation survey:
  `https://arxiv.org/html/2503.16416v2`
- Microsoft Human-AI Interaction Guidelines:
  `https://www.microsoft.com/en-us/research/project/guidelines-for-human-ai-interaction/`
- NIST AI RMF trustworthiness characteristics:
  `https://airc.nist.gov/airmf-resources/airmf/3-sec-characteristics/`

## Local Environment Checked

- OS: WSL2 Linux.
- Shell: `/bin/bash`.
- `CODEX_HOME`: unset, so use the Codex default `~/.codex`.
- `CLAUDE_CONFIG_DIR`: unset, so use the Claude Code default `~/.claude`.
- `uv`: available at `~/.local/bin/uv`, version `0.10.9`.
- `jq`: unavailable during inspection; JSONL structure was inspected with Python.

## Codex Local Findings

Local Codex state exists at `~/.codex`.

Observed candidate sources:

- `~/.codex/sessions/`: present, 142 JSONL files.
- `~/.codex/history.jsonl`: present, 470 valid JSONL rows.
- `~/.codex/memories/`: present, 0 files in this environment.
- `~/.codex/archived_sessions/`: not present in this environment.

Codex session JSONL aggregate:

- Files inspected: 142.
- Rows inspected: 51,228.
- Parse failures: 0.
- Top-level shape: every row had `timestamp`, `type`, and `payload`.
- Record types: `event_msg`, `response_item`, `turn_context`, `session_meta`,
  and `compacted`.

Codex model signals:

- `turn_context.payload.model` existed in all 142 inspected session files.
- `turn_context.payload.collaboration_mode.settings.model` also existed and matched
  the same local model value in the inspected corpus.
- `turn_context.payload.effort` and
  `turn_context.payload.collaboration_mode.settings.reasoning_effort` recorded
  reasoning-effort-like values.
- `session_meta.payload.model_provider` existed in all inspected session metadata
  records.
- `session_meta.payload.model` and `session_meta.payload.effort` were not present in
  the inspected corpus.

Confirmed local Codex model values in this environment were `gpt-5.5`; provider
values were mostly `custom` with a small number of `openai` records. Treat these as
recorded local signals, not proof of the backend model.

Codex `history.jsonl` aggregate:

- Rows inspected: 470.
- Parse failures: 0.
- Shape: `session_id`, `text`, `ts`.
- This file can inventory prior prompts or session references, but it is not a full
  transcript replacement.

## Claude Code Local Findings

Local Claude Code state exists at `~/.claude`.

Observed candidate sources:

- `~/.claude/projects/<project>/*.jsonl`: present.
- `~/.claude/projects/<project>/<session-id>/subagents/*.jsonl`: present.
- `~/.claude/projects/<project>/memory/*.md`: present in one project, 6 Markdown
  files.

Claude transcript JSONL aggregate:

- Files inspected: 391.
- Parse failures: 0.
- Common record types included `assistant`, `user`, `attachment`, `mode`,
  `last-prompt`, `permission-mode`, `system`, `file-history-snapshot`, `ai-title`,
  `queue-operation`, `agent-name`, and `worktree-state`.

Claude model signals:

- Every inspected `assistant` record had `message.model`.
- `user.toolUseResult.resolvedModel` appeared on some tool-result records.
- `assistant.message.content[].input.model` appeared on some assistant tool-call
  records. Treat this as a requested subagent/tool model argument, not the primary
  model of the assistant message.
- Confirmed local `message.model` values included Claude model slugs and non-Anthropic
  provider slugs. Treat these as recorded/effective local transcript signals.

Claude auto memory:

- Auto-memory files were found under
  `~/.claude/projects/<project>/memory/`.
- The observed directory contained `MEMORY.md` plus topic Markdown files.

## Online Confirmation Summary

Codex:

- Official docs confirm local state under `CODEX_HOME`, defaulting to `~/.codex`.
- Official docs confirm `history.jsonl` under `CODEX_HOME` when history persistence is
  enabled.
- Official docs confirm Codex memories under `~/.codex/memories/` by default.
- Official docs confirm model and model-related configuration keys, but local
  transcript inspection is still required for transcript field shapes.

Claude Code:

- Official docs confirm CLI transcripts at
  `~/.claude/projects/<project>/<session-id>.jsonl`.
- Official docs explicitly state the JSONL entry format is internal and may change.
- Official docs confirm auto memory under
  `~/.claude/projects/<project>/memory/` by default.
- Official docs confirm status-line input includes `model.id`, `model.display_name`,
  `session_id`, and `transcript_path`.
- Official docs confirm model aliases, model settings, fallback chains, and fallback
  notices, but local transcript fields remain the source for sampled report grouping.

uv:

- Official docs confirm standalone installer, PyPI/pipx, Homebrew, WinGet, Scoop,
  Docker, GitHub Releases, and Cargo installation paths.
- Because uv is already installed locally, this environment does not need an install
  prompt before script dependency setup.

Text profiling:

- scikit-learn confirms bag-of-words, token counting, n-grams, and TF-IDF-style
  vectorization support.
- scikit-learn documents `stop_words=None` as default and warns about known issues
  with the built-in English stop list.
- jieba confirms default precise-mode Chinese tokenization through `jieba.cut` and
  list output through `jieba.lcut`.
- pandas confirms `DataFrame.to_csv` for CSV output.

Privacy and redaction:

- NIST AI RMF supports privacy-enhanced AI through data minimization,
  de-identification, aggregation, and tradeoff-aware risk handling.
- Microsoft Presidio supports PII detection and anonymization with recognizers,
  regex, NER, context, and custom recognizers.
- Presidio documentation warns automated detection cannot guarantee finding all
  sensitive information. This supports keeping manual review and output leak checks
  in the skill workflow.

Agent behavior methods:

- ReAct supports analyzing interleaved reasoning/action/tool-use trajectories.
- The agent evaluation survey distinguishes final-response, stepwise, and
  trajectory-based assessment; it also notes trajectory evaluation can be
  reference-based or reference-free and each has tradeoffs.
- Microsoft Human-AI Interaction Guidelines are a relevant framework for interaction
  behavior and recovery from errors.
- NIST AI RMF characteristics are relevant to safety, privacy, transparency, and
  trustworthiness coding.

## Remaining Limits

- Local transcript fields cannot prove the actual backend model for every request.
  Reports must call these `recorded/effective model` signals unless external provider
  evidence is available.
- Claude Code JSONL is documented as internal and unstable. The inventory script must
  count keys and warn on unknown shapes instead of failing on schema drift.
- Codex transcript schema is also treated as local state rather than a stable public
  API. Field extraction must be versioned by inspection date and local CLI version
  when available.
- Local findings are from this user's current machine only. Other machines, OSes,
  managed settings, or tool versions can differ.
