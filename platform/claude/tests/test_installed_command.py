"""The installed `mindpersona` command, started the way Claude Code starts it (over stdio).

Skipped unless MINDPERSONA_INSTALLED_CMD names the command, e.g. after `pip install .`:
    MINDPERSONA_INSTALLED_CMD=mindpersona python -m pytest platform/claude/tests/test_installed_command.py
CI runs it on a fresh install, so a packaging mistake (a missing skills/ folder, a wrong entry
point, memory saved inside site-packages) fails the build.
"""
import asyncio
import os
import shlex

import pytest

COMMAND = os.environ.get("MINDPERSONA_INSTALLED_CMD")
pytestmark = pytest.mark.skipif(not COMMAND, reason="set MINDPERSONA_INSTALLED_CMD to test an installed command")


def run(home, scenario, *args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    command, *base_args = shlex.split(COMMAND)
    env = {k: v for k, v in os.environ.items() if k != "MINDPERSONA_MEMORY_DIR"}
    env["HOME"] = str(home)

    async def main():
        params = StdioServerParameters(command=command, args=[*base_args, *args], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                return await scenario(session, init)

    return asyncio.run(asyncio.wait_for(main(), timeout=120))


def test_installed_server_serves_personas_and_keeps_feedback_in_home(tmp_path):
    async def first(session, init):
        prompts = (await session.list_prompts()).prompts
        tools = {t.name for t in (await session.list_tools()).tools}
        intj = (await session.get_prompt("mbti-intj")).messages[0].content.text
        saved = await session.call_tool("update_mbti_memory",
                                        {"mbti_type": "intj", "feedback_summary": "Lead with the conclusion"})
        return len(prompts), tools, intj, saved

    count, tools, intj, saved = run(tmp_path, first)
    assert count == 16
    assert {"update_mbti_memory", "load_persona", "list_adjustments", "remove_adjustment"} <= tools
    assert intj.startswith("# INTJ")
    assert not saved.isError
    assert (tmp_path / ".mindpersona" / "memory" / "customized-intj.md").is_file()

    async def second(session, init):
        prompt = (await session.get_prompt("mbti-intj")).messages[0].content.text
        listed = (await session.call_tool("list_adjustments", {"mbti_type": "intj"})).content[0].text
        return prompt, listed

    prompt, listed = run(tmp_path, second)
    assert "Lead with the conclusion" in prompt
    assert "1. [" in listed and "Lead with the conclusion" in listed


def test_installed_command_names_itself_in_help_and_in_a_terminal(tmp_path):
    from pathlib import Path
    import subprocess
    from .test_terminal_start import run_in_terminal

    command, *base_args = shlex.split(COMMAND)
    env = dict(os.environ, HOME=str(tmp_path))
    usage = subprocess.run([command, *base_args, "--help"], env=env, capture_output=True, text=True, timeout=60)
    assert usage.stdout.startswith("usage: mindpersona ")

    code, output = run_in_terminal([command, *base_args], env)
    assert code == 0
    assert "MindPersona is an MCP server" in output
    assert f"-- {Path(command).resolve()}\n" in output


def test_installed_server_takes_a_default_persona(tmp_path):
    async def scenario(session, init):
        return init.instructions or ""

    assert "INTJ persona as their default" in run(tmp_path, scenario, "--persona", "intj")
