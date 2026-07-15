# Script Interfaces

This reference owns deterministic helper scripts, dependency management, and working
file schemas. Scripts inventory and profile the corpus; the agent conducts the study.

## Stable Script Boundary

Only code tasks that are stable, mechanical, and format-tolerant.

Do not script:

- User habit inference.
- Task type interpretation.
- Representative sampling decisions.
- Key segment extraction based on meaning.
- Theme generation.
- Memory accuracy judgments.
- Final report conclusions.

## Script Tooling And Dependencies

Decision: require `uv` for script dependency management.

Runtime setup flow:

1. Check whether `uv` is available.
2. If `uv` is missing, ask the user whether to install it.
3. Recommend the install method for the user's OS from the official uv installation
   documentation.
4. If the user confirms, install uv using the selected official method.
5. Enter `scripts/`.
6. Tell the user which dependencies will be installed.
7. Ask for confirmation before installing dependencies.
8. Run `uv sync` in `scripts/`.

Dependency packaging:

- Add `scripts/pyproject.toml` for script dependencies.
- Commit `scripts/uv.lock` after dependency resolution.
- Let `uv sync` create `scripts/.venv/` locally.
- Do not commit `scripts/.venv/`.
- Ignore `scripts/.venv/` in the skill-local `.gitignore`.

Official uv install options to recommend:

- Windows quick install: PowerShell standalone installer.
- Windows package managers: WinGet or Scoop, if the user prefers system package
  management.
- macOS/Linux quick install: standalone installer with `curl`; use `wget` if `curl`
  is unavailable.
- macOS package manager: Homebrew, if the user prefers Homebrew-managed tools.
- Python-tool install: `pipx install uv`, if the user already uses `pipx`.

Online confirmation on 2026-06-27:

- Official uv documentation lists standalone installers, PyPI/pipx, Homebrew,
  MacPorts, WinGet, Scoop, Docker, GitHub Releases, and Cargo installation options.
- Use https://docs.astral.sh/uv/getting-started/installation/ as the primary source
  before printing install commands in future runs.

Local confirmation on 2026-06-27:

- Current OS is WSL2/Linux.
- Shell is `/bin/bash`.
- `uv` is already installed at `~/.local/bin/uv`.
- Local uv version is `0.10.9`.

Runtime rule: if `uv` is already available, skip the install prompt. Still ask before
running `uv sync` because that installs project dependencies.

## Planned Script: `scripts/history_inventory.py`

Purpose: create a low-cost corpus map.

Stable responsibilities:

- Expand user-provided roots.
- Expand `CODEX_HOME` when present.
- Expand standard home locations for Codex and Claude.
- Enumerate candidate transcript and memory files.
- Exclude known rule/config/source files.
- Emit path, agent, source type, size, mtime, extension, readability, line count, and
  content hash.
- Validate JSONL files line by line as JSON without interpreting schema.
- Validate Markdown memory files as readable text without interpreting meaning.
- Count top-level JSON keys in JSONL rows.
- Emit parse warnings instead of failing on unknown fields.

Suggested outputs:

- Working file: `inventory.jsonl`
- Persistent report file: `inventory_summary.json`
- Persistent report file: `warnings.json`

The script must not output raw transcript text.

Minimum `inventory.jsonl` schema:

- `id`
- `agent`
- `source_type`
- `path`
- `path_hash`
- `project_bucket`
- `size_bytes`
- `mtime`
- `extension`
- `line_count`
- `readable`
- `jsonl_total_lines`
- `jsonl_valid_lines`
- `top_level_key_counts`
- `text_line_count`
- `content_sha256`
- `warnings`

Use `path_hash` for privacy-safe report references. The local output may include
`path` so the agent can read selected files, but final reports should default to `id`
and `path_hash` instead of full local paths.

Inventory persistence boundary:

- `inventory.jsonl` is a working file for agent execution.
- `inventory.jsonl` may include full local `path` and `content_sha256`.
- Do not persist `inventory.jsonl` inside the default report package unless the user
  explicitly asks for a full working manifest.
- `inventory_summary.json` is the default persistent artifact.
- `inventory_summary.json` must omit full local paths and content hashes.
- `inventory_summary.json` may include `id`, `path_hash`, `agent`, `source_type`,
  project bucket labels, size ranges, time ranges, counts, parse rates, and warnings.

Potential source types:

- `codex_session`
- `codex_archived_session`
- `codex_history`
- `codex_memory`
- `claude_session`
- `claude_project_memory`
- `user_specified_transcript`
- `user_specified_memory`

Local confirmation on 2026-06-27:

- Codex session JSONL: 142 files, 51,228 valid rows, 0 parse failures. Every row had
  top-level `timestamp`, `type`, and `payload`.
- Codex observed row types: `event_msg`, `response_item`, `turn_context`,
  `session_meta`, and `compacted`.
- Codex `history.jsonl`: 470 valid rows, 0 parse failures, with `session_id`, `text`,
  and `ts`.
- Claude transcript JSONL: 391 files, 0 parse failures. Common row types included
  `assistant`, `user`, `attachment`, `mode`, `last-prompt`, `permission-mode`,
  `system`, `file-history-snapshot`, `ai-title`, `queue-operation`, `agent-name`, and
  `worktree-state`.

Runtime rule: exact JSONL shapes and useful top-level keys must still be learned from
the current local corpus at runtime. The script should only count keys, not assign
semantics unless the field is clearly generic or documented in `model-field-map.md`.

## Planned Script: `scripts/text_profile.py`

Status: confirmed for version 1.

