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
from mcp.types import Prompt, GetPromptResult, PromptMessage, Tool, CallToolResult, TextContent


def require_mcp_1x(server_cls=Server):
    """Exit with a fix instead of an AttributeError when mcp 2.x is installed.

    mcp 2.0 registers handlers in the Server constructor; this file uses the 1.x decorators.
    """
    if not hasattr(server_cls, "list_prompts"):
        raise SystemExit(
            "MindPersona needs mcp 1.x, but a newer mcp is installed.\n"
            "Fix: pip install 'mcp>=1.22,<2'"
        )


require_mcp_1x()

# Server settings
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
        description=f"MindPersona {mbti_type} persona",
        messages=[PromptMessage(role="user", content=TextContent(type="text", text=content + trigger))]
    )

LOAD_PERSONA_TYPES = ["intj", "intp", "infj", "infp", "istj", "isfj", "istp", "isfp",
                      "entj", "entp", "enfj", "enfp", "estj", "esfj", "estp", "esfp"]

# What each persona is best at (the Task Index in readme.md), so the model can pick one for a task
PERSONA_GUIDE = """\
- ESTJ: quick results, schedules and daily tasks
- ENTJ: driving decisions forward, strategic breakdown of goals, pushing others
- ISTJ: following the rules exactly, acceptance criteria, structured summaries
- INTJ: comparing options and giving a clear verdict, critical review, setting priorities
- INTP: finding logical flaws, cause-and-effect analysis
- ISTP: tracing a problem from cause to effect, shortest hands-on path
- INFP: taking feelings first without pushing solutions, ideas tied to personal meaning
- ISFP: calm companionship in the moment
- ENFP: open-minded brainstorming
- ENTP: connecting ideas and arguing the opposite side
- ENFJ: growth and motivation, finding the meaning of a task
- INFJ: mission and long-term vision
- ISFJ: patient, practical support that listens first
- ESFJ: warm, team-minded help and recognition
- ESTP: fast action and breaking deadlocks
- ESFP: lively, upbeat energy"""


async def persona_text(mbti_type: str) -> str:
    """The persona prompt for a type, the same text /mbti-<type> gives: the skill, the user's saved
    adjustments and the feedback instruction."""
    result = await get_prompt(f"mbti-{mbti_type.lower()}")
    return result.messages[0].content.text

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
                        "description": "The current MBTI type (e.g. intj, entj, infp)",
                        "enum": MBTI_TYPES
                    },
                    "feedback_summary": {
                        "type": "string",
                        "description": "What the user wants, summarized in one sentence"
                    }
                },
                "required": ["mbti_type", "feedback_summary"]
            }
        ),
        Tool(
            name="load_persona",
            description=(
                "Load a MindPersona persona and answer as it says from then on. Call it when the user asks for "
                "a type in plain words (\"use ESTJ to analyze this plan\", \"switch to infp\"). When the user asks "
                "which persona fits a task, or to pick one, choose the best type from this list, call the tool "
                "with it and tell the user which one you picked and why:\n" + PERSONA_GUIDE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mbti_type": {
                        "type": "string",
                        "description": "The MBTI type, e.g. intj or estj",
                        "enum": LOAD_PERSONA_TYPES
                    }
                },
                "required": ["mbti_type"]
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
    elif name == "load_persona":
        mbti_type = str(arguments.get("mbti_type", "")).strip().lower()
        if mbti_type not in LOAD_PERSONA_TYPES:
            return [TextContent(type="text", text=f"❌ Unknown MBTI type: {mbti_type!r}. "
                                                  f"Valid types: {', '.join(LOAD_PERSONA_TYPES)}")]
        text = await persona_text(mbti_type)
        return [TextContent(type="text", text=f"Persona {mbti_type.upper()} loaded. Follow it from now on:\n\n{text}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


STARTUP_TYPES = ["intj", "intp", "infj", "infp", "istj", "isfj", "istp", "isfp",
                 "entj", "entp", "enfj", "enfp", "estj", "esfj", "estp", "esfp"]


def startup_persona(argv: list[str], environ: dict) -> Optional[str]:
    """The persona to start every session with: --persona TYPE, or the MINDPERSONA_PERSONA
    environment variable. None if neither is set."""
    import argparse
    parser = argparse.ArgumentParser(prog="mcp_server.py", description="MindPersona MCP server")
    parser.add_argument("--persona", default=environ.get("MINDPERSONA_PERSONA") or None,
                        help="MBTI type to use in every session, e.g. intj (default: $MINDPERSONA_PERSONA)")
    persona = parser.parse_args(argv).persona
    if persona is None:
        return None
    persona = persona.strip().lower()
    if persona not in STARTUP_TYPES:
        raise SystemExit(f"Unknown persona {persona!r} for --persona or MINDPERSONA_PERSONA. "
                         f"Use one of: {', '.join(STARTUP_TYPES)}")
    return persona


async def persona_instructions(persona: str) -> str:
    """Server instructions that make the persona the default. MCP clients such as Claude Code add
    them to the model's context in every session, so no slash prompt is needed."""
    result = await get_prompt(f"mbti-{persona}")
    return (f"The user chose the MindPersona {persona.upper()} persona as their default. Answer as it "
            f"says in every conversation unless they ask for another persona.\n\n"
            + result.messages[0].content.text)


if __name__ == "__main__":
    import mcp.server.stdio
    import asyncio
    import sys

    persona = startup_persona(sys.argv[1:], os.environ)

    async def main():
        if persona:
            server.instructions = await persona_instructions(persona)
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(main())
