"""A code block written by hand in the adjustments is part of the entry above it.

Users write adjustments by hand, and one can show an example in a fenced code block. Before, a
"# comment" line in the block was taken for a heading that ends the adjustments section, so every
adjustment after the block was neither loaded with the persona nor listed, and the fence "```"
was listed as an adjustment of its own.
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

WITH_CODE = """# INTJ - your personal version

## Your personal adjustments

- Write shell examples like this:
```bash
# install first

pip install x
```
- No emojis

## Notes for myself

Not an adjustment.
"""


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    (folder / "customized-intj.md").write_text(WITH_CODE, encoding="utf-8")
    yield folder
    shutil.rmtree(folder)


def persona():
    return asyncio.run(mcp_server.get_prompt("mbti-intj")).messages[0].content.text


def saved(memory):
    return (memory / "customized-intj.md").read_text(encoding="utf-8")


def test_adjustments_after_a_code_block_are_loaded(memory):
    text = persona()
    assert "```bash\n# install first\n\npip install x\n```\n- No emojis" in text
    assert "Not an adjustment" not in text


def test_a_code_block_is_listed_with_its_entry(memory):
    assert list_adjustments("intj")[1].splitlines()[1:] == [
        "1. Write shell examples like this: ```bash # install first pip install x ```",
        "2. No emojis"]


def test_an_entry_with_a_code_block_is_removed_whole(memory):
    ok, message = remove_adjustment("intj", 1)
    assert ok and "Removed: Write shell examples" in message
    text = saved(memory)
    assert "```" not in text and "install" not in text
    assert "- No emojis" in text


def test_a_new_adjustment_goes_after_the_code_block(memory):
    assert append_to_customized("intj", "Be brief")[0]
    text = saved(memory)
    assert text.index("- No emojis") < text.index("Be brief") < text.index("## Notes for myself")
    assert append_to_customized("intj", "No emojis")[1].startswith("This adjustment was already saved")


def test_a_heading_inside_a_code_block_is_not_the_adjustments_heading(memory):
    (memory / "customized-intj.md").write_text(
        "# Notes\n\n~~~\n## Your personal adjustments\n- not saved\n~~~\n", encoding="utf-8")
    assert list_adjustments("intj") == (True, "No saved adjustments for INTJ.")
    assert append_to_customized("intj", "Be brief")[0]
    # The real heading is added after the code block, which stays as it was
    assert saved(memory).startswith("# Notes\n\n~~~\n## Your personal adjustments\n- not saved\n~~~\n\n"
                                    "## Your personal adjustments\n\n- [")
    assert list_adjustments("intj")[1].splitlines()[1].endswith("Be brief")
