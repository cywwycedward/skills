# Agent Behavior Design

Reference for optional `agent-behavior/` analysis. Read only when the user explicitly
enables assistant or agent behavior analysis.

If the user does not answer or does not request this branch, keep it off.

## Primary Grouping

- Use actual/effective model buckets as evidence grouping metadata, but write the
  report around observable behavior dimensions and task contexts.
- Do not use displayed model as the primary grouping key.
- Displayed model may be reported only as an explanatory signal when the confirmed
  model signal map documents it.
- If actual/effective model cannot be established from the confirmed field mapping,
  use `unknown_actual_model`.
- A single session may contribute to multiple model buckets if the confirmed mapping
  supports turn-level model changes.

Normal skill use should rely on `model-signal-map.md` instead of re-researching model
field semantics.

## Analysis Frame

Default analysis frame: trace-based behavior coding.

Analyze observable agent behavior in conversation trajectories. Do not rate model
intelligence or intrinsic capability. Code these behavior dimensions:

1. Task framing and clarification.
2. Planning and decomposition.
3. Tool trajectory.
4. Grounding and evidence use.
5. Verification behavior.
6. Adaptivity and error recovery.
7. Instruction and boundary following.
8. Privacy and safety behavior.
9. Efficiency and cost control.
10. Communication and handoff quality.
11. Memory and context handling.

For each dimension, report observable patterns, supporting trace references,
frequency or rate when available, evidence strength, failure modes, and limits on what
was not observable. Within each actual/effective model bucket, include only dimensions
with evidence or mark important missing dimensions as `not_observed`.

Do not claim that a model is generally "smarter" or "better" from these observations.
Report only behavior patterns observed in the sampled traces.

## Report Sections

`agent-behavior/report.md` required sections:

```md
# Agent Behavior Report

## Scope
## Model Grouping Method
## Method
## Executive Summary
## Behavior By Actual/Effective Model
## Cross-Model Patterns
## Tool Trajectory
## Verification And Grounding
## Boundary And Privacy Behavior
## Failure Modes And Recovery
## Evidence Strength
## Future Use Suggestions
## Next Analysis Plan
## Limits
```

`## Method` must include `Sample Bias Notes`: task mix, tool-heavy skew, uneven
sample counts, project concentration, failure/recovery oversampling, and how those
limits affect comparison.

`## Behavior By Actual/Effective Model` uses this bucket template:

```md
### {actual_model_bucket}

Sample count:
Model signal source:
Task mix:
Bias and limits:
Dimension findings:
```

Bucket sections summarize behavior, not model capability. Each dimension finding
should include pattern, data support, failure mode when observed, and limit.

`## Tool Trajectory` must explain observable chains, not just tool counts:
request -> tool path -> output handling -> follow-up action or skipped follow-up.
High tool counts mean the analysis is tool-trace heavy and completion should be
judged from tool results, not assistant claims alone.

`## Verification And Grounding` must separate `observed_verification` from
`completion_claim_only`. A completion claim counts as observed verification only
when supported by test/build/check/screenshot/browser/source results or another
task-appropriate tool result.

`## Failure Modes And Recovery` uses these fields when evidence exists: `trigger`,
`diagnosis`, `corrective_action`, and `outcome`. For interruption, resume, rollback,
or context compaction, state whether the agent re-established current goal,
completed work, remaining work, and verification status.

`## Boundary And Privacy Behavior` must use segment IDs, path hashes, and aggregate
categories. Do not include raw transcript text, complete local paths, secret values,
or event text that reconstructs private content.

`## Future Use Suggestions` gives evidence-linked operating advice for future agent
use. Each suggestion cites finding IDs and avoids general model ranking. Useful
classes include coding tasks, long-running tasks, subagent tasks, UI tasks, research
tasks, and any multi-model comparison request.

`## Next Analysis Plan` lists 2-5 concrete next analysis actions that answer this
report's limits, such as completion-claim audit, verification-result audit, matched
task-type sampling, interrupted/resumed session audit, or memory influence audit.

## Evidence Strength

- `strong`: the pattern appears across multiple sessions or task types within the
  same actual/effective model bucket, with clear trace references.
- `medium`: the pattern appears across multiple samples but is concentrated in one
  task type, project, or tool environment.
- `weak`: the pattern appears in a small number of samples or a single session.
- `not_comparable`: sample size, task type, or tool environment differs too much for
  cross-model comparison.
- `unknown_model`: the behavior is observable but the actual/effective model cannot
  be confirmed.

## Cross-Model Comparison Rule

- Do not rank models by default.
- The report may compare observed behavior patterns across model buckets, but should
  avoid saying one model is generally better than another.
- If the user asks for comparison, control for task type, sample size, project, and
  tool environment when possible.
- If those controls are not possible, mark the comparison as `not_comparable`.

## Anti-Anthropomorphism Rule

- Do not explain agent behavior with personality or motive claims.
- Prefer observable descriptions, such as "this model bucket more often ended without
  verification in sampled traces".
- Avoid labels such as lazy, careless, confident, stubborn, or smart unless quoting
  the user's own wording in a redacted and necessary way.

## Sampling Priorities

Agent behavior sampling differs from user habit sampling. Prefer sessions with
observable trajectories:

- Tool calls.
- Plan, execution, and verification chains.
- Failures and recovery attempts.
- User corrections of the agent.
- Multiple actual/effective model buckets.
- Comparable samples for the same task type across model buckets.
- Explicit user boundaries, privacy requirements, or high-risk operations.

Short ordinary question-answer sessions are lower value for agent behavior analysis.

Use sampling reasons from `report-schemas.md` for agent behavior samples, especially
`agent_tool_coverage`, `model_bucket_coverage`, `comparable_task_coverage`,
`verification_pattern`, `failed_retried_interrupted`, and `privacy_security_pattern`.

## Model Signal Reporting

- `agent-behavior/report.md` must cite `model-signal-map.md`, including its date.
- The `Model Grouping Method` section must state how many sampled turns or sessions
  were assigned to actual/effective model buckets.
- It must also state how many sampled turns or sessions fell into
  `unknown_actual_model`.
- If model grouping is incomplete, the report must explain how that limits behavior
  comparisons.
