import json
from pathlib import Path

from history_inventory import main as inventory_main
from text_profile import main as profile_main


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_default_persistent_inventory_summary_is_privacy_safe(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    out_dir = tmp_path / "report"
    secret_path = codex_home / "sessions" / "session.jsonl"
    write(
        secret_path,
        '{"timestamp":"2026-06-27T00:00:00Z","type":"event_msg","payload":{"text":"LEAK_SENTINEL_TRANSCRIPT"}}\n',
    )

    assert inventory_main(["--agent", "codex", "--codex-home", str(codex_home), "--output-dir", str(out_dir)]) == 0

    summary_text = (out_dir / "inventory_summary.json").read_text(encoding="utf-8")
    warnings_text = (out_dir / "warnings.json").read_text(encoding="utf-8")
    assert "LEAK_SENTINEL_TRANSCRIPT" not in summary_text
    assert "LEAK_SENTINEL_TRANSCRIPT" not in warnings_text
    assert str(secret_path) not in summary_text
    assert "content_sha256" not in summary_text


def test_text_profile_uses_only_redacted_selected_text(tmp_path: Path) -> None:
    selected = tmp_path / "selected_text.jsonl"
    out_dir = tmp_path / "profile"
    selected.write_text(
        json.dumps(
            {
                "id": "sample-redacted",
                "inventory_id": "i1",
                "source_type": "codex_session",
                "role": "user",
                "agent_tool": "codex",
                "actual_model_bucket": "unknown_actual_model",
                "displayed_model_signal": None,
                "behavior_dimension_hint": None,
                "group": {"agent": "codex", "project_bucket": "current", "time_bucket": "recent"},
                "redacted_text": "Please inspect [REDACTED_PATH] and [REDACTED_EMAIL].",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    assert profile_main(["--input", str(selected), "--output-dir", str(out_dir)]) == 0

    output_text = "\n".join(path.read_text(encoding="utf-8") for path in out_dir.iterdir() if path.is_file())
    assert "LEAK_SENTINEL_TRANSCRIPT" not in output_text
    assert "/home/private/repo" not in output_text
    assert "person@example.com" not in output_text
