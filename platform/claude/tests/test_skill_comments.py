"""Maintainer comments in skills/ are not sent to Claude Code, like on the other platforms."""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import MBTI_TYPES, SKILLS_DIR, get_prompt, skill_prompt

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import sync_platforms


@pytest.fixture(autouse=True)
def temp_memory_dir():
    original = mcp_server.MEMORY_DIR
    temp_dir = Path(tempfile.mkdtemp())
    mcp_server.MEMORY_DIR = temp_dir
    yield temp_dir
    mcp_server.MEMORY_DIR = original
    shutil.rmtree(temp_dir)


def prompt_text(mbti_type):
    return asyncio.run(get_prompt(f"mbti-{mbti_type}")).messages[0].content.text


@pytest.mark.parametrize("mbti_type", MBTI_TYPES)
def test_persona_has_no_comment_lines(mbti_type):
    assert "<!--" in (SKILLS_DIR / f"mbti-{mbti_type}.md").read_text(encoding="utf-8")
    text = prompt_text(mbti_type)
    assert "<!--" not in text
    assert "memory/customized-" not in text
    # The lines around the comment are still there
    assert "- Avoid:" in text and "- North star:" in text


@pytest.mark.parametrize("mbti_type", MBTI_TYPES)
def test_same_persona_text_as_the_other_platforms(mbti_type):
    skill = (SKILLS_DIR / f"mbti-{mbti_type}.md").read_text(encoding="utf-8")
    assert skill_prompt(skill) == sync_platforms.clean_prompt(skill)
    assert prompt_text(mbti_type).startswith(skill_prompt(skill))


def test_comments_inside_a_line_stay():
    assert skill_prompt("# T\n- use `<!-- -->` in HTML\n") == "# T\n- use `<!-- -->` in HTML"
