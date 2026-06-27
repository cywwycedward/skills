import json
from pathlib import Path

import pytest

from history_inventory import main


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_inventory_discovers_supported_codex_and_claude_sources(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    claude_home = tmp_path / "claude"
    out_dir = tmp_path / "out"

    write(
        codex_home / "sessions" / "2026" / "session.jsonl",
        '{"timestamp":"2026-06-27T00:00:00Z","type":"turn_context","payload":{"model":"gpt-5.5"}}\n'
        '{"timestamp":"2026-06-27T00:00:01Z","type":"event_msg","payload":{"text":"RAW_CODEX_SECRET_123"}}\n',
    )
    write(codex_home / "history.jsonl", '{"session_id":"s1","text":"RAW_HISTORY_SECRET","ts":1}\n')
    write(codex_home / "memories" / "memory.md", "RAW_MEMORY_SECRET\n")
    write(codex_home / "config.toml", "api_key='RAW_CONFIG_SECRET'\n")
    write(
        claude_home / "projects" / "proj-a" / "session.jsonl",
        '{"type":"assistant","message":{"model":"claude-sonnet","content":"RAW_CLAUDE_SECRET"}}\n',
    )
    write(claude_home / "projects" / "proj-a" / "memory" / "MEMORY.md", "RAW_CLAUDE_MEMORY\n")
    write(claude_home / "settings.json", '{"token":"RAW_SETTINGS_SECRET"}\n')

    exit_code = main(
        [
            "--agent",
            "both",
            "--codex-home",
            str(codex_home),
            "--claude-home",
            str(claude_home),
            "--output-dir",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    inventory = read_jsonl(out_dir / "inventory.jsonl")
    source_types = {row["source_type"] for row in inventory}
    assert source_types == {
        "codex_session",
        "codex_history",
        "codex_memory",
        "claude_session",
        "claude_project_memory",
    }
    for row in inventory:
        assert set(row) >= {
            "id",
            "agent",
            "source_type",
            "path",
            "path_hash",
            "project_bucket",
            "size_bytes",
            "mtime",
            "extension",
            "line_count",
            "readable",
            "jsonl_total_lines",
            "jsonl_valid_lines",
            "top_level_key_counts",
            "text_line_count",
            "content_sha256",
            "warnings",
        }
    all_output = (out_dir / "inventory.jsonl").read_text(encoding="utf-8")
    all_output += (out_dir / "inventory_summary.json").read_text(encoding="utf-8")
    all_output += (out_dir / "warnings.json").read_text(encoding="utf-8")
    assert "RAW_CODEX_SECRET_123" not in all_output
    assert "RAW_HISTORY_SECRET" not in all_output
    assert "RAW_MEMORY_SECRET" not in all_output
    assert "RAW_CLAUDE_SECRET" not in all_output
    assert "RAW_CONFIG_SECRET" not in all_output
    assert "RAW_SETTINGS_SECRET" not in all_output


def test_inventory_records_json_parse_warnings_without_failing(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    out_dir = tmp_path / "out"
    write(
        codex_home / "sessions" / "broken.jsonl",
        '{"timestamp":"2026-06-27T00:00:00Z","type":"event_msg","payload":{}}\n'
        '{"timestamp":\n',
    )

    exit_code = main(
        [
            "--agent",
            "codex",
            "--codex-home",
            str(codex_home),
            "--output-dir",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    [row] = read_jsonl(out_dir / "inventory.jsonl")
    assert row["jsonl_total_lines"] == 2
    assert row["jsonl_valid_lines"] == 1
    assert row["top_level_key_counts"] == {"payload": 1, "timestamp": 1, "type": 1}
    assert any("json_parse_error" in warning for warning in row["warnings"])
    warnings = json.loads((out_dir / "warnings.json").read_text(encoding="utf-8"))
    assert warnings["parse_warnings"]


def test_inventory_summary_omits_paths_and_content_hashes(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    out_dir = tmp_path / "out"
    write(codex_home / "history.jsonl", '{"session_id":"s1","text":"RAW_PROMPT","ts":1}\n')

    assert main(["--agent", "codex", "--codex-home", str(codex_home), "--output-dir", str(out_dir)]) == 0

    summary = json.loads((out_dir / "inventory_summary.json").read_text(encoding="utf-8"))
    serialized = json.dumps(summary, sort_keys=True)
    assert "path_hash" in serialized
    assert str(codex_home) not in serialized
    assert "content_sha256" not in serialized
    assert "RAW_PROMPT" not in serialized


def test_inventory_rejects_broad_root_without_known_candidates(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    out_dir = tmp_path / "out"
    write(root / "src" / "main.py", "print('RAW_SOURCE_SECRET')\n")
    write(root / "AGENTS.md", "RAW_RULE_SECRET\n")
    write(root / "notes.md", "RAW_DOC_SECRET\n")

    assert main(["--agent", "both", "--root", str(root), "--no-defaults", "--output-dir", str(out_dir)]) == 0

    inventory = read_jsonl(out_dir / "inventory.jsonl")
    assert inventory == []
    summary = json.loads((out_dir / "inventory_summary.json").read_text(encoding="utf-8"))
    assert summary["total_files"] == 0