Purpose: provide deterministic text statistics that support, but do not replace,
close reading.

Stable responsibilities:

- Read selected, redacted text extracted by the agent.
- Separate role groups when reliable role signals exist.
- Default to user messages and memory when role signals are reliable.
- Optionally include assistant messages as a separate group.
- Exclude code blocks, tool output, and assistant long output when requested.
- Compute normalized term frequency.
- Compute n-gram frequency.
- Compute TF-IDF-style distinguishing terms.
- Compute coarse co-occurrence counts.
- Emit tokenization warnings.

Suggested outputs:

- `text_profile_summary.json`
- `term_frequency.csv`
- `ngram_frequency.csv`
- `tfidf_terms.csv`
- `cooccurrence.csv`
- `text_profile_warnings.json`

Output schemas:

`term_frequency.csv` columns:

- `group_id`
- `role`
- `token`
- `token_type`
- `count`
- `per_1000_tokens`
- `doc_count`

`ngram_frequency.csv` columns:

- `group_id`
- `role`
- `n`
- `ngram`
- `token_type`
- `count`
- `per_1000_tokens`
- `doc_count`

`tfidf_terms.csv` columns:

- `group_id`
- `role`
- `token`
- `token_type`
- `tfidf`
- `doc_count`

`cooccurrence.csv` columns:

- `group_id`
- `role`
- `term_a`
- `term_b`
- `window_size`
- `count`

`text_profile_summary.json` should include:

- total document count.
- total token count.
- token counts by group and role.
- dependency versions.
- tokenization method.
- excluded content counts.
- warning summary.

Input boundary:

- Accept `--input selected_text.jsonl`.
- Do not discover or traverse the full history corpus.
- Do not parse raw Codex or Claude transcript schemas.
- Do not decide which files are representative.
- The agent extracts selected, redacted text into `selected_text.jsonl` after choosing
  samples.
- Treat missing role/group fields as `unknown` and emit warnings instead of guessing
  aggressively.

Minimum `selected_text.jsonl` row schema:

```json
{
  "id": "sample-001",
  "inventory_id": "claude-0001",
  "source_type": "claude_session",
  "role": "user",
  "agent_tool": "claude",
  "actual_model_bucket": "unknown_actual_model",
  "displayed_model_signal": null,
  "behavior_dimension_hint": null,
  "group": {
    "agent": "claude",
    "project_bucket": "current",
    "time_bucket": "recent"
  },
  "redacted_text": "..."
}
```

`selected_text.jsonl` is a working file only. It may contain redacted private text and
must not be persisted in the default report package unless the user explicitly asks
for that higher-risk artifact.

For user-habits analysis, model fields may be null or `unknown_actual_model`. For
agent-behavior analysis, `actual_model_bucket` must be populated from the confirmed
`model-field-map.md` extraction rules when available.

Keep `selected_text_manifest.jsonl` as an optional working manifest for sampling
provenance. It may include local `path`, `range_hint`, and `notes`, but it is not the
input to `text_profile.py` and should not appear in final reports.

Text analysis principle:

Counts suggest where to look; close reading decides what it means.

Confirmed version 1 text-analysis stack:

- Use `scikit-learn` for count vectorization, n-grams, and TF-IDF-style statistics.
- Use `jieba` for Chinese tokenization.
- Use `pandas` for tabular CSV/JSON output.
- Do not hand-roll TF-IDF or Chinese segmentation when these dependencies are
  unavailable.
- Manage these dependencies with `uv sync` in `scripts/`.
- If required dependencies are missing and the user does not approve installing them,
  skip text profiling and record the missing dependency warning in `warnings.md`.

Method confirmation on 2026-06-27:

- scikit-learn documents bag-of-words vectorization as tokenization, token counting,
  and normalization/weighting.
- scikit-learn `CountVectorizer` implements tokenization and occurrence counting.
- scikit-learn `TfidfVectorizer` supports custom analyzers/tokenizers, `ngram_range`,
  `stop_words`, `token_pattern`, and TF-IDF weighting.
- scikit-learn documents `stop_words=None` as the default and warns that the built-in
  English stop list has known issues.
- jieba documents `jieba.cut`/`jieba.lcut`; default precise mode is appropriate for
  general Chinese segmentation.
- pandas documents `DataFrame.to_csv` for CSV output.

Version 1 text-statistics defaults:

- Unicode normalization: preserve original text except standard Python string
  handling; do not strip accents by default.
- Case normalization: lowercase non-CJK text through scikit-learn defaults.
- Stopwords: `None` by default. Do not use scikit-learn's built-in `english` stop
  list unless a future design explicitly opts in.
- English/non-CJK word tokenization: scikit-learn default word analyzer with token
  pattern equivalent to two-or-more alphanumeric characters.
- Chinese/CJK tokenization: use `jieba.lcut(text, cut_all=False, HMM=True)` and drop
  whitespace-only tokens.
- Term frequency: unigram counts per group and role, plus `per_1000_tokens`.
- N-grams: emit 1-gram, 2-gram, and 3-gram counts.
- TF-IDF: use scikit-learn `TfidfVectorizer` with the same tokenizer/analyzer policy,
  `use_idf=True`, `smooth_idf=True`, `sublinear_tf=False`, and default L2 norm.
- Co-occurrence: use token-window counts with default `window_size=5`; record the
  configured window in `cooccurrence.csv`.
- Dependency packaging: declare `scikit-learn`, `jieba`, and `pandas` in
  `scripts/pyproject.toml`; commit `scripts/uv.lock`; do not commit `scripts/.venv/`.
