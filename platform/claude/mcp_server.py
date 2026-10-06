"""
MindPersona MCP Server
为 Claude Code 提供 MBTI 性格适配 prompt

使用方法：
1. pip install -r requirements.txt
2. 配置 MCP Server（见 README.md）
3. 重启 Claude Code
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

## 🔄 反馈触发机制（重要）

当前用户的 MBTI 类型为：{mbti_type}

**当用户表达任何形式的不满、抱怨、负面情绪、或要求改变交流方式时，你必须立即：**

1. 向用户道歉并简短安抚
2. 总结用户不满的核心诉求（一句话）
3. **立即调用 `update_mbti_memory` 工具**，将：
   - `mbti_type` 设置为当前人格类型（如 intj）
   - `feedback_summary` 设置为你总结的核心诉求
4. 工具调用成功后，明确告知用户："已更新到 {mbti_type} 的私人档案，后续会严格遵守"

**注意：**
- 用户语气冷淡、表示不满、要求改变 → 都是触发条件
- feedback_summary 必须是总结后的一句话，不是原话复述
- 即使 customized-{mbti_type}.md 不存在，工具会自动创建
"""

# 初始化 Server
server = Server(SERVER_NAME)

def get_mbti_type_from_filename(filename: str) -> Optional[str]:
    """从文件名提取 MBTI 类型，如 mbti-intj.md -> intj"""
    match = re.match(r"mbti-([a-z]{4})\.md$", filename, re.IGNORECASE)
    return match.group(1).upper() if match else None

def scan_skills() -> list[dict]:
    """扫描 skills/ 目录，返回所有 MBTI prompt 列表"""
    prompts = []
    for filepath in sorted(SKILLS_DIR.glob("mbti-*.md")):
        mbti_type = get_mbti_type_from_filename(filepath.name)
        if mbti_type:
            prompts.append({
                "type": mbti_type,
                "filepath": filepath,
                "description": f"MindPersona {mbti_type} 性格适配"
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

MBTI_TYPES = ["intj", "intp", "infj", "infp", "istj", "isfj", "istp", "isfp",
              "entj", "entp", "enfj", "enfp", "estj", "esfj", "estp", "esfp"]
MAX_SUMMARY_CHARS = 300
# Prefix of a saved entry: "- [2026-04-15 12:34] ", or a hand-written "- （2026-04-04）"
ENTRY_PREFIX = re.compile(r"^-\s*(\[[^\]]*\]|（[^）]*）|\([^)]*\))?\s*")


def normalize_mbti_type(mbti_type: str) -> Optional[str]:
    """The lowercase MBTI type, or None if it is not one of the 16 (this also blocks paths like ../)"""
    t = (mbti_type or "").strip().lower()
    return t if t in MBTI_TYPES else None


def clean_summary(feedback_summary: str) -> str:
    """Keep it on one line: one line is one adjustment. A line break would start a new heading or
    paragraph in the file, which is then loaded as part of the persona prompt."""
    return " ".join((feedback_summary or "").split())


def _add_entry(content: str, new_entry: str, summary: str) -> Optional[str]:
    """Insert new_entry after the last entry under PERSONAL_ADJUSTMENTS_HEADER.
    Returns None if this adjustment is already saved."""
    lines = content.splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.strip() == PERSONAL_ADJUSTMENTS_HEADER), None)
    if header is None:
        # No PERSONAL_ADJUSTMENTS_HEADER yet: add it at the end of the file
        return content.rstrip() + f"\n\n{PERSONAL_ADJUSTMENTS_HEADER}\n\n{new_entry}"

    # The section ends at the next heading
    section_end = next((i for i in range(header + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    entries = [i for i in range(header + 1, section_end) if lines[i].lstrip().startswith("-")]
    if any(ENTRY_PREFIX.sub("", lines[i].strip()) == summary for i in entries):
        return None

    if entries:
        insert_at = entries[-1] + 1
    else:
        insert_at = header + 1
        if insert_at < len(lines) and not lines[insert_at].strip():
            insert_at += 1  # keep the blank line under the heading
    if insert_at > 0 and not lines[insert_at - 1].endswith("\n"):
        lines[insert_at - 1] += "\n"
    lines.insert(insert_at, new_entry)
    return "".join(lines)


def append_to_customized(mbti_type: str, feedback_summary: str) -> tuple[bool, str]:
    """
    Append feedback to customized-{type}.md
    Returns: (success: bool, message: str)
    """
    mbti_lower = normalize_mbti_type(mbti_type)
    if not mbti_lower:
        return False, f"Unknown MBTI type: {mbti_type}. Valid types: {', '.join(MBTI_TYPES)}"

    summary = clean_summary(feedback_summary)
    if not summary:
        return False, "feedback_summary is empty"
    if len(summary) > MAX_SUMMARY_CHARS:
        return False, f"feedback_summary is too long ({len(summary)} characters). Summarize it in one sentence of at most {MAX_SUMMARY_CHARS} characters"

    customized_file = MEMORY_DIR / f"customized-{mbti_lower}.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = f"- [{timestamp}] {summary}\n"

    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        if not customized_file.exists():
            # No file yet: create it with the first entry
            content = get_customized_template(mbti_lower, summary)
        else:
            content = _add_entry(customized_file.read_text(encoding="utf-8"), new_entry, summary)
            if content is None:
                return True, "This adjustment was already saved, so it was not added again"
        customized_file.write_text(content, encoding="utf-8")

        # Read it back to check the write
        verified = customized_file.read_text(encoding="utf-8")
        if summary in verified:
            return True, "Feedback saved"
        else:
            return False, "The feedback was written but could not be read back"

    except Exception as e:
        return False, f"Could not save the feedback: {str(e)}"

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """列出所有可用 prompt（用户输入 /mbti-intj 时显示）"""
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
    mbti_lower = normalize_mbti_type(name.removeprefix("mbti-"))
    if not mbti_lower:
        raise ValueError(f"Unknown prompt: {name}. Available: {', '.join('mbti-' + t for t in MBTI_TYPES)}")
    mbti_type = mbti_lower.upper()

    # 读取主 prompt
    skill_file = SKILLS_DIR / f"mbti-{mbti_type.lower()}.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill file not found: skills/mbti-{mbti_lower}.md")

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
    """列出所有可用工具"""
    return [
        Tool(
            name="update_mbti_memory",
            description="当用户表达不满、抱怨或负面情绪时，将反馈追加到 customized-{mbti_type}.md。触发条件：用户语气不满、抱怨、要求改变交流方式。",
            inputSchema={
                "type": "object",
                "properties": {
                    "mbti_type": {
                        "type": "string",
                        "description": "当前 MBTI 类型（如 intj, entj, infp）",
                        "enum": MBTI_TYPES
                    },
                    "feedback_summary": {
                        "type": "string",
                        "description": "用户反馈的核心诉求摘要（已总结为一句话）"
                    }
                },
                "required": ["mbti_type", "feedback_summary"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Run a tool call"""
    if name == "update_mbti_memory":
        mbti_type = arguments.get("mbti_type", "")
        feedback_summary = arguments.get("feedback_summary", "")

        if not mbti_type or not feedback_summary:
            return [TextContent(type="text", text="Error: mbti_type and feedback_summary are both required")]

        success, message = append_to_customized(mbti_type, feedback_summary)
        if success:
            path = MEMORY_DIR / f"customized-{normalize_mbti_type(mbti_type)}.md"
            return [TextContent(type="text", text=f"✅ {message}\n\nFile: {path}")]
        else:
            return [TextContent(type="text", text=f"❌ {message}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

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
