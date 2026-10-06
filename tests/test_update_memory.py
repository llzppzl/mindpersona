"""Saved adjustments: update_mbti_memory, list_adjustments and remove_adjustment"""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mindpersona import server


@pytest.fixture(autouse=True)
def memory_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path)
    return tmp_path


def call(name, arguments):
    return asyncio.run(server.call_tool(name, arguments))[0].text


def rules(mbti_type="intj"):
    return [server.without_timestamp(entry) for entry in server.read_adjustments(mbti_type)]


def test_first_adjustment_creates_the_file(memory_dir):
    assert server.save_adjustment("intj", "用户觉得回复太啰嗦") == (1, True)
    assert (memory_dir / "customized-intj.md").exists()


def test_adjustments_are_numbered_in_the_order_they_were_saved():
    server.save_adjustment("intj", "第一次反馈")
    assert server.save_adjustment("intj", "第二次反馈") == (2, True)
    assert rules() == ["第一次反馈", "第二次反馈"]


def test_template_contains_correct_format():
    template = server.get_customized_template("INTJ", "测试反馈")
    assert "# INTJ 进化版" in template
    assert "## 你的私人调整" in template
    assert "测试反馈" in template
    assert "[20" in template  # timestamp


def test_same_rule_is_not_saved_twice():
    server.save_adjustment("intj", "Lead with the conclusion")
    assert server.save_adjustment("intj", "lead with the  conclusion") == (1, False)
    assert rules() == ["Lead with the conclusion"]


def test_multi_line_summary_is_saved_as_one_adjustment():
    server.save_adjustment("intj", "No tables.\nUse bullet points.")
    assert rules() == ["No tables. Use bullet points."]


def test_save_tool_gives_the_number_to_undo_with():
    text = call("update_mbti_memory", {"mbti_type": "intj", "feedback_summary": "No emoji"})
    assert text.startswith("Saved INTJ adjustment #1: No emoji")
    assert "remove_adjustment, number 1" in text


def test_list_tool_numbers_the_adjustments():
    assert call("list_adjustments", {"mbti_type": "intj"}) == "No adjustments saved for INTJ."

    server.save_adjustment("intj", "No emoji")
    server.save_adjustment("intj", "Lead with the conclusion")
    lines = call("list_adjustments", {"mbti_type": "intj"}).splitlines()

    assert lines[0].startswith("INTJ adjustments (")
    assert lines[1].startswith("1. [") and lines[1].endswith("] No emoji")
    assert lines[2].startswith("2. [") and lines[2].endswith("] Lead with the conclusion")


def test_remove_deletes_one_adjustment_and_renumbers():
    for rule in ["Rule A", "Rule B", "Rule C"]:
        server.save_adjustment("intj", rule)

    text = call("remove_adjustment", {"mbti_type": "intj", "number": 2})

    assert text.startswith("Removed INTJ adjustment #2: [")
    assert "2. [" in text and text.endswith("] Rule C")  # the list that is left
    assert rules() == ["Rule A", "Rule C"]
    assert "Rule B" not in server.build_persona_prompt("intj")


def test_remove_rejects_numbers_that_do_not_exist():
    server.save_adjustment("intj", "Rule A")

    with pytest.raises(ValueError, match="no #5"):
        call("remove_adjustment", {"mbti_type": "intj", "number": 5})
    with pytest.raises(ValueError, match="number must be"):
        call("remove_adjustment", {"mbti_type": "intj", "number": "two"})
    assert rules() == ["Rule A"]


def test_removing_the_last_one_then_saving_again():
    server.save_adjustment("intj", "Rule A")
    server.remove_adjustment("intj", 1)
    assert rules() == []

    assert server.save_adjustment("intj", "Rule B") == (1, True)
    assert "Rule B" in server.build_persona_prompt("intj")


def test_entries_written_by_hand_are_listed_and_removable(memory_dir):
    (memory_dir / "customized-intj.md").write_text(
        "# INTJ\n\n## 你的私人调整\n\n- （2026-04-04）你希望更委婉一点\n", encoding="utf-8"
    )

    assert server.save_adjustment("intj", "No emoji") == (2, True)
    assert rules() == ["（2026-04-04）你希望更委婉一点", "No emoji"]

    server.remove_adjustment("intj", 1)
    assert rules() == ["No emoji"]


def test_file_without_the_header_keeps_its_text(memory_dir):
    path = memory_dir / "customized-intj.md"
    path.write_text("# My notes\n", encoding="utf-8")

    assert server.save_adjustment("intj", "No emoji") == (1, True)
    assert path.read_text(encoding="utf-8").startswith("# My notes\n")
    assert "No emoji" in server.build_persona_prompt("intj")


def test_unknown_type_is_an_error_and_writes_nothing(memory_dir):
    with pytest.raises(ValueError, match="Unknown MBTI type"):
        call("update_mbti_memory", {"mbti_type": "../x", "feedback_summary": "hi"})
    with pytest.raises(ValueError, match="feedback_summary is empty"):
        call("update_mbti_memory", {"mbti_type": "intj", "feedback_summary": " "})
    assert list(memory_dir.iterdir()) == []


def test_persona_tells_the_model_what_to_save():
    text = server.build_persona_prompt("intj")
    assert 'call update_mbti_memory with mbti_type "intj"' in text
    assert "Don't save frustration with their own code" in text


def test_note_when_the_default_persona_outgrows_the_instructions(monkeypatch):
    monkeypatch.setattr(server, "DEFAULT_PERSONA", "intj")
    assert "Note:" not in call("update_mbti_memory", {"mbti_type": "intj", "feedback_summary": "Rule 0"})

    for i in range(1, 40):
        server.save_adjustment("intj", f"Rule number {i} about how to answer")

    assert "Claude Code keeps the first 2048" in call("update_mbti_memory", {"mbti_type": "intj", "feedback_summary": "One more"})
    assert "Claude Code keeps the first 2048" in call("list_adjustments", {"mbti_type": "intj"})
    assert "Note:" not in call("list_adjustments", {"mbti_type": "enfp"})  # not the default
