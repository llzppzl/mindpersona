"""Start the real server over stdio and talk to it with the MCP client, the way Claude Code does.

Read-only (list and get prompts, list tools), so nothing is written to memory/.
"""
import asyncio
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent.parent / "mcp_server.py"


def run_session(scenario):
    async def main():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
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


def test_mcp_2_gives_a_fix_instead_of_a_traceback():
    sys.path.insert(0, str(SERVER.parent))
    from mcp_server import require_mcp_1x

    class Mcp2Server:  # mcp 2.x's Server has no list_prompts decorator
        pass

    with pytest.raises(SystemExit, match="mcp>=1.3,<2"):
        require_mcp_1x(Mcp2Server)
