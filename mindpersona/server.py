"""
MindPersona MCP Server
为 Claude Code 提供 MBTI 性格适配 prompt

安装（Claude Code）：
    claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
详见 platform/claude/README.md
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from mcp.server import Server
from mcp.types import Prompt, GetPromptResult, PromptMessage, Tool, CallToolResult, TextContent


def require_mcp_1x(server_cls=Server):
    """Exit with a fix instead of an AttributeError when mcp 2.x is installed.

    mcp 2.0 registers handlers in the Server constructor; this file uses the 1.x decorators.
    """
    if not hasattr(server_cls, "list_prompts"):
        raise SystemExit(
            "MindPersona needs mcp 1.x, but a newer mcp is installed.\n"
            "Fix: pip install 'mcp>=1.3,<2'"
        )


require_mcp_1x()

# 服务配置
SERVER_NAME = "mindpersona"
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_DIR = PACKAGE_DIR.parent


def find_skills_dir() -> Path:
    """安装后 skills 打包在 mindpersona/skills；从源码运行时在仓库根目录"""
    packaged = PACKAGE_DIR / "skills"
    return packaged if packaged.is_dir() else REPO_DIR / "skills"


def find_memory_dir() -> Path:
    """个人反馈保存位置

    优先级：MINDPERSONA_MEMORY_DIR 环境变量 > 源码仓库的 memory/ > ~/.mindpersona/memory
    安装后不能写在包目录里（uvx 的环境是临时的，升级也会丢）。
    """
    if os.environ.get("MINDPERSONA_MEMORY_DIR"):
        return Path(os.environ["MINDPERSONA_MEMORY_DIR"]).expanduser()
    if (REPO_DIR / "skills").is_dir() and (REPO_DIR / "memory").is_dir():
        return REPO_DIR / "memory"
    return Path.home() / ".mindpersona" / "memory"


SKILLS_DIR = find_skills_dir()
MEMORY_DIR = find_memory_dir()
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

MBTI_TYPES = ["intj", "intp", "infj", "infp", "istj", "isfj", "istp", "isfp",
              "entj", "entp", "enfj", "enfp", "estj", "esfj", "estp", "esfp"]


def parse_skill(filepath: Path) -> dict:
    """从 skill 文件读出标题和"适用任务"，用于 prompt 描述和任务索引

    标题行形如 "# ESTJ - 总经理"；适用任务是一张 | 任务 | 使用场景 | 表，
    没有主位的类型写的是一行括号说明。
    """
    lines = filepath.read_text(encoding="utf-8").splitlines()
    title = lines[0].lstrip("# ").split(" - ", 1)[-1].strip() if lines else ""
    tasks, note, in_section = [], "", False
    for line in lines:
        if line.startswith("## "):
            in_section = line.strip() == "## 适用任务"
            continue
        if not in_section or not line.strip():
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] not in ("任务", "") and not set(cells[0]) <= set("-: "):
                tasks.append(f"{cells[0]}: {cells[1]}")
        elif not note:
            note = line.strip().strip("（）()")
    return {"title": title, "tasks": tasks, "note": note}


def scan_skills() -> list[dict]:
    """扫描 skills/ 目录，返回所有 MBTI prompt 列表"""
    prompts = []
    for filepath in sorted(SKILLS_DIR.glob("mbti-*.md")):
        mbti_type = get_mbti_type_from_filename(filepath.name)
        if mbti_type:
            info = parse_skill(filepath)
            summary = "；".join(info["tasks"]) or info["note"]
            prompts.append({
                "type": mbti_type,
                "filepath": filepath,
                "title": info["title"],
                "summary": summary,
                "description": f"MindPersona {mbti_type} {info['title']}：{summary}".rstrip("：")
            })
    return prompts


def build_task_index() -> str:
    """所有人格的任务索引，放进 load_persona 的描述里，模型据此推荐类型"""
    return "\n".join(f"- {p['type']} {p['title']}：{p['summary']}" for p in scan_skills())


def build_persona_prompt(mbti_type: str) -> str:
    """skill 原文 + 用户的私人调整 + 反馈触发说明"""
    mbti_lower = mbti_type.lower()
    skill_file = SKILLS_DIR / f"mbti-{mbti_lower}.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_file}")

    content = skill_file.read_text(encoding="utf-8")

    # 尝试加载 customized 个性化（如果存在）
    customized_file = MEMORY_DIR / f"customized-{mbti_lower}.md"
    if customized_file.exists():
        customized = customized_file.read_text(encoding="utf-8")
        # 提取 PERSONAL_ADJUSTMENTS_HEADER 部分（所有反馈条目）
        match = re.search(rf"{PERSONAL_ADJUSTMENTS_HEADER}\s*\n(.*?)(?=<!-- 格式|$)", customized, re.DOTALL)
        if match:
            personal_adjustments = match.group(1).strip()
            content += f"\n\n{PERSONAL_ADJUSTMENTS_HEADER}\n\n{personal_adjustments}"

    return content + TRIGGER_INSTRUCTION.format(mbti_type=mbti_lower)

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
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
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
    """当用户调用 /mbti-intj 时，读取并返回对应 prompt

    Claude Code 中显示为 /mcp__mindpersona__mbti-intj
    """
    mbti_type = name.replace("mbti-", "").upper()
    return GetPromptResult(
        description=f"MindPersona {mbti_type} 性格适配",
        messages=[PromptMessage(role="user", content=TextContent(type="text", text=build_persona_prompt(mbti_type)))]
    )

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="load_persona",
            description=(
                "加载一个 MindPersona 人格，之后按返回的说明回答。"
                "用户说\"用 ESTJ 帮我…\"/\"Use INTJ to…\"时调用；"
                "用户问\"这个任务用哪个人格\"或要求自动选择时，按下面的任务索引选出最合适的类型再调用，并告诉用户选了哪个、为什么。\n"
                "任务索引：\n" + build_task_index()
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mbti_type": {
                        "type": "string",
                        "description": "MBTI 类型（如 intj, estj）",
                        "enum": MBTI_TYPES
                    }
                },
                "required": ["mbti_type"]
            }
        ),
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
    """执行工具调用"""
    if name == "load_persona":
        mbti_type = arguments.get("mbti_type", "").lower()
        if mbti_type not in MBTI_TYPES:
            return [TextContent(type="text", text=f"错误: 未知类型 {mbti_type!r}，可选: {', '.join(MBTI_TYPES)}")]
        return [TextContent(type="text", text=build_persona_prompt(mbti_type))]
    elif name == "update_mbti_memory":
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

def main():
    """命令行入口（pyproject.toml 中的 mindpersona 命令）"""
    import asyncio
    import mcp.server.stdio

    async def run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
