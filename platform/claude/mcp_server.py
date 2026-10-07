"""
MindPersona MCP Server
Serves the MBTI persona prompts to Claude Code.

Usage:
1. pip install -r requirements.txt
2. Add the MCP server (see README.md)
3. Restart Claude Code
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from mcp.server import Server
from mcp.types import Prompt, GetPromptResult, Tool, CallToolResult, TextContent

# 服务配置
SERVER_NAME = "mindpersona"
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"
MEMORY_DIR = Path(__file__).parent.parent.parent / "memory"
PERSONAL_ADJUSTMENTS_HEADER = "## 你的私人调整"

TRIGGER_INSTRUCTION = """
---

## Saving feedback (important)

The current MBTI persona is: {mbti_type}

When the user asks for a lasting change in how you answer them (tone, length, format, level of detail, way of working), for example "too long", "stop apologizing", "use tables", "be gentler":

1. Summarize what they want in one sentence, in your own words (not a quote).
2. Call the `update_mbti_memory` tool with `mbti_type` = "{mbti_type}" and `feedback_summary` = that sentence.
3. When it succeeds, tell the user, in the language they write in, that you saved it for this persona and will follow it from now on.

Don't save:
- frustration with their own code, tools or day ("this build keeps failing"): help with the problem instead;
- a request that is only about the current answer or task ("shorter this time");
- something the persona above already says.

If you can't tell whether they want it remembered, ask. The tool creates customized-{mbti_type}.md if it doesn't exist yet.
"""

# The MCP server
server = Server(SERVER_NAME)

def get_mbti_type_from_filename(filename: str) -> Optional[str]:
    """The MBTI type in a skill file name, e.g. mbti-intj.md -> INTJ"""
    match = re.match(r"mbti-([a-z]{4})\.md$", filename, re.IGNORECASE)
    return match.group(1).upper() if match else None

def scan_skills() -> list[dict]:
    """List the MBTI prompts in skills/"""
    prompts = []
    for filepath in sorted(SKILLS_DIR.glob("mbti-*.md")):
        mbti_type = get_mbti_type_from_filename(filepath.name)
        if mbti_type:
            prompts.append({
                "type": mbti_type,
                "filepath": filepath,
                "description": f"MindPersona {mbti_type} persona"
            })
    return prompts

CUSTOMIZED_TEMPLATE = """# {mbti_type} 进化版 - 你的私人部分

<!-- 此文件与 skills/mbti-{mbti_type_lower}.md 合并 -->
<!-- 当用户给反馈时，AI 必须更新此文件 -->

{{HDR}}

- [{timestamp}] {feedback_summary}

<!-- 格式：(时间) 反馈内容 -->
"""

def get_customized_template(mbti_type: str, feedback_summary: str) -> str:
    """生成 customized-{type}.md 的初始内容"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = CUSTOMIZED_TEMPLATE.format(
        mbti_type=mbti_type.upper(),
        mbti_type_lower=mbti_type.lower(),
        timestamp=timestamp,
        feedback_summary=feedback_summary
    )
    return result.replace("{HDR}", PERSONAL_ADJUSTMENTS_HEADER)

