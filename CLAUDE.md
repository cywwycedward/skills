# CLAUDE.md

## Common Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Workspace Guidelines

### 1. Workspace Structure

This repository stores Codex skills.

```text
.
|-- AGENTS.md              # Repository-level agent guidance
|-- CLAUDE.md              # Repository-level agent guidance for Claude
`-- skills/
    |-- private/           # Personal skills; useful as references, not guaranteed portable
    |   `-- <skill-name>/
    |       |-- SKILL.md
    |       `-- ...
    `-- public/            # Reusable skills; designed to work outside the owner's machine
        `-- <skill-name>/
            |-- SKILL.md
            `-- ...
```

Rules:
- Put skill content under `skills/`, not at the repository root.
- Each direct child of `skills/private/` or `skills/public/` is one skill package.
- `private` skills may include personal paths, accounts, worktrees, vaults, or habits.
- `public` skills should avoid personal coupling and document required setup.
- Add new skills to `private` by default; move them to `public` only after making them portable.

### 2. Git-Guidelines

#### Scope Ignore Rules By Ownership

**Root `.gitignore` handles root-level noise. Nested projects own their own ignores.**

When editing ignore rules:
- Keep root `.gitignore` focused on repository-level files, editor state, local env files, and root-level tool caches.
- Don't add skill-specific runtime state, build outputs, language caches, or generated files to the root `.gitignore`.
- If a skill needs files ignored, add or update that skill's local `.gitignore`.
- Use root-anchored patterns when the rule is meant only for the repository root.

#### Branch Management By Intent

**Branch names start with the work's ownership scope, then follow Git Flow intent.**

Before creating a development branch:
- Classify repository maintenance work under `repo/***`.
- Classify skill development work under `<skill-name>/***`, where `<skill-name>` is the skill package directory name.
- Use Git Flow-style intent under that ownership prefix.
- Use `feature` for new behavior, content, or capabilities.
- Use `hotfix` for urgent fixes to broken behavior, bad guidance, or incorrect shipped content.
- Do not create `release/***` branches; this repository does not use release branches.

Examples:
- Repository maintenance feature: `repo/feature/update-agent-guidance`
- Repository maintenance hotfix: `repo/hotfix/fix-root-gitignore`
- Skill feature: `<skill-name>/feature/add-reference-workflow`
- Skill hotfix: `<skill-name>/hotfix/fix-invalid-command`