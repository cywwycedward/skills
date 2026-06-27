"""Text Profile CLI.

Statistical profiling of selected agent history text.
Reads a single JSONL file and writes profile CSVs, a summary JSON,
and a warnings JSON.  Does NOT traverse history roots or agent config
directories.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import jieba
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# ---------------------------------------------------------------------------
# CJK Unicode ranges used for detection
# ---------------------------------------------------------------------------
_CJK_RANGES: list[tuple[int, int]] = [
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
]

# ---------------------------------------------------------------------------
# Non-CJK token pattern – scikit-learn-compatible default (2+ word chars)
# ---------------------------------------------------------------------------
_NON_CJK_RE: re.Pattern[str] = re.compile(r"(?u)\b\w\w+\b")

# ---------------------------------------------------------------------------
# Roles included by default (assistant only with --include-assistant)
# ---------------------------------------------------------------------------
_DEFAULT_ROLES: frozenset[str] = frozenset({"user", "memory", "unknown"})


# ===================================================================
# Helpers
# ===================================================================


def _has_cjk(text: str) -> bool:
    """Return True when *text* contains at least one CJK character."""
    for ch in text:
        cp = ord(ch)
        for lo, hi in _CJK_RANGES:
            if lo <= cp <= hi:
                return True
    return False


def _derive_group_id(group: dict[str, Any]) -> str:
    """Produce a stable group identifier from the group dict.

    Returns ``"none"`` for an empty group.
    """
    if not group:
        return "none"
    return json.dumps(group, sort_keys=True, ensure_ascii=False)


def _tokenize(text: str) -> tuple[str, list[str]]:
    """Tokenize *text*, returning ``(token_type, tokens)``.

    *token_type* is ``"cjk"`` or ``"non_cjk"``.
    Whitespace-only jieba tokens are dropped.
    """
    if _has_cjk(text):
        raw = jieba.lcut(text, cut_all=False, HMM=True)
        tokens = [t for t in raw if t.strip()]
        return "cjk", tokens
    tokens = [m.group(0).lower() for m in _NON_CJK_RE.finditer(text)]
    return "non_cjk", tokens


def _strip_code_blocks(text: str) -> tuple[str, int]:
    """Remove fenced code blocks (`` ``` ... ``` ``) from *text*.

    Returns ``(cleaned_text, stripped_block_count)``.
    """
    # Match ```-delimited blocks; the content between is removed.
    pattern = re.compile(r"```.*?```", re.DOTALL)
    count = len(pattern.findall(text))
    cleaned = pattern.sub("", text)
    return cleaned, count


def _strip_tool_output(text: str) -> tuple[str, int]:
    """Remove lines that start with ``TOOL_OUTPUT:``.

    Returns ``(cleaned_text, stripped_line_count)``.
    """
    lines = text.split("\n")
    kept: list[str] = []
    removed = 0
    for line in lines:
        if line.startswith("TOOL_OUTPUT:"):
            removed += 1
        else:
            kept.append(line)
    return "\n".join(kept), removed


# ===================================================================
# Core profiling logic
# ===================================================================


def _load_and_filter(
    input_path: Path,
    include_assistant: bool,
    max_assistant_chars: int | None,
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    """Read the JSONL file and return filtered rows + warning counters + skipped rows.

    Returns ``(rows, warnings, skipped_rows)`` where *warnings* is a flat dict of counters
    and *skipped_rows* is a list of dicts describing unparseable lines.
    """
    rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    warnings: dict[str, int] = {
        "missing_role_count": 0,
        "missing_group_count": 0,
        "missing_redacted_text_count": 0,
        "excluded_assistant_count": 0,
    }
    allowed_roles = set(_DEFAULT_ROLES)
    if include_assistant:
        allowed_roles.add("assistant")

    with input_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped_rows.append(
                    {
                        "reason": "json_decode_error",
                    }
                )
                continue

            role = rec.get("role")
            if role is None:
                role = "unknown"
                warnings["missing_role_count"] += 1
            rec["role"] = role

            group = rec.get("group")
            if group is None:
                group = {}
                warnings["missing_group_count"] += 1
            rec["group"] = group

            if "redacted_text" not in rec:
                warnings["missing_redacted_text_count"] += 1
                rec["redacted_text"] = ""

            if role not in allowed_roles:
                if role == "assistant":
                    warnings["excluded_assistant_count"] += 1
                continue

            # Truncate assistant text when requested
            if role == "assistant" and max_assistant_chars is not None:
                text = rec["redacted_text"]
                if isinstance(text, str) and len(text) > max_assistant_chars:
                    rec["redacted_text"] = text[:max_assistant_chars]

            rows.append(rec)

    return rows, warnings, skipped_rows


def _build_doc_records(
    rows: list[dict[str, Any]],
    exclude_code_blocks: bool,
    exclude_tool_output: bool,
) -> tuple[
    list[dict[str, Any]],
    dict[str, int],
    list[str],
]:
    """Process rows into document records ready for tokenization.

    Returns ``(docs, excluded_counts, tokenization_warnings)``.
    """
    docs: list[dict[str, Any]] = []
    excluded_counts: dict[str, int] = {
        "code_blocks": 0,
        "tool_output_lines": 0,
    }
    tokenization_warnings: list[str] = []

    for rec in rows:
        text = rec.get("redacted_text", "")
        if not isinstance(text, str):
            text = str(text)

        if exclude_code_blocks:
            text, code_count = _strip_code_blocks(text)
            excluded_counts["code_blocks"] += code_count

        if exclude_tool_output:
            text, tool_count = _strip_tool_output(text)
            excluded_counts["tool_output_lines"] += tool_count

        if not text.strip():
            tokenization_warnings.append(
                f"empty-or-whitespace-text: id={rec.get('id', '?')}"
            )
            continue

        token_type, tokens = _tokenize(text)
        if not tokens:
            tokenization_warnings.append(
                f"zero-tokens: id={rec.get('id', '?')} token_type={token_type}"
            )
            continue

        group_id = _derive_group_id(rec["group"])

        docs.append(
            {
                "group_id": group_id,
                "role": rec["role"],
                "token_type": token_type,
                "tokens": tokens,
            }
        )

    return docs, excluded_counts, tokenization_warnings


def _group_docs(
    docs: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, list[list[str]]]]:
    """Group document token lists by (group_id, role) and token_type.

    Returns ``{(group_id, role): {"cjk": [tokens, ...], "non_cjk": [tokens, ...]}}``.
    """
    grouped: dict[tuple[str, str], dict[str, list[list[str]]]] = defaultdict(
        lambda: {"cjk": [], "non_cjk": []}
    )
    for doc in docs:
        key = (doc["group_id"], doc["role"])
        grouped[key][doc["token_type"]].append(doc["tokens"])
    return dict(grouped)


def _compute_term_frequencies(
    grouped: dict[tuple[str, str], dict[str, list[list[str]]]],
) -> pd.DataFrame:
    """Compute unigram term frequencies and return a DataFrame."""
    records: list[dict[str, Any]] = []
    for (group_id, role), by_type in sorted(grouped.items()):
        # Total token count across all types for per_1000 denominator
        total_tokens = sum(
            sum(len(tokens) for tokens in token_lists)
            for token_lists in by_type.values()
        )

        for token_type, doc_token_lists in by_type.items():
            if not doc_token_lists:
                continue
            doc_strings = [" ".join(tokens) for tokens in doc_token_lists]
            vectorizer = CountVectorizer(
                analyzer=lambda d: d.split(),
                lowercase=False,
            )
            dtm = vectorizer.fit_transform(doc_strings)
            feature_names = vectorizer.get_feature_names_out()
            counts = dtm.sum(axis=0).A1  # total count per token
            doc_counts = (dtm > 0).sum(axis=0).A1  # doc frequency

            for i, token in enumerate(feature_names):
                count = int(counts[i])
                records.append(
                    {
                        "group_id": group_id,
                        "role": role,
                        "token": token,
                        "token_type": token_type,
                        "count": count,
                        "per_1000_tokens": round(
                            count * 1000 / total_tokens, 4
                        )
                        if total_tokens > 0
                        else 0.0,
                        "doc_count": int(doc_counts[i]),
                    }
                )

    return pd.DataFrame(records)


def _compute_ngram_frequencies(
    grouped: dict[tuple[str, str], dict[str, list[list[str]]]],
) -> pd.DataFrame:
    """Compute 1-gram through 3-gram frequencies and return a DataFrame."""
    records: list[dict[str, Any]] = []
    for (group_id, role), by_type in sorted(grouped.items()):
        total_tokens = sum(
            sum(len(tokens) for tokens in token_lists)
            for token_lists in by_type.values()
        )

        for token_type, doc_token_lists in by_type.items():
            if not doc_token_lists:
                continue
            doc_ngrams = [_make_ngrams(tokens, max_n=3) for tokens in doc_token_lists]
            vectorizer = CountVectorizer(
                analyzer=lambda d: d,
                lowercase=False,
            )
            dtm = vectorizer.fit_transform(doc_ngrams)
            feature_names = vectorizer.get_feature_names_out()
            counts = dtm.sum(axis=0).A1
            doc_counts = (dtm > 0).sum(axis=0).A1

            for i, ngram_str in enumerate(feature_names):
                n = len(ngram_str.split())
                records.append(
                    {
                        "group_id": group_id,
                        "role": role,
                        "n": n,
                        "ngram": ngram_str,
                        "token_type": token_type,
                        "count": int(counts[i]),
                        "per_1000_tokens": round(
                            counts[i] * 1000 / total_tokens, 4
                        )
                        if total_tokens > 0
                        else 0.0,
                        "doc_count": int(doc_counts[i]),
                    }
                )

    return pd.DataFrame(records)


def _make_ngrams(tokens: list[str], max_n: int) -> list[str]:
    """Return contiguous token n-grams up to *max_n* as space-joined strings."""
    ngrams: list[str] = []
    for n in range(1, max_n + 1):
        if len(tokens) < n:
            continue
        for i in range(len(tokens) - n + 1):
            ngrams.append(" ".join(tokens[i : i + n]))
    return ngrams


def _compute_tfidf(
    grouped: dict[tuple[str, str], dict[str, list[list[str]]]],
) -> pd.DataFrame:
    """Compute unigram TF-IDF scores and return a DataFrame."""
    records: list[dict[str, Any]] = []
    for (group_id, role), by_type in sorted(grouped.items()):
        for token_type, doc_token_lists in by_type.items():
            if not doc_token_lists:
                continue
            doc_strings = [" ".join(tokens) for tokens in doc_token_lists]
            vectorizer = TfidfVectorizer(
                analyzer=lambda d: d.split(),
                lowercase=False,
                use_idf=True,
                smooth_idf=True,
                sublinear_tf=False,
            )
            dtm = vectorizer.fit_transform(doc_strings)
            feature_names = vectorizer.get_feature_names_out()
            # Compute per-token TF-IDF: average across documents containing it
            doc_counts = (dtm > 0).sum(axis=0).A1
            tfidf_sums = dtm.sum(axis=0).A1

            for i, token in enumerate(feature_names):
                dc = int(doc_counts[i])
                records.append(
                    {
                        "group_id": group_id,
                        "role": role,
                        "token": token,
                        "token_type": token_type,
                        "tfidf": round(float(tfidf_sums[i]), 6),
                        "doc_count": dc,
                    }
                )

    return pd.DataFrame(records)


def _compute_cooccurrence(
    grouped: dict[tuple[str, str], dict[str, list[list[str]]]],
    window_size: int,
) -> pd.DataFrame:
    """Compute token co-occurrence within a sliding window."""
    records: list[dict[str, Any]] = []
    for (group_id, role), by_type in sorted(grouped.items()):
        for token_type, doc_token_lists in by_type.items():
            pair_counter: Counter[tuple[str, str]] = Counter()
            for tokens in doc_token_lists:
                n = len(tokens)
                for i in range(n):
                    window = tokens[i : i + window_size]
                    for j in range(len(window)):
                        for k in range(j + 1, len(window)):
                            a, b = window[j], window[k]
                            key = (a, b) if a < b else (b, a)
                            pair_counter[key] += 1

            for (term_a, term_b), count in sorted(pair_counter.items()):
                records.append(
                    {
                        "group_id": group_id,
                        "role": role,
                        "term_a": term_a,
                        "term_b": term_b,
                        "window_size": window_size,
                        "count": count,
                    }
                )

    return pd.DataFrame(records)


# ===================================================================
# Output writers
# ===================================================================


def _write_summary(
    output_dir: Path,
    doc_count: int,
    total_tokens: int,
    token_counts_by_group_and_role: dict[str, dict[str, int]],
    excluded_counts: dict[str, int],
    warning_summary: dict[str, Any],
) -> None:
    summary: dict[str, Any] = {
        "total_document_count": doc_count,
        "total_token_count": total_tokens,
        "token_counts_by_group_and_role": token_counts_by_group_and_role,
        "dependency_versions": {
            "scikit-learn": _sklearn_version(),
            "jieba": jieba.__version__,
            "pandas": pd.__version__,
        },
        "tokenization_method": {
            "cjk": "jieba.lcut(cut_all=False, HMM=True)",
            "non_cjk": "scikit-learn-compatible default word token pattern",
        },
        "excluded_content_counts": excluded_counts,
        "warning_summary": warning_summary,
    }
    path = output_dir / "text_profile_summary.json"
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _sklearn_version() -> str:
    import sklearn

    return sklearn.__version__


def _write_warnings(
    output_dir: Path,
    warnings: dict[str, int],
    tokenization_warnings: list[str],
    skipped_rows: list[dict[str, Any]],
) -> None:
    payload: dict[str, Any] = {
        "missing_role_count": warnings.get("missing_role_count", 0),
        "missing_group_count": warnings.get("missing_group_count", 0),
        "missing_redacted_text_count": warnings.get(
            "missing_redacted_text_count", 0
        ),
        "excluded_assistant_count": warnings.get("excluded_assistant_count", 0),
        "tokenization_warnings": tokenization_warnings,
        "skipped_rows": skipped_rows,
    }
    path = output_dir / "text_profile_warnings.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ===================================================================
# CLI
# ===================================================================


def main(argv: list[str] | None = None) -> int:
    """Run the text profiling CLI and return a process-style exit code."""
    parser = argparse.ArgumentParser(
        description="Statistical text profiling for selected agent history.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the JSONL file (only this file is read).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for output files.",
    )
    parser.add_argument(
        "--include-assistant",
        action="store_true",
        default=False,
        help="Include assistant-role text (excluded by default).",
    )
    parser.add_argument(
        "--exclude-code-blocks",
        action="store_true",
        default=False,
        help="Strip fenced code blocks before tokenization.",
    )
    parser.add_argument(
        "--exclude-tool-output",
        action="store_true",
        default=False,
        help="Strip lines starting with TOOL_OUTPUT: before tokenization.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=5,
        help="Token window size for co-occurrence (default: 5).",
    )
    parser.add_argument(
        "--max-assistant-chars",
        type=int,
        default=None,
        help="Truncate assistant text to this many characters.",
    )

    args = parser.parse_args(argv)

    input_path: Path = args.input
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load & filter
    # ------------------------------------------------------------------
    rows, warnings, skipped_rows = _load_and_filter(
        input_path,
        include_assistant=args.include_assistant,
        max_assistant_chars=args.max_assistant_chars,
    )

    # ------------------------------------------------------------------
    # Build document records (with optional content stripping)
    # ------------------------------------------------------------------
    docs, excluded_counts, tokenization_warnings = _build_doc_records(
        rows,
        exclude_code_blocks=args.exclude_code_blocks,
        exclude_tool_output=args.exclude_tool_output,
    )

    # ------------------------------------------------------------------
    # Group by (group_id, role)
    # ------------------------------------------------------------------
    grouped = _group_docs(docs)

    # ------------------------------------------------------------------
    # Compute token counts by group and role
    # ------------------------------------------------------------------
    token_counts_by_group_and_role: dict[str, dict[str, int]] = {}
    total_tokens = 0
    for (group_id, role), by_type in grouped.items():
        tsum = sum(
            sum(len(tokens) for tokens in token_lists)
            for token_lists in by_type.values()
        )
        total_tokens += tsum
        token_counts_by_group_and_role.setdefault(group_id, {})[role] = tsum

    # ------------------------------------------------------------------
    # Write CSVs
    # ------------------------------------------------------------------
    term_freq_df = _compute_term_frequencies(grouped)
    if not term_freq_df.empty:
        term_freq_df.to_csv(
            output_dir / "term_frequency.csv", index=False, encoding="utf-8"
        )
    else:
        _write_empty_csv(
            output_dir / "term_frequency.csv",
            ["group_id", "role", "token", "token_type",
             "count", "per_1000_tokens", "doc_count"],
        )

    ngram_freq_df = _compute_ngram_frequencies(grouped)
    if not ngram_freq_df.empty:
        ngram_freq_df.to_csv(
            output_dir / "ngram_frequency.csv", index=False, encoding="utf-8"
        )
    else:
        _write_empty_csv(
            output_dir / "ngram_frequency.csv",
            ["group_id", "role", "n", "ngram", "token_type",
             "count", "per_1000_tokens", "doc_count"],
        )

    tfidf_df = _compute_tfidf(grouped)
    if not tfidf_df.empty:
        tfidf_df.to_csv(
            output_dir / "tfidf_terms.csv", index=False, encoding="utf-8"
        )
    else:
        _write_empty_csv(
            output_dir / "tfidf_terms.csv",
            ["group_id", "role", "token", "token_type",
             "tfidf", "doc_count"],
        )

    cooc_df = _compute_cooccurrence(grouped, window_size=args.window_size)
    if not cooc_df.empty:
        cooc_df.to_csv(
            output_dir / "cooccurrence.csv", index=False, encoding="utf-8"
        )
    else:
        _write_empty_csv(
            output_dir / "cooccurrence.csv",
            ["group_id", "role", "term_a", "term_b",
             "window_size", "count"],
        )

    # ------------------------------------------------------------------
    # Write summary & warnings
    # ------------------------------------------------------------------
    warning_summary = {
        "missing_role_count": warnings["missing_role_count"],
        "missing_group_count": warnings["missing_group_count"],
        "missing_redacted_text_count": warnings["missing_redacted_text_count"],
        "excluded_assistant_count": warnings["excluded_assistant_count"],
        "tokenization_warnings": tokenization_warnings,
        "skipped_rows_count": len(skipped_rows),
    }
    _write_summary(
        output_dir,
        doc_count=len(rows),
        total_tokens=total_tokens,
        token_counts_by_group_and_role=token_counts_by_group_and_role,
        excluded_counts=excluded_counts,
        warning_summary=warning_summary,
    )
    _write_warnings(output_dir, warnings, tokenization_warnings, skipped_rows)

    return 0


def _write_empty_csv(path: Path, columns: list[str]) -> None:
    """Write a CSV file containing only the header row."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        import csv
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()


if __name__ == "__main__":
    sys.exit(main())
