"""A save or removal that fails halfway leaves the saved adjustments as they were."""
import io
import pathlib
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import append_to_customized, remove_adjustment


@pytest.fixture
def memory(monkeypatch):
    folder = Path(tempfile.mkdtemp())
    monkeypatch.setattr(mcp_server, "MEMORY_DIR", folder)
    yield folder
    shutil.rmtree(folder)


class DiskFull(io.StringIO):
    """A file that takes the first few characters and then fails, like a full disk"""

    def __init__(self, path):
        super().__init__()
        self.path = path

    def write(self, text):
        with io.open(str(self.path), "w", encoding="utf-8") as f:
            f.write(text[:10])  # what reached the disk before the error
        raise OSError(28, "No space left on device")


def fail_writes(monkeypatch):
    real_open = pathlib.Path.open

    def open_(self, mode="r", *args, **kwargs):
        return DiskFull(self) if "w" in mode else real_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "open", open_)


def saved(memory):
    return (memory / "customized-intj.md").read_text(encoding="utf-8")


def leftovers(memory):
    return sorted(p.name for p in memory.iterdir() if p.name != "customized-intj.md")


def test_a_failed_save_keeps_the_adjustments_already_saved(memory, monkeypatch):
    append_to_customized("intj", "Lead with the conclusion")
    append_to_customized("intj", "Use tables for comparisons")
    before = saved(memory)

    fail_writes(monkeypatch)
    ok, message = append_to_customized("intj", "No emojis")
    assert not ok and "No space left" in message
    assert saved(memory) == before
    assert leftovers(memory) == []


def test_a_temporary_file_left_by_a_killed_server_is_ignored_by_git(memory, monkeypatch):
    # The temporary file holds the user's adjustments, so it must never be committed from a clone
    temps = []

    def replace(src, dst):
        temps.append(Path(src).name)
        raise KeyboardInterrupt  # stopped right before the rename

    monkeypatch.setattr(mcp_server.os, "replace", replace)
    with pytest.raises(KeyboardInterrupt):
        mcp_server.write_safely(memory / "customized-intj.md", "- [2026-04-15 12:34] Be brief\n")
    gitignore = (Path(__file__).resolve().parents[3] / ".gitignore").read_text(encoding="utf-8")
    assert "memory/.customized-*.tmp" in gitignore.splitlines()
    assert pathlib.PurePath("memory", temps[0]).match("memory/.customized-*.tmp")


def test_a_failed_removal_keeps_every_adjustment(memory, monkeypatch):
    append_to_customized("intj", "first")
    append_to_customized("intj", "second")
    before = saved(memory)

    fail_writes(monkeypatch)
    ok, message = remove_adjustment("intj", 1)
    assert not ok and "No space left" in message
    assert saved(memory) == before
    assert leftovers(memory) == []
