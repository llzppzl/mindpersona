"""
MindPersona MCP Server
为 Claude Code 提供 MBTI 性格适配 prompt

安装（Claude Code）：
    claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
详见 platform/claude/README.md
"""

import os
import re
import sys
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

# Appended to every persona. Only requests about how to answer are saved: an adjustment loads in
# every later session, so a saved complaint about the user's bug would follow them for good.
TRIGGER_INSTRUCTION = """
---

## Feedback memory ({mbti_upper})

When the user asks you to change how you answer (tone, length, format, way of working), call update_mbti_memory with mbti_type "{mbti_type}" and their request as one short rule, then follow it. Don't save frustration with their own code, tools or day, or a request for the current task only. list_adjustments and remove_adjustment show and delete saved rules.
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
            content += f"\n\n{PERSONAL_ADJUSTMENTS_HEADER}\n\n{personal_adjustments}\n"

    return content + TRIGGER_INSTRUCTION.format(mbti_type=mbti_lower, mbti_upper=mbti_lower.upper())


# Server instructions: Claude Code loads them into every session, even when tool search
# defers the tool descriptions, and keeps the first 2,048 characters.
INSTRUCTIONS_LIMIT = 2048

USAGE_INSTRUCTIONS = """MindPersona adapts your replies to one of 16 MBTI personas ({types}).
- When the user names a type ("Use INTJ to review this", "用 ESTJ 帮我排计划"), call load_persona with that type and follow the text it returns.
- When the user asks which persona fits a task, pick a type from the task index in the load_persona description, say which one and why, then call load_persona.
- When the user asks what you remember about how they like answers, or to forget some of it, use list_adjustments and remove_adjustment.
- Answer in the language the user writes in."""

# Set by main() from --persona
DEFAULT_PERSONA: Optional[str] = None

DEFAULT_PERSONA_HEADER = """MindPersona: the user chose {mbti_type} as their default persona. Follow the persona below in every reply. If they ask for another type, call load_persona and follow that one instead. Answer in the language the user writes in.

