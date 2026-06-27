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
