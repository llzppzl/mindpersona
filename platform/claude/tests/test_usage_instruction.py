"""The persona tells the model what to do with it, and that the user's adjustments come first.

The skills describe a user of the type: what they need and what frustrates them about AI. The
prompt sent the description with no instruction to answer that way, and nothing said which wins
when a saved adjustment ("be warmer") disagrees with a persona default ("no comforting words").
"""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import MBTI_TYPES, append_to_customized, call_tool, get_prompt, persona_instructions


@pytest.fixture(autouse=True)
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    yield folder
    shutil.rmtree(folder)


def prompt_text(mbti_type):
    return asyncio.run(get_prompt(f"mbti-{mbti_type}")).messages[0].content.text


@pytest.mark.parametrize("mbti_type", MBTI_TYPES)
def test_every_persona_says_how_to_use_it(mbti_type):
    text = prompt_text(mbti_type)
    usage = text.index("## Using this persona")
    assert f"answer the user the way this {mbti_type.upper()} persona describes" in text
    # After the persona, before the instruction about saving feedback
    assert text.index("- North star:") < usage < text.index("## Saving feedback")
    # A blank line before ---, so it is a separator and not the underline of a heading
    assert "\n\n---\n\n## Using this persona" in text


def test_without_adjustments_there_is_nothing_about_them():
    assert "follow the adjustment" not in prompt_text("intj")


def test_saved_adjustments_win_over_the_persona():
    append_to_customized("intj", "Be a little warmer when I am stressed")
    text = prompt_text("intj")
    assert text.index("Be a little warmer") < text.index("## Using this persona")
    assert "where one of them disagrees with the persona, follow the adjustment" in text


def test_load_persona_and_the_default_persona_say_it_once():
    loaded = asyncio.run(call_tool("load_persona", {"mbti_type": "estj"}))[0].text
    default = asyncio.run(persona_instructions("estj"))
    for text in (loaded, default):
        assert text.count("## Using this persona") == 1
