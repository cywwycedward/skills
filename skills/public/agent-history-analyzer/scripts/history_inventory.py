"""Agent History Inventory CLI.

Discovers and inventories agent conversation history and memory files.
Emits inventory.jsonl, inventory_summary.json, and warnings.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INVENTORY_KEYS = [
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
]

SUMMARY_SOURCE_KEYS = [
    "id",
    "path_hash",
    "agent",
    "source_type",
    "project_bucket",
    "size_bytes",
    "mtime",
    "extension",
    "line_count",
    "jsonl_total_lines",
    "jsonl_valid_lines",
    "text_line_count",
    "warnings",
]

EXCLUDED_BASENAMES = frozenset(
    {
        "AGENTS.md",
        "AGENTS.override.md",
        "CLAUDE.md",
    }
)

SOURCE_CODE_EXTENSIONS = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".c",
        ".cpp",
        ".cc",
        ".h",
        ".hpp",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".scala",
        ".cs",
        ".vb",
        ".pl",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ps1",
        ".bat",
        ".cmd",
    }
)

NON_TARGET_BASENAMES = frozenset(
    {
        "settings.json",
        "mcp.json",
        ".mcp.json",
        "config.json",
        "config.toml",
        "config.yaml",
        "config.yml",
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials.json",
        "credentials.yaml",
        "credentials.yml",
        "token.json",
        "secrets.json",
        "package.json",
        "cargo.toml",
        "makefile",
        "dockerfile",
        "readme.md",
        "changelog.md",
        "license",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _expand_path(raw: str) -> Path:
    """Expand ``~`` and environment variables, return resolved absolute path."""
    return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()


def _path_hash(path: Path) -> str:
    """SHA-256 of the resolved absolute path string, truncated to 16 hex chars."""
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]


def _content_hash(path: Path) -> str | None:
    """Full SHA-256 hex digest of the file content, or *None* on read failure."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _is_excluded(path: Path) -> bool:
    """Return *True* for known non-target files that must never be inventoried."""
    name = path.name

    # --- basename block-list ------------------------------------------------
    if name in EXCLUDED_BASENAMES:
        return True
    if name.lower() in NON_TARGET_BASENAMES:
        return True

    # --- source-code extensions ---------------------------------------------
    if path.suffix in SOURCE_CODE_EXTENSIONS:
        return True

    # --- path-segment heuristics --------------------------------------------
    parts = path.parts
    for part in parts:
        if part == ".git":
            return True

    for i, part in enumerate(parts):
        if part == ".claude" and i + 1 < len(parts) and parts[i + 1] == "rules":
            return True

    # --- .codex/config.toml specifically -----------------------------------
    for i, part in enumerate(parts):
        if part == ".codex" and name == "config.toml":
            return True

    return False


def _is_memory_candidate(path: Path) -> bool:
    """Markdown file under a ``memory`` path segment *or* whose name starts with
    ``memory`` (case-insensitive)."""
    if path.suffix != ".md":
        return False
    name_lower = path.name.lower()
    if name_lower.startswith("memory"):
        return True
    for part in path.parts:
        if part.lower() == "memory":
            return True
    return False


# ---------------------------------------------------------------------------
# File processors
# ---------------------------------------------------------------------------


def _process_jsonl(path: Path) -> dict[str, Any]:
    """Process a JSONL file: count lines, valid JSON lines, top-level keys.

    Returns a dict with keys *total_lines*, *valid_lines*, *key_counter*,
    and *warnings*.  Does **not** interpret transcript semantics.
    """
    warnings: list[str] = []
    try:
        raw_text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "total_lines": 0,
            "valid_lines": 0,
            "key_counter": {},
            "warnings": [f"read_error: {exc}"],
        }

    lines = raw_text.splitlines()
    total_lines = len(lines)
    valid_lines = 0
    key_counter: Counter[str] = Counter()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
            valid_lines += 1
            if isinstance(obj, dict):
                for key in obj:
                    key_counter[key] += 1
        except json.JSONDecodeError as exc:
            warnings.append(f"json_parse_error: {exc}")

    return {
        "total_lines": total_lines,
        "valid_lines": valid_lines,
        "key_counter": dict(key_counter),
        "warnings": warnings,
    }


