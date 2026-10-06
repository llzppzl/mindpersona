"""load_persona 工具：在任何项目里用一句话切换人格"""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mindpersona import server


def call(name, arguments):
    return asyncio.run(server.call_tool(name, arguments))[0].text


def tools():
    return {t.name: t for t in asyncio.run(server.list_tools())}


def test_parse_skill_reads_title_and_tasks():
    info = server.parse_skill(server.SKILLS_DIR / "mbti-estj.md")
    assert info["title"] == "总经理"
    assert info["tasks"] == ["执行输出: 快速交付（按流程执行）", "目标拆解: 操作拆解（排期+每日任务）"]


def test_parse_skill_without_task_table_uses_note():
    info = server.parse_skill(server.SKILLS_DIR / "mbti-esfj.md")
    assert info["tasks"] == []
    assert "关怀服务" in info["note"]


def test_task_index_covers_all_16_types():
    index = server.build_task_index().splitlines()
    assert len(index) == 16
    assert all("：" in line and not line.endswith("：") for line in index)


def test_load_persona_tool_is_listed_with_task_index():
    tool = tools()["load_persona"]
    assert "ESTJ 总经理" in tool.description
    assert tool.inputSchema["properties"]["mbti_type"]["enum"] == server.MBTI_TYPES


def test_load_persona_returns_skill_and_feedback_instructions(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path)
    text = call("load_persona", {"mbti_type": "ESTJ"})
    assert text.startswith("# ESTJ - 总经理")
    assert "update_mbti_memory" in text


def test_load_persona_includes_personal_adjustments(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path)
    server.save_adjustment("estj", "不要用表格")

    assert "不要用表格" in call("load_persona", {"mbti_type": "estj"})


def test_load_persona_rejects_unknown_type():
    with pytest.raises(ValueError, match="Choose from: intj"):
        call("load_persona", {"mbti_type": "abcd"})


def test_prompt_and_tool_return_the_same_text(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path)
    prompt = asyncio.run(server.get_prompt("mbti-intj"))
    assert prompt.messages[0].content.text == call("load_persona", {"mbti_type": "intj"})


def test_prompt_descriptions_show_what_each_type_is_for():
    prompts = {p.name: p.description for p in asyncio.run(server.list_prompts())}
    assert "选项分析" in prompts["mbti-intj"]


def test_mcp_2_gets_a_clear_error_instead_of_a_crash():
    class Mcp2Server:  # mcp 2.x Server: no decorator methods
        pass

    with pytest.raises(SystemExit, match="mcp>=1.3,<2"):
        server.require_mcp_1x(Mcp2Server)
