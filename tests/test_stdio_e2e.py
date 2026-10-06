"""Start the real server over stdio and talk to it with the MCP client, the way Claude Code does.

By default this runs `python -m mindpersona.server` from this checkout.
Set MINDPERSONA_SERVER_CMD to test an installed command instead, e.g. MINDPERSONA_SERVER_CMD=mindpersona.
"""
import asyncio
import os
import shlex
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_DIR = Path(__file__).resolve().parent.parent


def server_params(memory_dir, server_args):
    env = {**os.environ, "MINDPERSONA_MEMORY_DIR": str(memory_dir)}
    env.pop("MINDPERSONA_PERSONA", None)
    if os.environ.get("MINDPERSONA_SERVER_CMD"):
        command, *args = shlex.split(os.environ["MINDPERSONA_SERVER_CMD"])
    else:
        command, args = sys.executable, ["-m", "mindpersona.server"]
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO_DIR), env.get("PYTHONPATH")]))
    return StdioServerParameters(command=command, args=[*args, *server_args], env=env)


def run_session(memory_dir, scenario, *server_args):
    async def main():
        async with stdio_client(server_params(memory_dir, server_args)) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                return await scenario(session, init)

    return asyncio.run(asyncio.wait_for(main(), timeout=60))


def text_of(result):
    return result.content[0].text


def test_server_starts_and_serves_prompts_and_tools(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # must not depend on the working directory

    async def scenario(session, init):
        prompts = (await session.list_prompts()).prompts
        intj = await session.get_prompt("mbti-intj")
        tools = (await session.list_tools()).tools
        estj = await session.call_tool("load_persona", {"mbti_type": "estj"})
        return init, prompts, intj, tools, estj

    init, prompts, intj, tools, estj = run_session(tmp_path / "memory", scenario)

    assert init.serverInfo.name == "mindpersona"
    assert "load_persona" in init.instructions
    assert len([p for p in prompts if p.name.startswith("mbti-")]) == 16
    assert intj.messages[0].content.text.startswith("# INTJ")
    assert {"load_persona", "update_mbti_memory"} <= {t.name for t in tools}
    assert text_of(estj).startswith("# ESTJ")


def test_feedback_is_saved_and_loaded_next_time(tmp_path):
    memory_dir = tmp_path / "memory"

    async def save(session, init):
        return await session.call_tool(
            "update_mbti_memory", {"mbti_type": "intj", "feedback_summary": "Skip the preamble"}
        )

    async def load(session, init):
        return await session.call_tool("load_persona", {"mbti_type": "intj"})

    saved = run_session(memory_dir, save)
    assert not saved.isError
    assert (memory_dir / "customized-intj.md").is_file()

    assert "Skip the preamble" in text_of(run_session(memory_dir, load))


def test_default_persona_is_sent_as_server_instructions(tmp_path):
    async def scenario(session, init):
        return init

    init = run_session(tmp_path / "memory", scenario, "--persona", "intj")

    assert init.instructions.startswith("MindPersona: the user chose INTJ")
    assert "# INTJ - 冷酷幕僚长" in init.instructions
