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

Confirmed method references on 2026-06-27:

- NIST AI RMF supports privacy-enhanced AI through data minimization,
  de-identification, aggregation, and tradeoff-aware risk handling.
- Microsoft Presidio supports PII detection and anonymization with predefined and
  custom recognizers, regex, NER, context, and anonymization operators.
- Presidio documentation warns that automated detection cannot guarantee finding all
  sensitive information.

Design consequence: use automated redaction as a support layer only. Final outputs
must still avoid raw transcript quoting by default and must receive a leak-oriented
review for paths, URLs, emails, secret-like values, private names, and raw excerpts.

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

Confirmed locally on 2026-06-27:

- Current environment is WSL2/Linux.
- `CODEX_HOME` is unset, so this environment uses `~/.codex`.
- `CLAUDE_CONFIG_DIR` is unset, so this environment uses `~/.claude`.
- Mounted Windows roots were not needed for this inspection.

Runtime rule: still check exact path expansion, environment variables, and
user-specified Windows-mounted roots during execution, because they are
environment-specific.

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

Online confirmation on 2026-06-27:

- Official Codex documentation says local state lives under `CODEX_HOME`, defaulting
  to `~/.codex`.
- Official Codex documentation says `history.jsonl` is under `CODEX_HOME` when
  history persistence is enabled.
- Official Codex documentation says memory files live under `~/.codex/memories/` by
  default.

Local confirmation on 2026-06-27:

- `~/.codex/sessions/` exists and contains 142 JSONL transcript files.
- `~/.codex/history.jsonl` exists and contained 470 valid JSONL rows with shape
  `session_id`, `text`, `ts`.
- `~/.codex/memories/` exists but contained no files in this environment.
- `~/.codex/archived_sessions/` was not present in this environment.
- 51,228 Codex session rows parsed successfully. Every row had top-level
  `timestamp`, `type`, and `payload`.
- Observed Codex session row types were `event_msg`, `response_item`,
  `turn_context`, `session_meta`, and `compacted`.

Runtime rule: do not assume Codex session JSONL schemas are stable. Inventory should
count keys, record parse warnings, and extract semantics only for fields documented in
the current `model-field-map.md`.

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

Online confirmation on 2026-06-27:

- Official Claude Code documentation says CLI transcripts are JSONL files at
  `~/.claude/projects/<project>/<session-id>.jsonl`.
- Official Claude Code documentation says the JSONL entry format is internal and may
  change between versions.
- Official Claude Code documentation says storage can move off `~/.claude` with
  `CLAUDE_CONFIG_DIR`.
- Official Claude Code documentation says auto memory lives under
  `~/.claude/projects/<project>/memory/` by default.

Local confirmation on 2026-06-27:

- `~/.claude/projects/` exists.
- 391 Claude transcript JSONL files were found, including nested subagent transcript
  files.
- 391 Claude transcript files parsed with 0 JSON failures.
- Common observed row types included `assistant`, `user`, `attachment`, `mode`,
  `last-prompt`, `permission-mode`, `system`, `file-history-snapshot`, `ai-title`,
  `queue-operation`, `agent-name`, and `worktree-state`.
- One project memory directory was found under `~/.claude/projects/<project>/memory/`
  with 6 Markdown files, including `MEMORY.md`.

Runtime rule: because Claude documents the JSONL shape as internal, scripts must be
format-tolerant and warnings-first. Prefer official script interfaces or `/export`
when a user asks for a Claude-native export rather than direct schema parsing.

Useful references to re-check:

- https://code.claude.com/docs/en/sessions
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/statusline
- https://code.claude.com/docs/en/model-config
