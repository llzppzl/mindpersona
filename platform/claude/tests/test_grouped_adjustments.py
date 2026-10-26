"""Adjustments that the user grouped under "### ..." headings are loaded, listed and kept.

The saved adjustments are plain text that users edit by hand. Before, any line starting with "#"
ended the section, so everything under a "### Formatting" heading was in the file but never loaded
into the persona, never listed and could not be removed.
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

GROUPED = """# INTJ - your personal version

## Your personal adjustments

- [2026-10-01 10:00] Lead with the conclusion

### Formatting
- Use tables for comparisons
- No emojis

## Notes for myself

Not an adjustment.
"""


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    (folder / "customized-intj.md").write_text(GROUPED, encoding="utf-8")
    yield folder
    shutil.rmtree(folder)


def persona():
    return asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text


def saved(memory):
    return (memory / "customized-intj.md").read_text(encoding="utf-8")


def test_grouped_adjustments_are_loaded_with_their_heading(memory):
    text = persona()
    assert "Lead with the conclusion" in text
    assert "### Formatting\n- Use tables for comparisons\n- No emojis" in text
    # A level-2 heading still ends the section
    assert "Not an adjustment" not in text


def test_grouped_adjustments_are_listed_without_the_heading(memory):
    listed = list_adjustments("intj")[1]
    assert listed.splitlines()[1:] == ["1. [2026-10-01 10:00] Lead with the conclusion",
                                       "2. Use tables for comparisons", "3. No emojis"]


def test_a_grouped_adjustment_can_be_removed(memory):
    ok, message = remove_adjustment("intj", 3)
    assert ok and "Removed: No emojis" in message
    assert "No emojis" not in saved(memory)
    assert "### Formatting\n- Use tables for comparisons\n" in saved(memory)


def test_a_new_adjustment_goes_before_the_groups(memory):
    assert append_to_customized("intj", "Be brief")[0]
    text = saved(memory)
    assert text.index("Be brief") < text.index("### Formatting")
    assert text.index("Lead with the conclusion") < text.index("Be brief")


def test_a_new_adjustment_with_only_groups_goes_under_the_heading(memory):
    (memory / "customized-intj.md").write_text(
        "## Your personal adjustments\n\n### Tone\n- Be gentle\n", encoding="utf-8")
    assert append_to_customized("intj", "Be brief")[0]
    lines = saved(memory).splitlines()
    assert lines[2].endswith("Be brief")
    assert lines[3] == "### Tone"
    assert "Be gentle" in persona()
