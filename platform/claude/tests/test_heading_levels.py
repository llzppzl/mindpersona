"""An adjustments heading written by hand at another level, or with a colon, is still found.

Only "## Your personal adjustments" counted. Under a hand-written "# Your personal adjustments",
"### Your personal adjustments" or "## Your personal adjustments:", the user's adjustments were not
loaded or listed, and the next save added a second heading at the end of the file.
"""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import append_to_customized, list_adjustments, remove_adjustment

HEADINGS = ["# Your personal adjustments", "### Your personal adjustments", "## Your personal adjustments:",
            "## Your personal adjustments ##", "## \u4f60\u7684\u79c1\u4eba\u8c03\u6574\uff1a"]


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    yield folder
    shutil.rmtree(folder)


def write(memory, text):
    (memory / "customized-intj.md").write_text(text, encoding="utf-8")


def saved(memory):
    return (memory / "customized-intj.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("heading", HEADINGS)
def test_adjustments_under_the_heading_are_loaded_and_listed(memory, heading):
    write(memory, f"# INTJ - your personal version\n\n{heading}\n\n- No emojis\n")
    text = asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text
    assert "- No emojis" in text
    assert list_adjustments("intj") == (True, "Saved adjustments for INTJ:\n1. No emojis")


@pytest.mark.parametrize("heading", HEADINGS)
def test_a_save_goes_under_the_heading_instead_of_adding_another(memory, heading):
    write(memory, f"# INTJ - your personal version\n\n{heading}\n\n- No emojis\n")
    assert append_to_customized("intj", "Use tables")[0]
    text = saved(memory)
    assert text.count("adjustments") + text.count("\u8c03\u6574") == 1
    assert text.index("No emojis") < text.index("Use tables")
    assert append_to_customized("intj", "no emojis") == (
        True, "This adjustment was already saved, so it was not added again")


def test_an_adjustment_under_the_heading_can_be_removed(memory):
    write(memory, "# INTJ - your personal version\n\n# Your personal adjustments\n\n- No emojis\n- Use tables\n")
    ok, message = remove_adjustment("intj", 1)
    assert ok and "Removed: No emojis" in message
    assert "No emojis" not in saved(memory) and "- Use tables" in saved(memory)


def test_a_smaller_heading_inside_the_section_is_a_group_not_a_second_section(memory):
    # Counted as both, its entries were listed twice
    write(memory, "## Your personal adjustments\n\n- No emojis\n\n### Your personal adjustments\n\n- Use tables\n")
    assert list_adjustments("intj") == (True, "Saved adjustments for INTJ:\n1. No emojis\n2. Use tables")


def test_other_headings_and_plain_text_are_not_the_adjustments_heading():
    for line in ("# INTJ - your personal version", "## Your personal adjustments for work",
                 "Your personal adjustments", "**Your personal adjustments**", "#Your personal adjustments"):
        assert not mcp_server.is_adjustments_header(line), line
