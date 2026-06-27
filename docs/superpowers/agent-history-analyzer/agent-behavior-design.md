# Agent Behavior Research Design

Status: confirmed for design; pending implementation validation.

This reference owns optional `agent-behavior/` analysis. The branch is off by default.
During initialization, ask the user whether they also want to analyze assistant or
agent behavior. Enable this branch only when the user explicitly says yes or otherwise
asks to analyze assistant or agent behavior, model differences, or tool-use patterns.

If the user does not answer or does not request it, keep the branch off.

## Primary Grouping

- Group agent behavior findings first by `actual/effective model`.
- Do not use displayed model as the primary grouping key.
- Displayed model may be reported only as an explanatory signal when the confirmed
  model field map documents it.
- If actual/effective model cannot be established from the confirmed field mapping,
  use `unknown_actual_model`.
- A single session may contribute to multiple model buckets if the confirmed mapping
  supports turn-level model changes.

Normal skill use should rely on [model-field-map.md](model-field-map.md) instead of
re-researching model field semantics.

## Analysis Frame

Default analysis frame: trace-based behavior coding.

Analyze observable agent behavior in conversation trajectories. Do not rate model
intelligence or intrinsic capability. For each actual/effective model bucket, code:

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
was not observable.

Do not claim that a model is generally "smarter" or "better" from these observations.
Report only behavior patterns observed in the sampled traces.

Method references confirmed on 2026-06-27:

- https://arxiv.org/html/2503.16416v2
- https://arxiv.org/abs/2210.03629
- https://arxiv.org/html/2510.02837v3
- https://www.microsoft.com/en-us/research/project/guidelines-for-human-ai-interaction/
- https://airc.nist.gov/airmf-resources/airmf/3-sec-characteristics/

Confirmed method notes:

- ReAct is relevant because it frames agent behavior as interleaved reasoning and
  acting trajectories with external tool/environment interactions.
- The agent evaluation survey distinguishes final-response, stepwise, and
  trajectory-based assessment. This design uses trace-based behavior coding, closest
  to trajectory and stepwise assessment, but does not automate judgment with an LLM
  judge in version 1.
- Microsoft Human-AI Interaction Guidelines are relevant to interaction timing,
  correction, error handling, and behavior over time.
- NIST AI RMF trustworthiness characteristics are relevant to privacy, safety,
  transparency, explainability, and risk tradeoff coding.

Runtime rule: re-check these sources if implementation starts after substantial
upstream changes or if the report adds automated grading, benchmark-style scoring, or
model ranking.

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
## Limits
```

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
- Avoid labels such as lazy, careless, confident, stubborn, or smart unless quoting the
  user's own wording in a redacted and necessary way.

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

## Model Field Map Reporting

- `agent-behavior/report.md` must cite the confirmed model field mapping reference,
  such as `model-field-map.md`, including its version or date.
- The `Model Grouping Method` section must state how many sampled turns or sessions
  were assigned to actual/effective model buckets.
- It must also state how many sampled turns or sessions fell into
  `unknown_actual_model`.
- If model grouping is incomplete, the report must explain how that limits behavior
  comparisons.

## Observable Inputs

If enabled, the skill may analyze:

- Assistant messages.
- Tool call patterns.
- Tool result handling.
- Validation behavior.
- Self-correction behavior.
- Planning and execution style.
- Recorded model and provider signals when present.
