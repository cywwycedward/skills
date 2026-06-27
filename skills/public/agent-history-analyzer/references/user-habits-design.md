# User Habits Design

Reference for user habit analysis. Read during sampling, close reading, and report
writing.

## Research Object

Analyze how the user collaborates with agent tools, not the private substance of the
user's business or project content.

Do not produce psychological profiles, personality judgments, or sensitive-attribute
inferences.

Focus on:

- How the user initiates tasks.
- When the user wants questions, plans, or direct execution.
- How the user corrects the agent and tightens boundaries.
- Risk preferences around privacy, file writes, network use, git, and tool calls.
- Preferred output forms and answer granularity.
- Verification expectations.
- Stable preferences appearing in memory files.

Treat business topics, project names, customer content, and private domain material as
redacted context categories, not report subjects.

## Report Sections

`user-habits/report.md` required sections:

```md
# User Habits Report

## Scope
## Method
## Preference Summary
## Collaboration Preferences
## Risk And Privacy Preferences
## Verification Preferences
## Output Preferences
## Tool And Workflow Preferences
## Memory-Derived Preferences
## Conflicts And Drift
## Evidence Strength
## Recommendations For Future Agent Collaboration
## Limits
```

## Evidence Strength

- `strong`: the preference appears across multiple sessions or projects, and
  transcript behavior agrees with memory records when memory is available.
- `medium`: the preference appears in multiple sessions but is concentrated in one
  project or time period, or only one evidence type supports it.
- `weak`: the preference appears in a small number of samples or may be temporary to
  the task context.
- `conflict`: sources disagree.

Every preference finding must carry an evidence strength. Do not present weak signals
as stable habits.

## Sampling Priorities

In addition to covering time, project, agent tool, and session size, oversample
high-value preference events:

- Sessions where the user corrects the agent.
- Sessions where the user explicitly states preferences or boundaries.
- Sessions where the user changes the desired process.
- Sessions involving privacy, security, persistence, or "do not read/save" limits.
- Sessions requesting verification, tests, citations, screenshots, or reproduction
  steps.
- Failed, retried, reverted, interrupted, or resumed tasks.
- Sessions near memory creation, update, conflict, or apparent staleness.

These events are more informative for user preferences than ordinary successful
task-completion sessions.

## Preference Source Type

- `explicit`: the user directly states the preference or a memory file records it.
- `inferred`: the preference is inferred from repeated behavior patterns.
- `mixed`: explicit and inferred evidence both support the preference.

Reports must distinguish explicit and inferred preferences. Treat inferred
preferences more conservatively when assigning evidence strength.

## Preference Scope Type

- `global`: applies across projects or task types.
- `project`: appears tied to a specific project or repository.
- `task_type`: appears tied to a task class, such as skill design, bug fixing, code
  review, writing, or research.
- `temporary`: appears tied to a short-term context or one current goal.
- `unknown`: not enough evidence to assign scope.

Each preference finding should state its likely scope.

## Memory-Derived Preferences

Memory-derived preference status:

- `confirmed`: transcript evidence supports the memory-derived preference.
- `stale`: recent transcript evidence no longer supports the preference.
- `conflicting`: memory files or transcripts disagree.
- `unverified`: there is not enough transcript evidence to validate the memory.

Do not treat memory as automatically true. The report may recommend memory changes,
but must not modify memory files automatically.

## Negative Preferences

Analyze explicit "do not" preferences as first-class findings. Represent them in
`user-habits/data-categories.json` and discuss them under the relevant report
sections.

## Preference Drift

Compare recent and older samples when the corpus spans enough time. Mark preference
drift status as:

- `stable`: consistent across the sampled history.
- `emerging`: appears mainly in recent samples.
- `declining`: appears historically but less often in recent samples.
- `changed`: recent evidence points in a different direction from older evidence.
- `unknown`: not enough time coverage to assess drift.

Do not treat old preferences as current preferences without checking recency.
