"""A customized-*.md file that is not UTF-8 (edited by hand, saved in another encoding) must not
stop the persona from loading, and the tools say how to fix it."""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server

# What an editor writes when it saves "Cafe" with an accented e in Windows-1252 instead of UTF-8
NOT_UTF8 = ("# INTJ\n\n## Your personal adjustments\n\n- [2026-10-01 10:00] Café style\n").encode("cp1252")


@pytest.fixture
def memory(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", tmp_path)
    (tmp_path / "customized-intj.md").write_bytes(NOT_UTF8)
    return tmp_path


def test_the_persona_still_loads_and_says_why_adjustments_are_missing(memory):
    # Before: UnicodeDecodeError, so neither /mbti-intj nor load_persona gave any persona
    text = asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text
    assert text.startswith("# INTJ")
    assert "could not be read" in text
    assert "UTF-8" in text
    loaded = asyncio.run(mcp_server.call_tool("load_persona", {"mbti_type": "intj"}))[0].text
    assert loaded.startswith("Persona INTJ loaded.")


def test_the_default_persona_still_starts(memory):
    # --persona intj: the server used to stop at startup, so Claude Code showed "Failed to connect"
    assert "# INTJ" in asyncio.run(mcp_server.persona_instructions("intj"))


def test_the_tools_say_how_to_fix_the_file_and_change_nothing(memory):
    for ok, message in (mcp_server.list_adjustments("intj"),
                        mcp_server.remove_adjustment("intj", 1),
                        mcp_server.append_to_customized("intj", "Use tables")):
        assert ok is False
        assert "save it with the UTF-8 encoding" in message
    assert (memory / "customized-intj.md").read_bytes() == NOT_UTF8


def test_a_file_saved_with_a_byte_order_mark_is_read(tmp_path, monkeypatch):
    # Notepad's "UTF-8 with BOM" puts \ufeff before the heading, which then was not found
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", tmp_path)
    path = tmp_path / "customized-intj.md"
    path.write_text("\ufeff## Your personal adjustments\n\n- No emojis\n", encoding="utf-8")

    assert mcp_server.list_adjustments("intj") == (True, "Saved adjustments for INTJ:\n1. No emojis")
    text = asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text
    assert "- No emojis" in text

    assert mcp_server.append_to_customized("intj", "Use tables")[0]
    saved = path.read_text(encoding="utf-8")
    assert saved.count("## Your personal adjustments") == 1
    assert "- No emojis\n- [" in saved
