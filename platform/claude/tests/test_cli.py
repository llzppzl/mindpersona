"""The `mindpersona` command (mindpersona/cli.py) and the MINDPERSONA_MEMORY_DIR setting."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CLI = REPO / "mindpersona" / "cli.py"

# Stands in for mcp_server.py: records how it was started instead of waiting on stdin
FAKE_SERVER = """
import json, os, sys
from pathlib import Path
Path(os.environ["REPORT"]).write_text(json.dumps({
    "argv": sys.argv,
    "memory_dir": os.environ.get("MINDPERSONA_MEMORY_DIR"),
    "server_dir_importable": str(Path(__file__).parent) in sys.path,
}))
"""


def run_cli(package_parent, tmp_path, *args, memory_dir=None):
    """Run cli.py from <package_parent>/mindpersona/ with a fake HOME; return what the server saw."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "MINDPERSONA_MEMORY_DIR"}
    env.update(HOME=str(home), REPORT=str(tmp_path / "report.json"), PYTHONPATH=str(package_parent))
    if memory_dir:
        env["MINDPERSONA_MEMORY_DIR"] = str(memory_dir)
    code = "from mindpersona.cli import main; main()"
    # cwd=tmp_path so the repo's own mindpersona/ is not the one imported
    subprocess.run([sys.executable, "-c", code, *args], cwd=tmp_path, env=env, check=True, timeout=60)
    return json.loads((tmp_path / "report.json").read_text()), home


def make_install(tmp_path):
    """The layout of an installed wheel: mindpersona/cli.py and mindpersona/platform/claude/mcp_server.py."""
    site = tmp_path / "site-packages"
    pkg = site / "mindpersona"
    (pkg / "platform" / "claude").mkdir(parents=True)
    shutil.copy(CLI, pkg / "cli.py")
    (pkg / "__init__.py").write_text("")
    (pkg / "platform" / "claude" / "mcp_server.py").write_text(FAKE_SERVER)
    return site, pkg


def test_installed_command_keeps_adjustments_in_the_home_folder(tmp_path):
    site, pkg = make_install(tmp_path)
    seen, home = run_cli(site, tmp_path, "--persona", "intj")

    memory = home / ".mindpersona" / "memory"
    assert seen["memory_dir"] == str(memory)
    assert memory.is_dir()  # created, so the first saved adjustment can be written
    assert seen["argv"] == [str(pkg / "platform" / "claude" / "mcp_server.py"), "--persona", "intj"]
    assert seen["server_dir_importable"]


def test_memory_dir_setting_wins_over_the_home_folder(tmp_path):
    site, _ = make_install(tmp_path)
    mine = tmp_path / "my-memory"
    seen, home = run_cli(site, tmp_path, memory_dir=mine)

    assert seen["memory_dir"] == str(mine)
    assert mine.is_dir()
    assert not (home / ".mindpersona").exists()


def test_source_checkout_keeps_using_the_repo_memory_folder(tmp_path):
    checkout = tmp_path / "checkout"
    (checkout / "mindpersona").mkdir(parents=True)
    shutil.copy(CLI, checkout / "mindpersona" / "cli.py")
    (checkout / "mindpersona" / "__init__.py").write_text("")
    (checkout / "platform" / "claude").mkdir(parents=True)
    (checkout / "platform" / "claude" / "mcp_server.py").write_text(FAKE_SERVER)

    seen, home = run_cli(checkout, tmp_path)

    assert seen["memory_dir"] is None
    assert not (home / ".mindpersona").exists()


def test_server_reads_memory_dir_from_the_environment(tmp_path):
    env = dict(os.environ, MINDPERSONA_MEMORY_DIR=str(tmp_path))
    code = "import mcp_server; print(mcp_server.MEMORY_DIR)"
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO / "platform" / "claude", env=env,
                         capture_output=True, text=True, check=True, timeout=60).stdout
    assert out.strip() == str(tmp_path)
