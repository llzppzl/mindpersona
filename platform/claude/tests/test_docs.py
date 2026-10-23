"""The docs keep up with the server's tools."""
import asyncio
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


def test_claude_setup_guide_names_every_tool_the_user_can_ask_for():
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    for name in ("load_persona", "list_adjustments", "remove_adjustment"):
        assert f"`{name}`" in guide
