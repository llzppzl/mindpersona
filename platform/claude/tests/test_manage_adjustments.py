"""Listing and removing saved adjustments"""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import append_to_customized, list_adjustments, remove_adjustment


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    yield folder
    shutil.rmtree(folder)


def test_list_numbers_the_saved_adjustments(memory):
    append_to_customized("intj", "Lead with the conclusion")
    append_to_customized("intj", "Use tables for comparisons")
    ok, text = list_adjustments("INTJ")
    assert ok
    lines = text.splitlines()
    assert lines[0] == "Saved adjustments for INTJ:"
    assert lines[1].startswith("1. [") and lines[1].endswith("] Lead with the conclusion")
    assert lines[2].startswith("2. [") and lines[2].endswith("] Use tables for comparisons")


def test_nothing_saved(memory):
    assert list_adjustments("estj") == (True, "No saved adjustments for ESTJ.")
    ok, text = remove_adjustment("estj", 1)
    assert not ok and "No saved adjustments" in text


def test_remove_deletes_only_that_one_and_the_persona_stops_loading_it(memory):
    for summary in ["first", "second", "third"]:
        append_to_customized("intj", summary)
    ok, text = remove_adjustment("intj", 2)
    assert ok
    assert text.startswith("Removed: [") and "] second" in text.splitlines()[0]
    content = (memory / "customized-intj.md").read_text(encoding="utf-8")
    assert "first" in content and "third" in content and "second" not in content

    prompt = asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text
    assert "] first" in prompt and "] third" in prompt and "] second" not in prompt


def test_bad_numbers_change_nothing(memory):
    append_to_customized("intj", "only one")
    before = (memory / "customized-intj.md").read_text(encoding="utf-8")
    for bad in (0, 2, "x", None):
        ok, _ = remove_adjustment("intj", bad)
        assert not ok
    assert (memory / "customized-intj.md").read_text(encoding="utf-8") == before


def test_unknown_type(memory):
    ok, text = list_adjustments("abcd")
    assert not ok and "Valid types" in text


def test_old_format_files_can_be_listed_and_edited(memory):
    legacy = "## 你的私人调整"
    (memory / "customized-intj.md").write_text(f"# INTJ\n\n{legacy}\n\n- [2026-04-15 12:34] Be brief\n- [2026-04-16 09:00] No emoji\n",
                                               encoding="utf-8")
    assert "1. [2026-04-15 12:34] Be brief" in list_adjustments("intj")[1]
    assert remove_adjustment("intj", 1)[0]
    assert "1. [2026-04-16 09:00] No emoji" in list_adjustments("intj")[1]


def test_lines_written_by_hand_are_listed_and_can_be_removed(memory):
    # Everything under the heading is loaded into the persona, so the list must show all of it,
    # however it was written; the template's comments are not adjustments
    file = memory / "customized-intj.md"
    file.write_text("# INTJ\n\n## Your personal adjustments\n\n<!-- my notes\n- not an entry -->\n"
                    "* No emojis\nAnswer in British English\n- [2026-04-15 12:34] Be brief\n\n"
                    "<!-- Format: - [time] feedback -->\n", encoding="utf-8")
    loaded = mcp_server.extract_adjustments(file.read_text(encoding="utf-8"))
    assert "No emojis" in loaded and "British English" in loaded and "not an entry" not in loaded

    ok, text = list_adjustments("intj")
    assert ok
    assert text.splitlines()[1:] == ["1. No emojis", "2. Answer in British English", "3. [2026-04-15 12:34] Be brief"]

    ok, text = remove_adjustment("intj", 1)
    assert ok and text.startswith("Removed: No emojis")
    assert "No emojis" not in mcp_server.extract_adjustments(file.read_text(encoding="utf-8"))
    assert "<!-- my notes" in file.read_text(encoding="utf-8")


def test_the_tools_are_offered_and_work_through_call_tool(memory):
    names = {t.name for t in asyncio.run(mcp_server.list_tools())}
    assert {"list_adjustments", "remove_adjustment"} <= names
    append_to_customized("isfp", "Gentle tone")
    listed = asyncio.run(mcp_server.call_tool("list_adjustments", {"mbti_type": "isfp"}))[0].text
    assert "1. [" in listed
    removed = asyncio.run(mcp_server.call_tool("remove_adjustment", {"mbti_type": "isfp", "number": 1}))[0].text
    assert removed.startswith("Removed:") and "No saved adjustments for ISFP." in removed
