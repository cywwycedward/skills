import csv
import json
from pathlib import Path

from text_profile import main


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    return path


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_text_profile_outputs_required_files_and_columns(tmp_path: Path) -> None:
    selected = write_jsonl(
        tmp_path / "selected_text.jsonl",
        [
            {
                "id": "sample-001",
                "inventory_id": "claude-0001",
                "source_type": "claude_session",
                "role": "user",
                "agent_tool": "claude",
                "actual_model_bucket": "unknown_actual_model",
                "displayed_model_signal": None,
                "behavior_dimension_hint": None,
                "group": {"agent": "claude", "project_bucket": "current", "time_bucket": "recent"},
                "redacted_text": "Please verify output and run tests before final answer.",
            },
            {
                "id": "sample-002",
                "inventory_id": "codex-0001",
                "source_type": "codex_history",
                "role": "memory",
                "agent_tool": "codex",
                "actual_model_bucket": "unknown_actual_model",
                "displayed_model_signal": None,
                "behavior_dimension_hint": None,
                "group": {"agent": "codex", "project_bucket": "all", "time_bucket": "older"},
                "redacted_text": "用户偏好 先计划 再实现 并验证",
            },
        ],
    )
    out_dir = tmp_path / "profile"

    assert main(["--input", str(selected), "--output-dir", str(out_dir)]) == 0

    assert (out_dir / "text_profile_summary.json").exists()
    assert (out_dir / "term_frequency.csv").exists()
    assert (out_dir / "ngram_frequency.csv").exists()
    assert (out_dir / "tfidf_terms.csv").exists()
    assert (out_dir / "cooccurrence.csv").exists()
    assert (out_dir / "text_profile_warnings.json").exists()

    assert set(read_csv(out_dir / "term_frequency.csv")[0]) == {
        "group_id",
        "role",
        "token",
        "token_type",
        "count",
        "per_1000_tokens",
        "doc_count",
    }
    assert set(read_csv(out_dir / "ngram_frequency.csv")[0]) == {
        "group_id",
        "role",
        "n",
        "ngram",
        "token_type",
        "count",
        "per_1000_tokens",
        "doc_count",
    }
    assert set(read_csv(out_dir / "tfidf_terms.csv")[0]) == {
        "group_id",
        "role",
        "token",
        "token_type",
        "tfidf",
        "doc_count",
    }
    assert set(read_csv(out_dir / "cooccurrence.csv")[0]) == {
        "group_id",
        "role",
        "term_a",
        "term_b",
        "window_size",
        "count",
    }

    summary = json.loads((out_dir / "text_profile_summary.json").read_text(encoding="utf-8"))
    assert summary["total_document_count"] == 2
    assert summary["tokenization_method"]["cjk"] == "jieba.lcut(cut_all=False, HMM=True)"
    assert summary["tokenization_method"]["non_cjk"] == "scikit-learn-compatible default word token pattern"
    assert "scikit-learn" in summary["dependency_versions"]
    assert "jieba" in summary["dependency_versions"]
    assert "pandas" in summary["dependency_versions"]


def test_text_profile_excludes_assistant_by_default_and_includes_when_requested(tmp_path: Path) -> None:
    selected = write_jsonl(
        tmp_path / "selected_text.jsonl",
        [
            {
                "id": "sample-user",
                "inventory_id": "i1",
                "source_type": "claude_session",
                "role": "user",
                "agent_tool": "claude",
                "actual_model_bucket": "unknown_actual_model",
                "displayed_model_signal": None,
                "behavior_dimension_hint": None,
                "group": {"agent": "claude", "project_bucket": "current", "time_bucket": "recent"},
                "redacted_text": "useronlytoken",
            },
            {
                "id": "sample-assistant",
                "inventory_id": "i2",
                "source_type": "claude_session",
                "role": "assistant",
                "agent_tool": "claude",
                "actual_model_bucket": "claude-sonnet",
                "displayed_model_signal": None,
                "behavior_dimension_hint": "verification",
                "group": {"agent": "claude", "project_bucket": "current", "time_bucket": "recent"},
                "redacted_text": "assistantonlytoken",
            },
        ],
    )

    default_out = tmp_path / "default"
    assert main(["--input", str(selected), "--output-dir", str(default_out)]) == 0
    default_terms = {row["token"] for row in read_csv(default_out / "term_frequency.csv")}
    assert "useronlytoken" in default_terms
    assert "assistantonlytoken" not in default_terms

    assistant_out = tmp_path / "assistant"
    assert main(["--input", str(selected), "--output-dir", str(assistant_out), "--include-assistant"]) == 0
    assistant_terms = {row["token"] for row in read_csv(assistant_out / "term_frequency.csv")}
    assert "useronlytoken" in assistant_terms
    assert "assistantonlytoken" in assistant_terms


def test_text_profile_warns_for_missing_role_and_group(tmp_path: Path) -> None:
    selected = write_jsonl(
        tmp_path / "selected_text.jsonl",
        [
            {
                "id": "sample-unknown",
                "inventory_id": "i1",
                "source_type": "user_specified_transcript",
                "redacted_text": "unknown role text",
            }
        ],
    )
    out_dir = tmp_path / "out"

    assert main(["--input", str(selected), "--output-dir", str(out_dir)]) == 0

    warnings = json.loads((out_dir / "text_profile_warnings.json").read_text(encoding="utf-8"))
    assert warnings["missing_role_count"] == 1
    assert warnings["missing_group_count"] == 1
    rows = read_csv(out_dir / "term_frequency.csv")
    assert {row["role"] for row in rows} == {"unknown"}


def test_text_profile_can_exclude_code_blocks_and_tool_output(tmp_path: Path) -> None:
    selected = write_jsonl(
        tmp_path / "selected_text.jsonl",
        [
            {
                "id": "sample-code",
                "inventory_id": "i1",
                "source_type": "codex_session",
                "role": "user",
                "agent_tool": "codex",
                "actual_model_bucket": "unknown_actual_model",
                "displayed_model_signal": None,
                "behavior_dimension_hint": None,
                "group": {"agent": "codex", "project_bucket": "current", "time_bucket": "recent"},
                "redacted_text": "keepword\n```python\nsecretcodeblock\n```\nTOOL_OUTPUT: secrettooloutput",
            }
        ],
    )
    out_dir = tmp_path / "out"

    assert main(["--input", str(selected), "--output-dir", str(out_dir), "--exclude-code-blocks", "--exclude-tool-output"]) == 0

    terms = {row["token"] for row in read_csv(out_dir / "term_frequency.csv")}
    assert "keepword" in terms
    assert "secretcodeblock" not in terms
    assert "secrettooloutput" not in terms
    summary = json.loads((out_dir / "text_profile_summary.json").read_text(encoding="utf-8"))
    assert summary["excluded_content_counts"]["code_blocks"] == 1
    assert summary["excluded_content_counts"]["tool_output_lines"] == 1
