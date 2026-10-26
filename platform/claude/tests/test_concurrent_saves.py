"""Saves from several servers at the same time all stay saved.

Every Claude Code window starts its own server. Each save reads the file, adds a line and writes it
back, so two saves at the same moment both read the old file and the one written last dropped the
other's adjustment, after it had been reported as saved.
"""
import multiprocessing
import os
import pathlib
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

SERVER_DIR = str(Path(__file__).parent.parent)
sys.path.insert(0, SERVER_DIR)
import mcp_server
from mcp_server import append_to_customized, list_adjustments, remove_adjustment


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    yield folder
    shutil.rmtree(folder)


def save_many(name, memory_dir, count):
    """Runs in its own process, like the server of another Claude Code window"""
    sys.path.insert(0, SERVER_DIR)
    import mcp_server as server
    # Set here, not through MINDPERSONA_MEMORY_DIR: this test module, imported in the new process
    # to find this function, has already imported the server with the repo's memory/ folder
    server.MEMORY_DIR = Path(memory_dir)
    for i in range(count):
        ok, message = server.append_to_customized("intj", f"{name} preference {i}")
        assert ok, message


def test_saves_from_several_servers_at_once_are_all_kept(memory):
    workers = [multiprocessing.get_context("spawn").Process(target=save_many, args=(name, str(memory), 20))
               for name in ("alpha", "beta", "gamma")]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=120)
        assert worker.exitcode == 0
    text = (memory / "customized-intj.md").read_text(encoding="utf-8")
    assert sum("preference" in line for line in text.splitlines()) == 60
    assert sorted(p.name for p in memory.iterdir()) == ["customized-intj.md"]


def test_a_save_waits_for_a_change_in_progress(memory, monkeypatch):
    append_to_customized("intj", "first")
    lock = memory / ".customized-intj.md.lock"
    lock.touch()
    monkeypatch.setattr(mcp_server, "LOCK_WAIT_SECONDS", 0.2)
    ok, message = append_to_customized("intj", "second")
    assert not ok and "another MindPersona server" in message
    ok, message = remove_adjustment("intj", 1)
    assert not ok and "nothing changed" in message
    lock.unlink()
    assert append_to_customized("intj", "second")[0]
    listed = list_adjustments("intj")[1].splitlines()
    assert listed[-1].startswith("2. ") and listed[-1].endswith(" second")


def test_a_lock_left_by_a_killed_server_is_taken_over(memory):
    lock = memory / ".customized-intj.md.lock"
    lock.touch()
    old = time.time() - mcp_server.STALE_LOCK_SECONDS - 5
    os.utime(lock, (old, old))
    assert append_to_customized("intj", "Lead with the conclusion")[0]
    assert not lock.exists()


def test_a_lock_left_by_a_killed_server_is_ignored_by_git():
    gitignore = (Path(__file__).resolve().parents[3] / ".gitignore").read_text(encoding="utf-8")
    pattern = "memory/.customized-*.lock"
    assert pattern in gitignore.splitlines()
    assert pathlib.PurePath("memory", ".customized-intj.md.lock").match(pattern)
