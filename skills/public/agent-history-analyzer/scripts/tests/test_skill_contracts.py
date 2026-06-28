import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]


def test_skill_discloses_required_analysis_design_references() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "references/user-habits-design.md" in skill_text
    assert "references/agent-behavior-design.md" in skill_text
    assert "references/model-signal-map.md" in skill_text

    user_habits = (
        SKILL_ROOT / "references" / "user-habits-design.md"
    ).read_text(encoding="utf-8")
    agent_behavior = (
        SKILL_ROOT / "references" / "agent-behavior-design.md"
    ).read_text(encoding="utf-8")

    assert "Preference Source Type" in user_habits
    assert "Preference Scope Type" in user_habits
    assert "Preference Drift" in user_habits
    assert "Anti-Anthropomorphism Rule" in agent_behavior
    assert "Cross-Model Comparison Rule" in agent_behavior


def test_workflow_defines_sampling_cleanup_and_verification_gates() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    lower_skill = skill_text.lower()

    assert "Initial report language" in skill_text
    assert "sampling_plan.json" in skill_text
    assert "`sample_reason`" in skill_text
    assert "Finalize Privacy Cleanup" in skill_text
    assert "inventory.jsonl" in skill_text
    assert "selected_text.jsonl" in skill_text
    assert "agent-behavior/behavior_events.jsonl" in skill_text
    assert "### 7. Verify Report Package" in skill_text
    assert "Completion criterion:" in skill_text

    for gate in [
        "required reports exist",
        "json files parse",
        "csv evidence tables have",
        "warnings.md contains all required sections",
        "raw working files were removed",
        "privacy scan passes",
        "model signal limits are stated",
        "verification evidence",
    ]:
        assert gate in lower_skill


def test_report_schema_defines_language_sampling_retention_and_verification() -> None:
    schema = (SKILL_ROOT / "references" / "report-schemas.md").read_text(
        encoding="utf-8"
    )

    for heading in [
        "## Report Language And Translation",
        "## Artifact Retention",
        "## Sampling Plan Schema",
        "## Report Package Verification",
    ]:
        assert heading in schema

    for token in [
        "report-{lang}.md",
        "warnings-{lang}.md",
        "Derived language outputs translate existing report content only",
        "sampling_plan.json",
        "sample_reason",
        "recent",
        "oldest",
        "largest",
        "memory",
        "project_bucket_coverage",
        "warning_pattern",
        "high_value_preference_event",
        "full-corpus reading",
        "completion_vs_verification",
    ]:
        assert token in schema

    assert "## Model Signal Limits" in schema


def test_user_and_agent_reports_have_readability_contracts() -> None:
    user_habits = (
        SKILL_ROOT / "references" / "user-habits-design.md"
    ).read_text(encoding="utf-8")
    agent_behavior = (
        SKILL_ROOT / "references" / "agent-behavior-design.md"
    ).read_text(encoding="utf-8")

    for token in [
        "## Readable Report Pattern",
        "### Finding Card Format",
        "### Collaboration Decision Matrix",
        "### Task Type Patterns",
        "### Privacy-Safe Examples",
        "future agent behavior protocol",
        "forbidden_action",
        "allowed_alternative",
    ]:
        assert token in user_habits

    for token in [
        "Sample Bias Notes",
        "Tool Trajectory",
        "observed_verification",
        "completion_claim_only",
        "Failure Modes And Recovery",
        "context compaction",
        "## Future Use Suggestions",
        "## Next Analysis Plan",
    ]:
        assert token in agent_behavior


def test_skill_package_has_no_stale_plan_markers() -> None:
    marker_parts = [
        r"NEEDS[_]",
        r"Placeholde[r]",
        r"not yet confirme[d]",
        r"references/model-fiel[d]-map",
        r"references/implementatio[n]-design",
        r"TB[D]",
        r"TOD[O]",
        r"implement late[r]",
        r"fill in detail[s]",
    ]
    marker_re = re.compile("|".join(marker_parts))
    offenders: list[str] = []

    for path in SKILL_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".venv" in path.parts or ".output" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if marker_re.search(text):
            offenders.append(str(path.relative_to(SKILL_ROOT)))

    assert offenders == []
