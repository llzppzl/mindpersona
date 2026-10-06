"""--persona: apply one persona to every reply through the server instructions"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mindpersona import server


def test_without_default_instructions_explain_the_tools():
    text = server.build_instructions()
    assert "load_persona" in text
    assert len(text) <= server.INSTRUCTIONS_LIMIT


def test_default_persona_instructions_contain_persona_and_adjustments(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path)
    server.save_adjustment("intj", "Skip the preamble")

    text = server.build_instructions("intj")

    assert text.startswith("MindPersona: the user chose INTJ")
    assert "# INTJ - 冷酷幕僚长" in text
    assert "Skip the preamble" in text


@pytest.mark.parametrize("mbti_type", server.MBTI_TYPES)
def test_every_persona_leaves_room_for_adjustments(tmp_path, monkeypatch, mbti_type):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path)
    assert len(server.build_instructions(mbti_type)) <= server.INSTRUCTIONS_LIMIT - 500


def test_persona_flag_and_env_var(monkeypatch):
    monkeypatch.delenv("MINDPERSONA_PERSONA", raising=False)
    assert server.parse_args([]).persona is None
    assert server.parse_args(["--persona", "INTJ"]).persona == "intj"

    monkeypatch.setenv("MINDPERSONA_PERSONA", "ENFP")
    assert server.parse_args([]).persona == "enfp"
    assert server.parse_args(["--persona", "intj"]).persona == "intj"


def test_unknown_persona_is_rejected(monkeypatch, capsys):
    monkeypatch.delenv("MINDPERSONA_PERSONA", raising=False)
    with pytest.raises(SystemExit):
        server.parse_args(["--persona", "abcd"])
    assert "choose from" in capsys.readouterr().err


def test_warns_when_claude_code_would_cut_the_instructions(capsys):
    server.warn_if_truncated("x" * 100, "intj")
    assert capsys.readouterr().err == ""

    server.warn_if_truncated("x" * 3000, "intj")
    assert "keeps only the first 2048" in capsys.readouterr().err
