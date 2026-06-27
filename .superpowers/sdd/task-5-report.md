Status: DONE

Commits:
- 1245757

Test summary: All 4 tests pass (test_text_profile_outputs_required_files_and_columns, test_text_profile_excludes_assistant_by_default_and_includes_when_requested, test_text_profile_warns_for_missing_role_and_group, test_text_profile_can_exclude_code_blocks_and_tool_output).

Concerns: None. Step 3 verification confirms text_profile.py has zero matches for history-root traversal patterns (`.codex`, `.claude`, `glob(`, `rglob(`, etc. — exit code 1). The script reads only the `--input` JSONL file.

---

## Fix Report

### Issue 1: Untracked skipped rows
Fixed by: Adding a `skipped_rows: list[dict[str, Any]]` list to `_load_and_filter`. On `json.JSONDecodeError`, the handler now appends `{"id": None, "reason": "json_decode_error", "line_preview": line[:100]}` instead of silently continuing. The function now returns `(rows, warnings, skipped_rows)` as a 3-tuple. `_write_warnings` accepts the new `skipped_rows` parameter and writes the actual list to `text_profile_warnings.json` instead of the hardcoded `[]`.

### Issue 2: Inconsistent naming
Fixed by: Changing the `warning_summary` dict in `main()` from `"skipped_rows_count": 0` to `"skipped_rows_count": len(skipped_rows)` so the summary always reflects the actual count. The warnings file continues to use `"skipped_rows": <list>` for the detail rows. Summary = count (integer), warnings = detail (list).

Test command: `uv run pytest tests/test_text_profile.py -v`
Test output: 4 passed, 5 warnings in 1.22s

Commit: `git add text_profile.py` and `git commit -m "fix(agent-history-analyzer): track skipped rows and fix warning key naming"`
