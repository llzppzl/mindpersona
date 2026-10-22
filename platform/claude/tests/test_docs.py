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


def test_claude_setup_guide_names_every_tool_the_user_can_ask_for():
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    for name in ("load_persona", "list_adjustments", "remove_adjustment"):
        assert f"`{name}`" in guide
