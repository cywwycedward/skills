# Script Interfaces

Reference for script CLI interfaces, output schemas, and dependency management.
Read before running scripts.

## Dependency Setup

Before running scripts, ensure `uv` is available. If missing, ask the user before installing.

```bash
cd scripts
uv sync
```

Dependencies: `jieba>=0.42.1`, `pandas>=2.2.0`, `scikit-learn>=1.5.0`, dev: `pytest>=8.0.0`.
`.venv/` is created locally and git-ignored. Do not commit it.

## history_inventory.py

Purpose: create a low-cost corpus map without reading project source or emitting raw transcript text.

```bash
cd scripts
uv run python history_inventory.py --agent {codex,claude,both} --output-dir ../.output/YYYY-MM-DD-summary
```

### Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `--agent {codex,claude,both}` | Yes | Which agent tool(s) to inventory |
| `--output-dir PATH` | Yes | Output directory |
| `--root PATH` | No | Repeatable. User-specified roots |
| `--codex-home PATH` | No | Override Codex home discovery |
| `--claude-home PATH` | No | Override Claude home discovery |
| `--no-defaults` | No | Skip default home-directory discovery |

### Output Files

**inventory.jsonl** (working file, may include path and content_sha256):

| Key | Description |
|-----|-------------|
| `id` | Unique identifier |
| `agent` | `codex` or `claude` |
| `source_type` | One of the eight source types |
| `path` | Full local path (working file only) |
| `path_hash` | `sha256(str(path.resolve()).encode())[:16]` |
| `project_bucket` | De-identified project label |
| `size_bytes` | File size |
| `mtime` | Modification timestamp |
| `extension` | File extension |
| `line_count` | Total lines |
| `readable` | Whether file was successfully opened |
| `jsonl_total_lines` | For JSONL: total lines |
| `jsonl_valid_lines` | For JSONL: valid JSON lines |
| `top_level_key_counts` | For JSONL: top-level key frequencies |
| `text_line_count` | For Markdown: text lines |
| `content_sha256` | Content hash (working file only) |
| `warnings` | List of warning strings |

**inventory_summary.json** (persistent, omits path and content_sha256):

```json
{
  "total_files": 0,
  "by_agent": {},
  "by_source_type": {},
  "size_bytes": {"min": null, "max": null, "total": 0},
  "time_range": {"min_mtime": null, "max_mtime": null},
  "parse_rates": {},
  "sources": [],
  "warning_counts": {}
}
```

Each `sources` entry includes `id`, `path_hash`, `agent`, `source_type`, `project_bucket`, `size_bytes`, `mtime`, `extension`, `line_count`, `jsonl_total_lines`, `jsonl_valid_lines`, `text_line_count`, `warnings` — but NOT `path` or `content_sha256`.

**warnings.json:**

```json
{
  "source_coverage": [],
  "parse_warnings": [],
  "privacy_warnings": [],
  "dependency_warnings": [],
  "model_signal_limits": [],
  "skipped_steps": []
}
```

## text_profile.py

Purpose: quantitative text statistics that support, but do not replace, close reading.
Reads only agent-prepared `selected_text.jsonl` — never traverses history roots.

```bash
cd scripts
uv run python text_profile.py --input ../.output/YYYY-MM-DD-summary/selected_text.jsonl --output-dir ../.output/YYYY-MM-DD-summary/user-habits
```

### Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `--input PATH` | Yes | Input JSONL file (selected_text.jsonl) |
| `--output-dir PATH` | Yes | Output directory |
| `--include-assistant` | No | Include assistant role text |
| `--exclude-code-blocks` | No | Strip ``` fenced blocks |
| `--exclude-tool-output` | No | Strip `TOOL_OUTPUT:` lines |
| `--window-size INT` | No | Co-occurrence window (default: 5) |
| `--max-assistant-chars INT` | No | Truncate long assistant text |

### selected_text.jsonl Row Schema

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
  "group": {"agent": "claude", "project_bucket": "current", "time_bucket": "recent"},
  "redacted_text": "..."
}
```

Default roles: `user`, `memory`, `unknown`. Assistant included only with `--include-assistant`.
Missing `role` → `"unknown"`, missing `group` → `{}`.

### Output Files

**term_frequency.csv:** `group_id`, `role`, `token`, `token_type`, `count`, `per_1000_tokens`, `doc_count`

**ngram_frequency.csv:** `group_id`, `role`, `n`, `ngram`, `token_type`, `count`, `per_1000_tokens`, `doc_count`

**tfidf_terms.csv:** `group_id`, `role`, `token`, `token_type`, `tfidf`, `doc_count`

**cooccurrence.csv:** `group_id`, `role`, `term_a`, `term_b`, `window_size`, `count`

**text_profile_summary.json:**
```json
{
  "total_document_count": 0,
  "total_token_count": 0,
  "token_counts_by_group_and_role": {},
  "dependency_versions": {},
  "tokenization_method": {},
  "excluded_content_counts": {},
  "warning_summary": {}
}
```

**text_profile_warnings.json:**
```json
{
  "missing_role_count": 0,
  "missing_group_count": 0,
  "missing_redacted_text_count": 0,
  "excluded_assistant_count": 0,
  "tokenization_warnings": [],
  "skipped_rows": []
}
```

### Tokenization

- **CJK:** `jieba.lcut(text, cut_all=False, HMM=True)`, drop whitespace-only tokens
- **Non-CJK:** scikit-learn default word pattern (two-or-more alphanumeric, lowercased)
- **Stopwords:** `None` by default
- **N-grams:** 1-gram, 2-gram, 3-gram
- **TF-IDF:** `TfidfVectorizer` with `use_idf=True, smooth_idf=True, sublinear_tf=False`
- **Co-occurrence:** token-window with configurable `window_size` (default 5)

### Boundary

The script reads only `--input`. It does not discover or traverse history roots.
Counts suggest where to look; close reading decides what it means.
