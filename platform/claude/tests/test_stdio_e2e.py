"""Start the real server over stdio and talk to it with the MCP client, the way Claude Code does.

Nothing is written to memory/: the tests that save adjustments use a temporary folder.
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent.parent / "mcp_server.py"


def run_session(scenario, env=None):
    async def main():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                return await scenario(session, init)

    return asyncio.run(asyncio.wait_for(main(), timeout=60))


def test_server_starts_and_serves_prompts_and_tools(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # must not depend on the working directory

    async def scenario(session, init):
        prompts = (await session.list_prompts()).prompts
        intj = await session.get_prompt("mbti-intj")
        tools = (await session.list_tools()).tools
        return init, prompts, intj, tools

    init, prompts, intj, tools = run_session(scenario)

    assert init.serverInfo.name == "mindpersona"
    assert len([p for p in prompts if p.name.startswith("mbti-")]) == 16
    assert intj.messages[0].content.text.startswith("# INTJ")
    assert "update_mbti_memory" in {t.name for t in tools}


def test_tools_take_the_type_in_capitals_and_the_number_as_text(tmp_path):
    """The MCP library checks arguments against the tool schema before call_tool runs. Before, the
    schema listed only lowercase types, so "ESTJ" got "Input validation error" and the model had to
    try again; a number sent as text ("1") was refused the same way."""
    env = dict(os.environ, MINDPERSONA_MEMORY_DIR=str(tmp_path))

    async def scenario(session, init):
        calls = [("load_persona", {"mbti_type": "ESTJ"}),
                 ("update_mbti_memory", {"mbti_type": "INTJ", "feedback_summary": "Lead with the verdict"}),
                 ("list_adjustments", {"mbti_type": "INTJ"}),
                 ("remove_adjustment", {"mbti_type": "INTJ", "number": "1"}),
                 ("load_persona", {"mbti_type": "esfp"})]
        return [await session.call_tool(name, args) for name, args in calls]

    results = run_session(scenario, env)
    texts = [r.content[0].text for r in results]
    assert not any(r.isError for r in results), texts
    assert texts[0].startswith("Persona ESTJ loaded.")
    assert texts[1].startswith("✅ Feedback saved")
    assert "1. [" in texts[2] and "Lead with the verdict" in texts[2]
    assert texts[3].startswith("Removed: ") and "No saved adjustments for INTJ." in texts[3]
    assert texts[4].startswith("Persona ESFP loaded.")


def test_a_tool_call_that_fails_is_marked_as_an_error(tmp_path):
    """Before, a failed call came back with isError False and only a "❌" in its text, so Claude
    Code showed it like a success and the model could tell the user it had saved the adjustment."""
    env = dict(os.environ, MINDPERSONA_MEMORY_DIR=str(tmp_path))

    async def scenario(session, init):
        calls = [("update_mbti_memory", {"mbti_type": "intj", "feedback_summary": "x" * 400}),
                 ("remove_adjustment", {"mbti_type": "intj", "number": 3}),
                 ("update_mbti_memory", {"mbti_type": "intj", "feedback_summary": "Lead with the verdict"}),
                 ("list_adjustments", {"mbti_type": "intj"})]
        return [await session.call_tool(name, args) for name, args in calls]

    too_long, nothing_to_remove, saved, listed = run_session(scenario, env)
    assert too_long.isError and "too long" in too_long.content[0].text
    assert nothing_to_remove.isError and "No saved adjustments" in nothing_to_remove.content[0].text
    assert not saved.isError and saved.content[0].text.startswith("✅ Feedback saved")
    assert not listed.isError and "Lead with the verdict" in listed.content[0].text


def test_mcp_2_gives_a_fix_instead_of_a_traceback():
    sys.path.insert(0, str(SERVER.parent))
    from mcp_server import require_mcp_1x

    class Mcp2Server:  # mcp 2.x's Server has no list_prompts decorator
        pass

    with pytest.raises(SystemExit, match="mcp>=1.22,<2"):
        require_mcp_1x(Mcp2Server)
