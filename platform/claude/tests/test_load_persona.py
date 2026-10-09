"""load_persona gives the model the same persona text as the /mbti-<type> prompt."""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import call_tool, get_prompt, list_tools, LOAD_PERSONA_TYPES


@pytest.fixture
def temp_memory_dir():
    original = mcp_server.MEMORY_DIR
    temp_dir = Path(tempfile.mkdtemp())
    mcp_server.MEMORY_DIR = temp_dir
    yield temp_dir
    mcp_server.MEMORY_DIR = original
    shutil.rmtree(temp_dir)


def run(coro):
    return asyncio.run(coro)


def test_tool_is_listed_with_every_type():
    tools = {t.name: t for t in run(list_tools())}
    tool = tools["load_persona"]
    assert sorted(tool.inputSchema["properties"]["mbti_type"]["enum"]) == sorted(LOAD_PERSONA_TYPES)
    assert len(LOAD_PERSONA_TYPES) == 16
    # The description says what each type is for, so the model can pick one
    for t in LOAD_PERSONA_TYPES:
        assert f"- {t.upper()}: " in tool.description
    assert "update_mbti_memory" in tools


def test_returns_the_same_text_as_the_prompt(temp_memory_dir):
    text = run(call_tool("load_persona", {"mbti_type": "ESTJ"}))[0].text
    prompt = run(get_prompt("mbti-estj")).messages[0].content.text
    assert text.startswith("Persona ESTJ loaded.")
    assert text.endswith(prompt)
    assert (Path(mcp_server.SKILLS_DIR) / "mbti-estj.md").read_text(encoding="utf-8").strip() in text


def test_includes_saved_adjustments(temp_memory_dir):
    assert mcp_server.append_to_customized("intj", "Answer in English")[0]
    text = run(call_tool("load_persona", {"mbti_type": "intj"}))[0].text
    assert "Answer in English" in text


def test_unknown_type_is_an_error_not_a_crash(temp_memory_dir):
    for bad in ["abcd", "../../etc/passwd", "", None]:
        text = run(call_tool("load_persona", {"mbti_type": bad}))[0].text
        assert text.startswith("❌ Unknown MBTI type")
        assert "intj" in text
    text = run(call_tool("load_persona", {}))[0].text
    assert text.startswith("❌ Unknown MBTI type")
