"""Started in a terminal, the server says what it is and stops, instead of waiting in silence.

It talks MCP over stdin and stdout. Before, `mindpersona` or `python mcp_server.py` typed in a
terminal printed nothing, waited for input, and did not stop on Ctrl+C. Its --help also said
"mcp_server.py" when the user had run the installed `mindpersona` command.
"""
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[1] / "mcp_server.py"
sys.path.insert(0, str(SERVER.parent))

from mcp_server import UVX_COMMAND, server_command, startup_persona, terminal_notice  # noqa: E402

pty = pytest.importorskip("pty")  # not on Windows


def run_in_terminal(cmd, env, timeout=30):
    """Run cmd with a pseudo-terminal as stdin, stdout and stderr; return (exit code, output)."""
    master, slave = pty.openpty()
    proc = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    output, deadline = b"", time.monotonic() + timeout
    while proc.poll() is None and time.monotonic() < deadline:
        if select.select([master], [], [], 0.1)[0]:
            try:
                output += os.read(master, 65536)
            except OSError:
                break
    if proc.poll() is None:
        proc.kill()
        pytest.fail(f"still waiting after {timeout}s; printed: {output.decode(errors='replace')!r}")
    while select.select([master], [], [], 0.1)[0]:
        try:
            chunk = os.read(master, 65536)
        except OSError:
            break
        if not chunk:
            break
        output += chunk
    os.close(master)
    return proc.returncode, output.decode(errors="replace").replace("\r\n", "\n")


def test_the_server_explains_itself_in_a_terminal_and_stops(tmp_path):
    env = dict(os.environ, MINDPERSONA_MEMORY_DIR=str(tmp_path))
    env.pop("MINDPERSONA_COMMAND", None)
    code, output = run_in_terminal([sys.executable, str(SERVER)], env)
    assert code == 0
    assert "MindPersona is an MCP server" in output
    assert f"claude mcp add mindpersona -s user -- {sys.executable} {SERVER}" in output


def test_a_wrong_persona_is_still_reported_in_a_terminal(tmp_path):
    env = dict(os.environ, MINDPERSONA_MEMORY_DIR=str(tmp_path))
    code, output = run_in_terminal([sys.executable, str(SERVER), "--persona", "abcd"], env)
    assert code == 1
    assert "Unknown persona 'abcd'" in output


def test_the_notice_names_the_command_that_was_run():
    assert "-- /opt/venv/bin/mindpersona\n" in terminal_notice({"MINDPERSONA_COMMAND": "/opt/venv/bin/mindpersona"})
    # A path with a space is quoted, so it can be pasted as is
    assert server_command({"MINDPERSONA_COMMAND": "/my tools/bin/mindpersona"}) == "'/my tools/bin/mindpersona'"


def test_a_command_in_the_uv_cache_is_given_as_the_uvx_line():
    for path in ("/home/me/.cache/uv/archive-v0/nWJOj-dbOXPGwGmB/bin/mindpersona",
                 "/home/me/.cache/uv/environments-v2/0232/64c4/bin/mindpersona"):
        assert server_command({"MINDPERSONA_COMMAND": path}) == UVX_COMMAND


def test_help_names_the_installed_command(capsys):
    with pytest.raises(SystemExit):
        startup_persona(["--help"], {"MINDPERSONA_COMMAND": "/opt/venv/bin/mindpersona"})
    assert capsys.readouterr().out.startswith("usage: mindpersona ")

    with pytest.raises(SystemExit):
        startup_persona(["--help"], {})
    assert capsys.readouterr().out.startswith("usage: mcp_server.py ")
