"""The server says which Python it needs when it is started with one that is too old."""
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parent.parent / "mcp_server.py"
GUIDE = Path(__file__).resolve().parents[3] / "platform" / "claude" / "README.md"


def run_as(version_info: tuple) -> subprocess.CompletedProcess:
    """Run the server as `python mcp_server.py` would, with sys.version_info set to version_info"""
    code = (f"import runpy, sys; sys.version_info = {version_info!r}; "
            f"runpy.run_path({str(SERVER)!r}, run_name='__main__')")
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, timeout=60)


def test_python_3_9_gets_a_clear_message():
    # macOS's own python3 is 3.9, which is what `which python3` gives in the clone setup. pip finds no
    # mcp for it, and the server stopped with "No module named 'mcp'", which the troubleshooting table
    # explained as the wrong python being used
    result = run_as((3, 9, 6, "final", 0))
    assert result.returncode == 1
    assert "MindPersona needs Python 3.10 or newer" in result.stderr
    assert "is Python 3.9" in result.stderr
    assert "Traceback" not in result.stderr


def test_setup_guide_names_the_python_it_needs():
    guide = GUIDE.read_text(encoding="utf-8")
    setup = guide.split("## Setup from a clone", 1)[1].split("\n## ", 1)[0]
    assert "Python 3.10 or newer" in setup
    troubleshooting = guide.split("## Troubleshooting", 1)[1].split("\n## ", 1)[0]
    assert "MindPersona needs Python 3.10 or newer" in troubleshooting
    assert "No matching distribution found for mcp" in troubleshooting