"""


def build_instructions(default_persona: Optional[str] = None) -> str:
    """Without a default: when to call the tools. With one: the whole persona, applied to every reply."""
    if not default_persona:
        return USAGE_INSTRUCTIONS.format(types=", ".join(MBTI_TYPES))
    header = DEFAULT_PERSONA_HEADER.format(mbti_type=default_persona.upper())
    return header + build_persona_prompt(default_persona)

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

def customized_path(mbti_type: str) -> Path:
    return MEMORY_DIR / f"customized-{mbti_type.lower()}.md"


def read_lines(mbti_type: str) -> list[str]:
    path = customized_path(mbti_type)
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def adjustment_lines(lines: list[str]) -> list[int]:
    """Indexes of the "- " lines under PERSONAL_ADJUSTMENTS_HEADER.

    One line is one adjustment, and its position is the number list_adjustments shows,
    so entries written by hand in another format count too.
    """
    stripped = [line.strip() for line in lines]
    if PERSONAL_ADJUSTMENTS_HEADER not in stripped:
        return []
    found = []
    for i in range(stripped.index(PERSONAL_ADJUSTMENTS_HEADER) + 1, len(lines)):
        if stripped[i].startswith("<!-- 格式"):
            break
        if stripped[i].startswith("- "):
            found.append(i)
    return found


def read_adjustments(mbti_type: str) -> list[str]:
    """Saved adjustments, oldest first, without the "- " bullet."""
    lines = read_lines(mbti_type)
    return [lines[i].strip()[2:] for i in adjustment_lines(lines)]


def one_line(text: str) -> str:
    """A rule must stay on one line, or it would be read back as several adjustments."""
    return " ".join(str(text or "").split())


def without_timestamp(entry: str) -> str:
    return re.sub(r"^\[[^\]]*\]\s*", "", entry)


def save_adjustment(mbti_type: str, rule: str) -> tuple[int, bool]:
    """Add one adjustment. Returns its number, and False if the same rule was already saved."""
    rule = one_line(rule)
    if not rule:
        raise ValueError("feedback_summary is empty")
    lines = read_lines(mbti_type)
    entries = adjustment_lines(lines)
    for number, i in enumerate(entries, 1):
        if without_timestamp(lines[i].strip()[2:]).casefold() == rule.casefold():
            return number, False

    entry = f"- [{datetime.now():%Y-%m-%d %H:%M}] {rule}"
    stripped = [line.strip() for line in lines]
    if not lines:
        lines = get_customized_template(mbti_type, rule).splitlines()
    elif entries:
        lines.insert(entries[-1] + 1, entry)
    elif PERSONAL_ADJUSTMENTS_HEADER in stripped:
        header = stripped.index(PERSONAL_ADJUSTMENTS_HEADER)
        lines[header + 1:header + 1] = ["", entry]
    else:
        lines += ["", PERSONAL_ADJUSTMENTS_HEADER, "", entry]
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    customized_path(mbti_type).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(entries) + 1, True


def remove_adjustment(mbti_type: str, number: int) -> str:
    """Delete adjustment `number` (counting from 1, as list_adjustments shows) and return it."""
    lines = read_lines(mbti_type)
    entries = adjustment_lines(lines)
    if not 1 <= number <= len(entries):
        raise ValueError(
            f"{mbti_type.upper()} has {len(entries)} saved adjustments, so there is no #{number}. "
            "Call list_adjustments to see them."
        )
    removed = lines.pop(entries[number - 1]).strip()[2:]
    customized_path(mbti_type).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return removed


def describe_adjustments(mbti_type: str) -> str:
    entries = read_adjustments(mbti_type)
    if not entries:
        return f"No adjustments saved for {mbti_type.upper()}."
    numbered = "\n".join(f"{number}. {entry}" for number, entry in enumerate(entries, 1))
    return f"{mbti_type.upper()} adjustments ({customized_path(mbti_type)}):\n{numbered}"


def limit_note(mbti_type: str) -> str:
    """For the --persona default: say when its adjustments no longer fit in what Claude Code keeps."""
    if mbti_type != DEFAULT_PERSONA:
        return ""
    size = len(build_instructions(mbti_type))
    if size <= INSTRUCTIONS_LIMIT:
        return ""
    return (
        f"\nNote: with --persona {mbti_type}, the instructions are now {size} characters and Claude Code keeps "
        f"the first {INSTRUCTIONS_LIMIT}, so the newest adjustments won't load in new sessions. "
        "Suggest removing ones the user no longer needs."
    )

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
            description=(
                "Save how the user wants you to answer (tone, length, format, way of working) as an adjustment "
                "to a persona. Adjustments load with the persona in every later session. Call it when the user "
                "asks you to change how you answer. Don't call it for frustration with their own code, tools or "
                "day, or for a request meant only for the current task."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mbti_type": {
                        "type": "string",
                        "description": "The persona in use",
                        "enum": MBTI_TYPES
                    },
                    "feedback_summary": {
                        "type": "string",
                        "description": "The request as one short rule, in the user's language, e.g. \"Lead with the conclusion\""
                    }
                },
                "required": ["mbti_type", "feedback_summary"]
            }
        ),
        Tool(
            name="list_adjustments",
            description=(
                "Show the adjustments saved for a persona, numbered, with when each was saved. "
                "Use it when the user asks what you remember about how they like answers."
            ),
            inputSchema={
                "type": "object",
                "properties": {"mbti_type": {"type": "string", "enum": MBTI_TYPES}},
                "required": ["mbti_type"]
            }
        ),
        Tool(
            name="remove_adjustment",
            description=(
                "Delete one saved adjustment by the number that list_adjustments or update_mbti_memory gave it. "
                "Use it when the user says an adjustment is wrong or asks you to undo one. "
                "Later adjustments move up one number, so remove the highest number first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mbti_type": {"type": "string", "enum": MBTI_TYPES},
                    "number": {"type": "integer", "minimum": 1}
                },
                "required": ["mbti_type", "number"]
            }
        )
    ]


def mbti_type_arg(arguments: dict) -> str:
    mbti_type = str(arguments.get("mbti_type") or "").lower()
    if mbti_type not in MBTI_TYPES:
        raise ValueError(f"Unknown MBTI type {mbti_type!r}. Choose from: {', '.join(MBTI_TYPES)}")
    return mbti_type


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Run a tool. Errors are raised; the MCP SDK sends them to the client with isError set."""
    if name == "load_persona":
        text = build_persona_prompt(mbti_type_arg(arguments))
    elif name == "update_mbti_memory":
        mbti_type = mbti_type_arg(arguments)
        number, is_new = save_adjustment(mbti_type, arguments.get("feedback_summary"))
        label = f"{mbti_type.upper()} adjustment #{number}"
        if is_new:
            text = (
                f"Saved {label}: {one_line(arguments.get('feedback_summary'))}\n"
                f"File: {customized_path(mbti_type)}\n"
                f"Tell the user what you saved, and that they can ask you to undo it (remove_adjustment, number {number})."
            )
        else:
            text = f"This is already saved as {label}. Nothing changed."
        text += limit_note(mbti_type)
    elif name == "list_adjustments":
        mbti_type = mbti_type_arg(arguments)
        text = describe_adjustments(mbti_type) + limit_note(mbti_type)
    elif name == "remove_adjustment":
        mbti_type = mbti_type_arg(arguments)
        try:
            number = int(arguments.get("number"))
        except (TypeError, ValueError):
            raise ValueError("number must be an adjustment number from list_adjustments, e.g. 2") from None
        removed = remove_adjustment(mbti_type, number)
        text = f"Removed {mbti_type.upper()} adjustment #{number}: {removed}\n\n{describe_adjustments(mbti_type)}"
    else:
        raise ValueError(f"Unknown tool: {name}")
    return [TextContent(type="text", text=text)]

def parse_args(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        prog="mindpersona",
        description="MindPersona MCP server. Claude Code starts it over stdio; see platform/claude/README.md.",
    )
    parser.add_argument(
        "--persona", metavar="TYPE", type=str.lower,
        default=(os.environ.get("MINDPERSONA_PERSONA") or "").lower() or None,
        help="apply this persona to every reply, e.g. intj (env: MINDPERSONA_PERSONA)",
    )
    args = parser.parse_args(argv)
    if args.persona and args.persona not in MBTI_TYPES:
        parser.error(f"unknown persona {args.persona!r}; choose from: {', '.join(MBTI_TYPES)}")
    return args


def warn_if_truncated(instructions: str, persona: Optional[str]) -> None:
    """Saved adjustments grow over time; say so before Claude Code silently cuts the end off."""
    if len(instructions) > INSTRUCTIONS_LIMIT:
        print(
            f"mindpersona: the instructions are {len(instructions)} characters, but Claude Code keeps only "
            f"the first {INSTRUCTIONS_LIMIT}. Shorten {MEMORY_DIR / f'customized-{persona}.md'} "
            "or set CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH.",
            file=sys.stderr,
        )


def main(argv=None):
    """命令行入口（pyproject.toml 中的 mindpersona 命令）"""
    import asyncio
    import mcp.server.stdio

    global DEFAULT_PERSONA
    args = parse_args(argv)
    DEFAULT_PERSONA = args.persona
    server.instructions = build_instructions(args.persona)
    warn_if_truncated(server.instructions, args.persona)

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