def append_to_customized(mbti_type: str, feedback_summary: str) -> tuple[bool, str]:
    """
    向 customized-{type}.md 追加反馈
    Returns: (success: bool, message: str)
    """
    mbti_lower = mbti_type.lower()
    customized_file = MEMORY_DIR / f"customized-{mbti_lower}.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = f"- [{timestamp}] {feedback_summary}\n"

    try:
        if not customized_file.exists():
            # 文件不存在，创建并写入第一条反馈
            content = get_customized_template(mbti_type, feedback_summary)
            customized_file.write_text(content, encoding="utf-8")
        else:
            # 文件存在，追加到 PERSONAL_ADJUSTMENTS_HEADER 部分
            content = customized_file.read_text(encoding="utf-8")

            # 检查是否已有 PERSONAL_ADJUSTMENTS_HEADER 部分
            if PERSONAL_ADJUSTMENTS_HEADER in content:
                # 追加到最后一条反馈之后（而非 header 之后）
                # 匹配形如 "- [2026-04-15 12:34] 反馈内容" 的行
                last_entry_pattern = r"(-\s*\[[\d\s:-]+\][^\n]*\n)(?=\n|$)"
                match = re.search(last_entry_pattern, content)
                if match:
                    # 插入到最后一条反馈之后
                    insert_pos = match.end()
                    content = content[:insert_pos] + new_entry + content[insert_pos:]
                else:
                    # 没有匹配到反馈条目，追加到 header 之后
                    content = content.replace(
                        f"{PERSONAL_ADJUSTMENTS_HEADER}\n",
                        f"{PERSONAL_ADJUSTMENTS_HEADER}\n{new_entry}"
                    )
            else:
                # 没有 PERSONAL_ADJUSTMENTS_HEADER，追加到文件末尾
                content = content.rstrip() + f"\n\n{PERSONAL_ADJUSTMENTS_HEADER}\n\n{new_entry}"

            customized_file.write_text(content, encoding="utf-8")

        # 验证写入
        verified = customized_file.read_text(encoding="utf-8")
        if new_entry.strip() in verified:
            return True, "反馈已成功写入"
        else:
            return False, "写入验证失败"

    except Exception as e:
        return False, f"写入失败: {str(e)}"

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List the prompts (shown when the user types /mbti-intj)"""
    prompts = scan_skills()
    return [
        Prompt(
            name=f"mbti-{p['type'].lower()}",
            description=p["description"]
        )
        for p in prompts
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: Optional[dict] = None) -> GetPromptResult:
    """当用户调用 /mbti-intj 时，读取并返回对应 prompt"""
    # 提取 MBTI 类型
    mbti_type = name.replace("mbti-", "").upper()

    # 读取主 prompt
    skill_file = SKILLS_DIR / f"mbti-{mbti_type.lower()}.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_file}")

    content = skill_file.read_text(encoding="utf-8")

    # 尝试加载 customized 个性化（如果存在）
    customized_file = MEMORY_DIR / f"customized-{mbti_type.lower()}.md"
    if customized_file.exists():
        customized = customized_file.read_text(encoding="utf-8")
        # 提取 PERSONAL_ADJUSTMENTS_HEADER 部分（所有反馈条目）
        match = re.search(rf"{PERSONAL_ADJUSTMENTS_HEADER}\s*\n(.*?)(?=<!-- 格式|$)", customized, re.DOTALL)
        if match:
            personal_adjustments = match.group(1).strip()
            content += f"\n\n{PERSONAL_ADJUSTMENTS_HEADER}\n\n{personal_adjustments}"

    trigger = TRIGGER_INSTRUCTION.format(mbti_type=mbti_type.lower())
    return GetPromptResult(
        description=f"MindPersona {mbti_type} 性格适配",
        messages=[{"role": "user", "content": {"type": "text", "text": content + trigger}}]
    )

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List the tools"""
    return [
        Tool(
            name="update_mbti_memory",
            description=("Save a lasting preference about how the user wants to be answered (tone, length, format, "
                         "way of working) to customized-{mbti_type}.md, so it applies whenever this persona is "
                         "loaded. Use it only when the user wants future answers to change, not for frustration "
                         "with their own code or day, or for a request about the current answer only."),
            inputSchema={
                "type": "object",
                "properties": {
                    "mbti_type": {
                        "type": "string",
                        "description": "当前 MBTI 类型（如 intj, entj, infp）",
                        "enum": ["intj", "intp", "infj", "infp", "istj", "isfj", "istp", "isfp",
                                "entj", "entp", "enfj", "enfp", "estj", "esfj", "estp", "esfp"]
                    },
                    "feedback_summary": {
                        "type": "string",
                        "description": "What the user wants, summarized in one sentence"
                    }
                },
                "required": ["mbti_type", "feedback_summary"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具调用"""
    if name == "update_mbti_memory":
        mbti_type = arguments.get("mbti_type", "").lower()
        feedback_summary = arguments.get("feedback_summary", "")

        if not mbti_type or not feedback_summary:
            return [TextContent(type="text", text="错误: mbti_type 和 feedback_summary 都是必填参数")]

        success, message = append_to_customized(mbti_type, feedback_summary)
        if success:
            return [TextContent(type="text", text=f"✅ {message}\n\n文件路径: {MEMORY_DIR / f'customized-{mbti_type}.md'}")]
        else:
            return [TextContent(type="text", text=f"❌ {message}")]
    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]

if __name__ == "__main__":
    import mcp.server.stdio
    import asyncio

    async def main():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(main())