def _process_markdown(path: Path) -> dict[str, Any]:
    """Process a Markdown memory file: count text lines.

    Returns a dict with *line_count*, *text_line_count*, and *warnings*.
    Does **not** interpret meaning.
    """
    warnings: list[str] = []
    try:
        raw_text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "line_count": 0,
            "text_line_count": 0,
            "warnings": [f"read_error: {exc}"],
        }

    lines = raw_text.splitlines()
    line_count = len(lines)
    text_line_count = sum(1 for line in lines if line.strip())

    return {
        "line_count": line_count,
        "text_line_count": text_line_count,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _discover_codex_candidates(codex_home: Path) -> list[tuple[Path, str]]:
    """Return ``(path, source_type)`` for every Codex candidate under *codex_home*."""
    candidates: list[tuple[Path, str]] = []
    if not codex_home.is_dir():
        return candidates

    # sessions/**/*.jsonl
    sessions_dir = codex_home / "sessions"
    if sessions_dir.is_dir():
        for f in sessions_dir.rglob("*.jsonl"):
            if not _is_excluded(f):
                candidates.append((f, "codex_session"))

    # archived_sessions/**/*.jsonl
    archived_dir = codex_home / "archived_sessions"
    if archived_dir.is_dir():
        for f in archived_dir.rglob("*.jsonl"):
            if not _is_excluded(f):
                candidates.append((f, "codex_archived_session"))

    # history.jsonl
    history_file = codex_home / "history.jsonl"
    if history_file.is_file() and not _is_excluded(history_file):
        candidates.append((history_file, "codex_history"))

    # memories/**/*.md
    memories_dir = codex_home / "memories"
    if memories_dir.is_dir():
        for f in memories_dir.rglob("*.md"):
            if not _is_excluded(f):
                candidates.append((f, "codex_memory"))

    return candidates


def _discover_claude_candidates(claude_home: Path) -> list[tuple[Path, str]]:
    """Return ``(path, source_type)`` for every Claude candidate under *claude_home*."""
    candidates: list[tuple[Path, str]] = []
    if not claude_home.is_dir():
        return candidates

    projects_dir = claude_home / "projects"
    if not projects_dir.is_dir():
        return candidates

    # projects/**/*.jsonl
    for f in projects_dir.rglob("*.jsonl"):
        if not _is_excluded(f):
            candidates.append((f, "claude_session"))

    # projects/**/memory/*.md
    for f in projects_dir.rglob("*.md"):
        if _is_excluded(f):
            continue
        for part in f.parts:
            if part.lower() == "memory":
                candidates.append((f, "claude_project_memory"))
                break

    return candidates


def _discover_user_root_candidates(root: Path) -> list[tuple[Path, str]]:
    """Return ``(path, source_type)`` for candidate files under a user-provided root.

    - ``.jsonl`` files become *user_specified_transcript*.
    - ``.md`` files that match :func:`_is_memory_candidate` become
      *user_specified_memory*.
    - Everything else is silently skipped.
    """
    candidates: list[tuple[Path, str]] = []
    if not root.is_dir():
        return candidates

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if _is_excluded(f):
            continue

        if f.suffix == ".jsonl":
            candidates.append((f, "user_specified_transcript"))
        elif f.suffix == ".md" and _is_memory_candidate(f):
            candidates.append((f, "user_specified_memory"))

    return candidates


# ---------------------------------------------------------------------------
# Project bucket derivation
# ---------------------------------------------------------------------------


def _derive_project_bucket(path: Path, home: Path | None, source_type: str) -> str:
    """Return a short project-bucket label derived from the file path."""
    if home is not None:
        try:
            rel = path.resolve().relative_to(home.resolve())
        except ValueError:
            rel = path
    else:
        rel = path

    parts = rel.parts

    if source_type == "codex_session":
        if len(parts) >= 2 and parts[0] == "sessions":
            return parts[1]
        return str(rel.parent) if len(parts) > 1 else "__root__"

    if source_type == "codex_archived_session":
        if len(parts) >= 2 and parts[0] == "archived_sessions":
            return parts[1]
        return str(rel.parent) if len(parts) > 1 else "__root__"

    if source_type == "codex_history":
        return "__root__"

    if source_type == "codex_memory":
        if len(parts) >= 2 and parts[0] == "memories":
            if len(parts) >= 3:
                return parts[1]
            return "__memories__"
        return str(rel.parent) if len(parts) > 1 else "__memories__"

    if source_type in ("claude_session", "claude_project_memory"):
        if len(parts) >= 2 and parts[0] == "projects":
            return parts[1]
        return str(rel.parent) if len(parts) > 1 else "__root__"

    # user-specified roots
    return "__user_root__"


# ---------------------------------------------------------------------------
# Agent derivation
# ---------------------------------------------------------------------------


def _derive_agent(source_type: str) -> str:
    """Derive the agent label from the source type."""
    if source_type.startswith("codex_"):
        return "codex"
    if source_type.startswith("claude_"):
        return "claude"
    return "user"


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------


def _build_inventory_row(
    path: Path,
    source_type: str,
    home: Path | None,
) -> dict[str, Any]:
    """Build a single inventory row for *path*."""

    # --- stat ---------------------------------------------------------------
    try:
        stat = path.stat()
        size_bytes: int | None = stat.st_size
        mtime: float | None = stat.st_mtime
    except OSError:
        size_bytes = None
        mtime = None

    is_jsonl = path.suffix == ".jsonl"
    is_md = path.suffix == ".md"

    # --- content processing -------------------------------------------------
    row_warnings: list[str] = []
    line_count: int | None = None
    readable = False
    jsonl_total_lines: int | None = None
    jsonl_valid_lines: int | None = None
    top_level_key_counts: dict[str, int] = {}
    text_line_count: int | None = None

    if is_jsonl:
        metrics = _process_jsonl(path)
        line_count = metrics["total_lines"]
        readable = True
        jsonl_total_lines = metrics["total_lines"]
        jsonl_valid_lines = metrics["valid_lines"]
        top_level_key_counts = metrics["key_counter"]
        text_line_count = 0
        row_warnings.extend(metrics["warnings"])
    elif is_md:
        metrics = _process_markdown(path)
        line_count = metrics["line_count"]
        readable = True
        jsonl_total_lines = 0
        jsonl_valid_lines = 0
        text_line_count = metrics["text_line_count"]
        row_warnings.extend(metrics["warnings"])
    else:
        try:
            raw = path.read_text(encoding="utf-8")
            lines = raw.splitlines()
            line_count = len(lines)
            readable = True
        except Exception:
            line_count = 0
            readable = False
        jsonl_total_lines = 0
        jsonl_valid_lines = 0
        text_line_count = 0

    # --- hashes -------------------------------------------------------------
    path_h = _path_hash(path)
    content_sha = _content_hash(path)

    return {
        "id": path_h,
        "agent": _derive_agent(source_type),
        "source_type": source_type,
        "path": str(path),
        "path_hash": path_h,
        "project_bucket": _derive_project_bucket(path, home, source_type),
        "size_bytes": size_bytes,
        "mtime": mtime,
        "extension": path.suffix,
        "line_count": line_count,
        "readable": readable,
        "jsonl_total_lines": jsonl_total_lines,
        "jsonl_valid_lines": jsonl_valid_lines,
        "top_level_key_counts": top_level_key_counts,
        "text_line_count": text_line_count,
        "content_sha256": content_sha,
        "warnings": row_warnings,
    }


# ---------------------------------------------------------------------------
# Output builders
# ---------------------------------------------------------------------------


def _build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build ``inventory_summary.json`` structure (no *path* or *content_sha256*)."""
    by_agent: Counter[str] = Counter()
    by_source_type: Counter[str] = Counter()
    sizes: list[int] = []
    mtimes: list[float] = []
    parse_rate_buckets: dict[str, list[float]] = {}
    warning_counts: Counter[str] = Counter()
    sources: list[dict[str, Any]] = []

    for row in rows:
        agent = row["agent"]
        st = row["source_type"]

        by_agent[agent] += 1
        by_source_type[st] += 1

        size = row["size_bytes"]
        if size is not None:
            sizes.append(size)

        mt = row["mtime"]
        if mt is not None:
            mtimes.append(mt)

        jtl = row["jsonl_total_lines"]
        if jtl is not None and jtl > 0:
            rate = row["jsonl_valid_lines"] / jtl
            parse_rate_buckets.setdefault(st, []).append(rate)

        for w in row["warnings"]:
            wtype = w.split(":", 1)[0] if ":" in w else w
            warning_counts[wtype] += 1

        source_entry = {k: row[k] for k in SUMMARY_SOURCE_KEYS}
        sources.append(source_entry)

    agg_rates: dict[str, float] = {}
    for st, rates in parse_rate_buckets.items():
        agg_rates[st] = sum(rates) / len(rates) if rates else 0.0

    return {
        "total_files": len(rows),
        "by_agent": dict(by_agent),
        "by_source_type": dict(by_source_type),
        "size_bytes": {
            "min": min(sizes) if sizes else None,
            "max": max(sizes) if sizes else None,
            "total": sum(sizes),
        },
        "time_range": {
            "min_mtime": min(mtimes) if mtimes else None,
            "max_mtime": max(mtimes) if mtimes else None,
        },
        "parse_rates": agg_rates,
        "sources": sources,
        "warning_counts": dict(warning_counts),
    }


def _build_warnings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build ``warnings.json`` structure."""
    parse_warnings: list[dict[str, Any]] = []

    for row in rows:
        for w in row["warnings"]:
            if "json_parse_error" in w or "read_error" in w:
                parse_warnings.append(
                    {
                        "id": row["id"],
                        "path_hash": row["path_hash"],
                        "source_type": row["source_type"],
                        "warning": w,
                    }
                )

    return {
        "source_coverage": [],
        "parse_warnings": parse_warnings,
        "privacy_warnings": [],
        "dependency_warnings": [],
        "model_signal_limits": [],
        "skipped_steps": [],
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the inventory CLI and return a process-style exit code (0 on success)."""
    parser = argparse.ArgumentParser(
        description="Inventory agent conversation history and memory files."
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=["codex", "claude", "both"],
        help="Which agent(s) to inventory.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=_expand_path,
        help="Directory for output files.",
    )
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        type=_expand_path,
        help="User-specified root path (repeatable).",
    )
    parser.add_argument(
        "--codex-home",
        type=_expand_path,
        default=None,
        help="Override Codex home directory.",
    )
    parser.add_argument(
        "--claude-home",
        type=_expand_path,
        default=None,
        help="Override Claude home directory.",
    )
    parser.add_argument(
        "--no-defaults",
        action="store_true",
        help="Skip default home-directory discovery.",
    )

    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Resolve agent homes
    # ------------------------------------------------------------------
    codex_home: Path | None = args.codex_home
    claude_home: Path | None = args.claude_home

    if not args.no_defaults:
        if codex_home is None:
            env = os.environ.get("CODEX_HOME")
            if env:
                codex_home = _expand_path(env)

        if claude_home is None:
            env = os.environ.get("CLAUDE_CONFIG_DIR")
            if env:
                claude_home = _expand_path(env)

        home = Path.home()
        if codex_home is None:
            candidate = home / ".codex"
            if candidate.is_dir():
                codex_home = candidate

        if claude_home is None:
            candidate = home / ".claude"
            if candidate.is_dir():
                claude_home = candidate

    # ------------------------------------------------------------------
    # Discover candidates: (path, source_type, home)
    # Discovery order: user roots -> explicit agent homes -> env vars
    # -> standard home paths (already resolved above)
    # ------------------------------------------------------------------
    candidates: list[tuple[Path, str, Path | None]] = []

    # 1. User roots
    for root in args.root:
        for f, st in _discover_user_root_candidates(root):
            candidates.append((f, st, None))

    # 2. Agent homes
    agent_arg: str = args.agent
    if agent_arg in ("codex", "both") and codex_home is not None:
        for f, st in _discover_codex_candidates(codex_home):
            candidates.append((f, st, codex_home))

    if agent_arg in ("claude", "both") and claude_home is not None:
        for f, st in _discover_claude_candidates(claude_home):
            candidates.append((f, st, claude_home))

    # ------------------------------------------------------------------
    # Deduplicate by resolved path
    # ------------------------------------------------------------------
    seen: set[str] = set()
    unique: list[tuple[Path, str, Path | None]] = []
    for f, st, home in candidates:
        resolved = str(f.resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique.append((f, st, home))

    # ------------------------------------------------------------------
    # Process every candidate
    # ------------------------------------------------------------------
    rows: list[dict[str, Any]] = []
    for f, st, home in unique:
        row = _build_inventory_row(f, st, home)
        rows.append(row)

    # ------------------------------------------------------------------
    # Build output structures
    # ------------------------------------------------------------------
    summary = _build_summary(rows)
    warnings = _build_warnings(rows)

    # ------------------------------------------------------------------
    # Write output files
    # ------------------------------------------------------------------
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    inv_path = out_dir / "inventory.jsonl"
    with inv_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            json.dump(row, fh, ensure_ascii=False, default=str)
            fh.write("\n")

    (out_dir / "inventory_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    (out_dir / "warnings.json").write_text(
        json.dumps(warnings, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
