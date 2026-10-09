"""--persona / MINDPERSONA_PERSONA make a persona the default for every session."""
import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

SERVER = Path(__file__).parent.parent / "mcp_server.py"
sys.path.insert(0, str(SERVER.parent))
import mcp_server
from mcp_server import startup_persona, persona_instructions, get_prompt


@pytest.fixture
def temp_memory_dir():
    original = mcp_server.MEMORY_DIR
    temp_dir = Path(tempfile.mkdtemp())
    mcp_server.MEMORY_DIR = temp_dir
    yield temp_dir
    mcp_server.MEMORY_DIR = original
    shutil.rmtree(temp_dir)


def test_no_persona_by_default():
    assert startup_persona([], {}) is None
    assert startup_persona([], {"MINDPERSONA_PERSONA": ""}) is None


def test_persona_from_argument_or_environment():
    assert startup_persona(["--persona", "INTJ"], {}) == "intj"
    assert startup_persona(["--persona=estj"], {}) == "estj"
    assert startup_persona([], {"MINDPERSONA_PERSONA": " Infp "}) == "infp"
    # The argument wins over the environment
    assert startup_persona(["--persona", "entj"], {"MINDPERSONA_PERSONA": "infp"}) == "entj"


def test_unknown_persona_stops_with_the_valid_types():
    for args, env in [(["--persona", "abcd"], {}), ([], {"MINDPERSONA_PERSONA": "../x"})]:
        with pytest.raises(SystemExit) as e:
            startup_persona(args, env)
        assert "intj" in str(e.value.code)


def test_instructions_hold_the_persona_and_saved_adjustments(temp_memory_dir):
    assert mcp_server.append_to_customized("intj", "Answer in English")[0]
    text = asyncio.run(persona_instructions("intj"))
    prompt = asyncio.run(get_prompt("mbti-intj")).messages[0].content.text
    assert text.startswith("The user chose the MindPersona INTJ persona as their default.")
    assert text.endswith(prompt)
    assert "Answer in English" in text


def initialize(*args, env=None):
    """Start the server over stdio like Claude Code does and return its initialize result."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER), *args],
                                       env={**os.environ, **(env or {})})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                return await session.initialize()

    return asyncio.run(go())


def test_server_sends_the_persona_as_instructions():
    skill = (mcp_server.SKILLS_DIR / "mbti-estj.md").read_text(encoding="utf-8").strip()
    assert skill in initialize("--persona", "estj").instructions
    assert skill in initialize(env={"MINDPERSONA_PERSONA": "estj"}).instructions


def test_server_without_persona_has_no_instructions(monkeypatch):
    monkeypatch.delenv("MINDPERSONA_PERSONA", raising=False)
    assert not initialize().instructions
