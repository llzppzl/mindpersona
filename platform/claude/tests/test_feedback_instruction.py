"""The feedback instruction sent with each persona, and the tool and prompt descriptions"""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server

CJK = re.compile(r"[\u4e00-\u9fff]")


def persona_text(name="mbti-intj"):
    result = asyncio.run(mcp_server.get_prompt(name))
    message = result.messages[0]
    content = message.content if hasattr(message, "content") else message["content"]
    return content.text if hasattr(content, "text") else content["text"]


def test_instruction_names_the_persona_and_the_tool():
    text = persona_text("mbti-estj")
    instruction = text[text.index("## Saving feedback"):]
    assert "update_mbti_memory" in instruction
    assert '`mbti_type` = "estj"' in instruction


def test_instruction_only_saves_lasting_preferences():
    instruction = mcp_server.TRIGGER_INSTRUCTION
    assert "lasting change" in instruction
    assert "Don't save" in instruction
    assert "frustration with their own code" in instruction
    assert "only about the current answer" in instruction


def test_confirmation_follows_the_users_language():
    assert "in the language they write in" in mcp_server.TRIGGER_INSTRUCTION


def test_instruction_and_descriptions_are_in_english():
    assert not CJK.search(mcp_server.TRIGGER_INSTRUCTION)
    tool = asyncio.run(mcp_server.list_tools())[0]
    assert not CJK.search(tool.description)
    assert not CJK.search(tool.inputSchema["properties"]["feedback_summary"]["description"])
    for prompt in asyncio.run(mcp_server.list_prompts()):
        assert not CJK.search(prompt.description)
