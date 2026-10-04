"""skills 和 memory 目录的查找规则"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mindpersona import server


def test_source_checkout_uses_repo_skills():
    assert server.find_skills_dir() == server.REPO_DIR / "skills"
    assert (server.SKILLS_DIR / "mbti-intj.md").is_file()


def test_installed_package_uses_packaged_skills(tmp_path, monkeypatch):
    package = tmp_path / "site-packages" / "mindpersona"
    (package / "skills").mkdir(parents=True)
    monkeypatch.setattr(server, "PACKAGE_DIR", package)

    assert server.find_skills_dir() == package / "skills"


def test_memory_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("MINDPERSONA_MEMORY_DIR", str(tmp_path / "mem"))

    assert server.find_memory_dir() == tmp_path / "mem"


def test_installed_package_keeps_memory_in_home(tmp_path, monkeypatch):
    """安装后不能把反馈写进包目录：uvx 的环境是临时的，升级也会丢"""
    monkeypatch.delenv("MINDPERSONA_MEMORY_DIR", raising=False)
    monkeypatch.setattr(server, "REPO_DIR", tmp_path / "site-packages")
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    assert server.find_memory_dir() == tmp_path / "home" / ".mindpersona" / "memory"


def test_memory_dir_is_created_on_first_feedback(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path / "not-yet" / "memory")

    ok, _ = server.append_to_customized("intj", "少说废话")

    assert ok
    assert (tmp_path / "not-yet" / "memory" / "customized-intj.md").is_file()
