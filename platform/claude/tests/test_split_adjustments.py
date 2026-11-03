"""Adjustments saved under a second adjustments heading are loaded, listed and kept.

Older versions missed a heading written by hand in another case, or behind a byte order mark, and
added a second one at the end of the file for the next save. Once the first was found again, only
its section was read: everything under the second heading stopped being loaded or listed, and the
next save of the same adjustment added it again.
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

SPLIT = """# INTJ - your personal version

## Your Personal Adjustments

- No emojis

## Your personal adjustments

- [2026-10-01 10:00] Use tables

<!-- Format: - [time] feedback -->

## Notes for myself

Not an adjustment.
"""


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    (folder / "customized-intj.md").write_text(SPLIT, encoding="utf-8")
    yield folder
    shutil.rmtree(folder)


def saved(memory):
    return (memory / "customized-intj.md").read_text(encoding="utf-8")


def test_adjustments_under_both_headings_are_loaded(memory):
    text = asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text
    assert "- No emojis" in text
    assert "- [2026-10-01 10:00] Use tables" in text
    assert "Not an adjustment" not in text


def test_adjustments_under_both_headings_are_listed(memory):
    assert list_adjustments("intj") == (
        True, "Saved adjustments for INTJ:\n1. No emojis\n2. [2026-10-01 10:00] Use tables")


def test_an_adjustment_under_the_second_heading_is_not_saved_again(memory):
    ok, message = append_to_customized("intj", "use tables.")
    assert ok and "already saved" in message
    assert saved(memory) == SPLIT


def test_a_new_adjustment_goes_under_the_first_heading(memory):
    assert append_to_customized("intj", "Be brief")[0]
    text = saved(memory)
    assert text.index("No emojis") < text.index("Be brief") < text.index("## Your personal adjustments")


def test_an_adjustment_under_the_second_heading_can_be_removed(memory):
    ok, message = remove_adjustment("intj", 2)
    assert ok and "Removed: [2026-10-01 10:00] Use tables" in message
    assert "Use tables" not in saved(memory)
    assert "- No emojis" in saved(memory)
