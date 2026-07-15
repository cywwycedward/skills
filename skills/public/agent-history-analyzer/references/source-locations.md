# Source Locations

Reference for corpus discovery, include/exclude rules, and path conventions.
Read during inventory step to know which files to analyze and which to skip.

## Scope

Version 1 analyzes conversation history and memory only.

**Include:**
- Codex transcript/history candidates
- Codex generated memory candidates
- Claude Code transcript candidates
- Claude Code project memory candidates
- User-specified transcript or memory files/directories

**Exclude:**
- `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`
- `.claude/rules/`
- `.codex/config.toml`
- Claude settings files, MCP configuration, provider configuration
- Environment files, credentials
- Project source code
- Project documentation
- Git history

Do not read excluded files to "understand context."

## Discovery Priority

1. User-specified transcript or memory paths
2. User-specified agent data roots
3. Tool-specific environment variables (`CODEX_HOME`, `CLAUDE_CONFIG_DIR`)
4. Standard home-directory paths for the current OS

Do not perform broad full-disk searches. If a default location is missing, report it as missing and continue.

## Codex Sources

- `$CODEX_HOME/sessions/**/*.jsonl` → `codex_session`
- `$CODEX_HOME/archived_sessions/**/*.jsonl` → `codex_archived_session`
- `$CODEX_HOME/history.jsonl` → `codex_history`
- `$CODEX_HOME/memories/**/*.md` → `codex_memory`
- If `CODEX_HOME` is unset, use `~/.codex`

## Claude Code Sources

- `~/.claude/projects/**/*.jsonl` → `claude_session`
- `~/.claude/projects/**/memory/*.md` → `claude_project_memory`
- If `CLAUDE_CONFIG_DIR` is set, use that instead of `~/.claude`

## User-Specified Roots

- `.jsonl` files → `user_specified_transcript`
- `.md` files under a path segment named `memory` or filename starting with `memory` (case-insensitive) → `user_specified_memory`

## OS Path Handling

- Linux/macOS: `~/.codex`, `~/.claude`
- Windows: `%USERPROFILE%\.codex`, `%USERPROFILE%\.claude`
- WSL: Linux paths first; allow user to specify Windows-mounted roots like `/mnt/c/Users/<user>/.codex`

## Privacy

- Read only the minimum needed transcript and memory data
- Prefer aggregate metrics over raw quoting
- Do not quote raw transcript content in the final report by default
- Report sensitive findings by category and count, not by raw value
- Save report packages under `.output/` using the artifact layout in
  `report-schemas.md`
