"""The docs keep up with the server's tools."""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_server import list_tools

REPO = Path(__file__).resolve().parents[3]


def test_security_page_names_every_tool_that_changes_saved_adjustments():
    # SECURITY.md said to edit the files by hand after list_adjustments and remove_adjustment existed
    security = (REPO / "SECURITY.md").read_text(encoding="utf-8")
    tools = {t.name for t in asyncio.run(list_tools())}
    for name in ("update_mbti_memory", "list_adjustments", "remove_adjustment"):
        assert name in tools
        assert f"`{name}`" in security


def test_contributing_lists_the_sections_every_skill_has():
    # It listed "suitable tasks, interaction layer, ..." while the files use other headings
    contributing = (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8")
    skill = (REPO / "skills" / "mbti-intj.md").read_text(encoding="utf-8")
    headings = [line for line in skill.splitlines() if line.startswith("## ")]
    assert len(headings) == 5
    for heading in headings:
        assert f"`{heading}`" in contributing


def persona_names():
    """{"intj": "Cold Chief of Staff", ...} from the first line of each skill"""
    names = {}
    for skill in sorted((REPO / "skills").glob("mbti-*.md")):
        title = skill.read_text(encoding="utf-8").splitlines()[0]
        names[skill.stem.removeprefix("mbti-")] = title.split(" - ", 1)[1].strip()
    return names


def test_claude_md_uses_the_persona_names_of_the_skills():
    # It still called INTJ "Architect" and INFP "Mediator" after the skills were renamed
    claude_md = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    table = dict(re.findall(r"\| `([a-z]{4})` \| ([^|]+?) (?=\|)", claude_md))
    assert table == persona_names()


def test_claude_setup_guide_uses_the_persona_names_of_the_skills():
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    names = persona_names()
    examples = re.findall(r"switch to the ([A-Z]{4}) \(([^)]+)\) persona", guide)
    assert examples
    for mbti_type, name in examples:
        assert name == names[mbti_type.lower()]


def test_every_pain_point_in_the_readme_names_a_persona():
    # "Idea Translator" and "Agile Coach" are no persona's name, so a reader could not tell which
    # type to load for them
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    needs = [line for line in readme.splitlines() if line.strip().startswith("What you need:")]
    assert len(needs) == 4
    names = persona_names()
    for line in needs:
        match = re.search(r"the \*\*([A-Z]{4})\*\* persona", line)
        assert match, line
        mbti_type = match.group(1).lower()
        assert mbti_type in names
        # The quoted style is either the persona's own name, or the name follows in brackets
        style = re.search(r'\*\*"([^"]+)"\*\*', line).group(1)
        assert style == names[mbti_type] or f"({names[mbti_type]})" in line


def test_troubleshooting_says_what_the_server_prints_in_a_terminal():
    # It said the server "prints nothing and waits for input" after the server was changed to print
    # a note and exit, so a user checking a working command thought it was broken
    from mcp_server import terminal_notice
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    troubleshooting = guide.split("## Troubleshooting", 1)[1].split("\n## ", 1)[0]
    assert "waits for input" not in troubleshooting
    assert "prints a short note that it is an MCP server" in troubleshooting
    assert terminal_notice({}).startswith("MindPersona is an MCP server")
    assert "claude mcp add" in terminal_notice({})


def test_claude_setup_guide_names_every_tool_the_user_can_ask_for():
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    for name in ("load_persona", "list_adjustments", "remove_adjustment"):
        assert f"`{name}`" in guide
