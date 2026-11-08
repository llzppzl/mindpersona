"""Start the real server over stdio and talk to it with the MCP client, the way Claude Code does.

Nothing is written to memory/: the tests that save adjustments use a temporary folder.
"""
import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .mcp_fields import field

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

    assert field(init, "serverInfo")["name"] == "mindpersona"
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
    assert not any(field(r, "isError") for r in results), texts
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
    assert field(too_long, "isError") and "too long" in too_long.content[0].text
    assert field(nothing_to_remove, "isError") and "No saved adjustments" in nothing_to_remove.content[0].text
    assert not field(saved, "isError") and saved.content[0].text.startswith("✅ Feedback saved")
    assert not field(listed, "isError") and "Lead with the verdict" in listed.content[0].text


def test_server_runs_on_mcp_2_style_handlers(tmp_path, monkeypatch):
    """mcp 2.x has no decorators and takes the handlers in the Server constructor. Before, the
    server stopped with "MindPersona needs mcp 1.x" there. CI also runs this file on a real mcp 2."""
    sys.path.insert(0, str(SERVER.parent))
    import mcp_server

    monkeypatch.setattr(mcp_server, "MEMORY_DIR", tmp_path)

    class Mcp2Server:
        def __init__(self, name, **handlers):
            self.name, self.handlers = name, handlers

    server = mcp_server.build_server(Mcp2Server)
    assert server.name == "mindpersona"
    assert set(server.handlers) == {"on_list_prompts", "on_get_prompt", "on_list_tools", "on_call_tool"}

    def handle(handler, **params):
        return asyncio.run(server.handlers[handler](None, SimpleNamespace(**params) if params else None))

    assert len(handle("on_list_prompts").prompts) == 16
    assert handle("on_get_prompt", name="mbti-intj", arguments=None).messages[0].content.text.startswith("# INTJ")
    assert "load_persona" in {t.name for t in handle("on_list_tools").tools}

    def call(name, arguments):
        result = handle("on_call_tool", name=name, arguments=arguments)
        return field(result, "isError"), result.content[0].text

    assert call("update_mbti_memory", {"mbti_type": "INTJ", "feedback_summary": "Lead with the verdict"}) == (
        False, f"✅ Feedback saved\n\nFile: {tmp_path / 'customized-intj.md'}")
    # A failed call, and arguments the 2.x low-level server does not check against the schema,
    # come back as failed results instead of failing the request
    assert call("remove_adjustment", {"mbti_type": "intj", "number": 5}) == (
        True, "❌ There is no adjustment 5 for INTJ; it has 1.")
    assert call("update_mbti_memory", None) == (True, "❌ mbti_type and feedback_summary are both required")
    failed, text = call("list_adjustments", {"mbti_type": 5})
    assert failed and text.startswith("❌ Unknown MBTI type: 5")
