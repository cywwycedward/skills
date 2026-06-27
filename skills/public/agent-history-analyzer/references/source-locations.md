# Source Locations

This reference owns corpus discovery, path handling, and source-location caveats for
the Agent History Analyzer skill.

## Scope Guard

Version 1 analyzes conversation history and memory only.

Include only:

- Codex transcript/history candidates.
- Codex generated memory candidates, if present.
- Claude Code transcript candidates.
- Claude Code project memory candidates, if present.
- User-specified transcript or memory files/directories.

Exclude by default:

- `AGENTS.md`
- `AGENTS.override.md`
- `CLAUDE.md`
- `.claude/rules/`
- `.codex/config.toml`
- Claude settings files
- MCP configuration
- provider configuration
- environment files
- credentials
- project source code
- project documentation
- git history

Do not read excluded files to "understand context". If the user wants to analyze
agent rule files or project instructions, design a separate branch or skill.

## Privacy Guard

Default behavior:

- Read only the minimum needed transcript and memory data.
- Prefer aggregate metrics and anonymized findings.
- Do not quote raw transcript content in the final report by default.
- If examples are useful, paraphrase them or use short redacted snippets.
- Report sensitive findings by category and count, not by raw value.
- Save only the privacy-safe report package under the skill-local `.output/`
  directory by default.
- Do not save long-lived user profiles unless the user explicitly requests them.

Sensitive categories to redact or count:

- API keys, tokens, secrets, and high-entropy identifiers.
- Email addresses.
- Account names.
- Absolute paths.
- URLs.
- Private repository names.
- Customer, client, or project names where detectable.
- Credentials and authentication material.

Regex redaction is not a complete privacy guarantee. The agent must still avoid
copying raw private content into outputs.

## Corpus Location Model

Use three distinct concepts:

1. Global state root
   - A tool-wide state directory, usually under the user's home directory.
   - This can physically contain sessions and memories for many projects.

2. Project-scoped state under global root
   - Data stored under the global state root but partitioned by project path or
     project identifier.

3. Repo-local project context
   - Rule or configuration files inside a project repository.
   - Excluded from version 1 analysis.

Codex and Claude Code can store all or most project session data under a global root,
while repository-local rule files are separate and out of scope.

## Source Discovery Priority

Discovery order:

1. User-specified transcript or memory paths.
2. User-specified agent data roots.
3. Tool-specific environment variables, such as `CODEX_HOME`.
4. Standard home-directory paths for the current OS.

Do not perform broad full-disk searches.

If a default location is missing, report it as missing and continue with other
available sources.

## OS Path Handling

Support at least:

- Linux/macOS home paths: `~/.codex`, `~/.claude`
- Windows home paths: `%USERPROFILE%\.codex`, `%USERPROFILE%\.claude`
- WSL paths: Linux home paths first; allow the user to specify Windows-mounted roots
  such as `/mnt/c/Users/<user>/.codex` or `/mnt/c/Users/<user>/.claude`.

NEEDS_LOCAL_CONFIRMATION: exact path expansion, environment variables, and mounted
Windows locations must be checked in the user's current environment during execution.

## Codex Data Sources

Currently expected candidates:

- `$CODEX_HOME/sessions/`
- `$CODEX_HOME/archived_sessions/`
- `$CODEX_HOME/history.jsonl`
- `$CODEX_HOME/memories/`
- If `CODEX_HOME` is unset, use the platform equivalent of `~/.codex`.

Understanding:

- Codex's global state root can contain sessions and generated memories across
  projects.
- Project-local Codex context files such as `AGENTS.md` and `.codex/config.toml` are
  excluded from this skill.
- Session/project attribution may need to be inferred from local transcript metadata,
  working directory fields, path fields, or surrounding rollout/session events.

NEEDS_ONLINE_CONFIRMATION: refresh official Codex documentation before hard-coding
current default locations or supported memory behavior.

NEEDS_LOCAL_CONFIRMATION: inspect local Codex transcript shapes before relying on
specific field names. Do not assume session JSONL schemas are stable.

Useful references to re-check:

- https://developers.openai.com/codex/cli/features
- https://developers.openai.com/codex/app/troubleshooting
- https://developers.openai.com/codex/memories
- https://developers.openai.com/codex/config-reference
- https://github.com/openai/codex

## Claude Code Data Sources

Currently expected candidates:

- `~/.claude/projects/<escaped-project-path>/<session-id>.jsonl`
- `~/.claude/projects/<escaped-project-path>/memory/*.md`

Understanding:

- Claude Code stores transcripts under a global state root partitioned by project.
- Claude project memory can also live under the global state root, partitioned by
  project.
- User-level and project-level `CLAUDE.md` files are rule/context files and are
  excluded from version 1.

NEEDS_ONLINE_CONFIRMATION: refresh official Claude Code documentation before
hard-coding current default locations or memory behavior.

NEEDS_LOCAL_CONFIRMATION: inspect local Claude transcript shapes before relying on
specific field names. Claude documentation states that JSONL entry format is internal
and may change.

Useful references to re-check:

- https://code.claude.com/docs/en/sessions
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/statusline
- https://code.claude.com/docs/en/model-config
