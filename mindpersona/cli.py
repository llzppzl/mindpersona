"""The `mindpersona` command: starts the MCP server in platform/claude/mcp_server.py.

It lets Claude Code run the server without a clone:
    claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
Arguments are passed on to the server unchanged.
"""
import os
import runpy
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SERVER_PATH = Path("platform") / "claude" / "mcp_server.py"
DEFAULT_MEMORY_DIR = Path.home() / ".mindpersona" / "memory"


def find_server() -> Path:
    """The installed copy inside this package, or the one in the source checkout this package is in."""
    for root in (PACKAGE_DIR, PACKAGE_DIR.parent):
        server = root / SERVER_PATH
        if server.is_file():
            return server
    raise SystemExit(f"mindpersona: {SERVER_PATH} not found next to {PACKAGE_DIR}")


def main() -> None:
    server = find_server()
    # An installed package lives in a folder that pip or uv may replace on the next install,
    # so keep saved adjustments in the home folder instead (a source checkout keeps using memory/)
    if server.is_relative_to(PACKAGE_DIR) and not os.environ.get("MINDPERSONA_MEMORY_DIR"):
        os.environ["MINDPERSONA_MEMORY_DIR"] = str(DEFAULT_MEMORY_DIR)
    if os.environ.get("MINDPERSONA_MEMORY_DIR"):
        Path(os.environ["MINDPERSONA_MEMORY_DIR"]).mkdir(parents=True, exist_ok=True)
    # Same as `python mcp_server.py ...`: the server's folder is importable and argv[0] is the script
    sys.path.insert(0, str(server.parent))
    sys.argv[0] = str(server)
    runpy.run_path(str(server), run_name="__main__")


if __name__ == "__main__":
    main()
