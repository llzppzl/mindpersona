"""The docs keep up with the server's tools."""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_server import list_tools

REPO = Path(__file__).resolve().parents[3]


def test_security_page_names_every_tool_that_changes_saved_adjustments():
    # SECURITY.md said to edit the files by hand after list_adjustments and remove_adjustment existed
    security = (REPO / "SECURITY.md").read_text(encoding="utf-8")
    tools = {t.name for t in asyncio.run(list_tools())}
    for name in ("update_mbti_memory", "list_adjustments", "remove_adjustment"):
        assert name in tools
        assert f"`{name}`" in security


def test_security_page_says_where_every_install_saves_adjustments():
    # It said only the uvx install saves to ~/.mindpersona/memory, and told everyone to open
    # memory/customized-*.md to delete lines. Every installed mindpersona command (uvx or pip) uses
    # the home folder, so those users were sent to a folder that has none of their adjustments
    security = (REPO / "SECURITY.md").read_text(encoding="utf-8")
    stored = security.split("## What is stored", 1)[1].split("\n## ", 1)[0]
    cli = (REPO / "mindpersona" / "cli.py").read_text(encoding="utf-8")
    assert 'DEFAULT_MEMORY_DIR = Path.home() / ".mindpersona" / "memory"' in cli
    assert "`~/.mindpersona/memory`" in stored
    assert "`pip install`" in stored and "`uvx`" in stored
    assert "`MINDPERSONA_MEMORY_DIR`" in stored
    assert "open `memory/customized-*.md`" not in security
    from mcp_server import call_tool
    assert "File: {path}" in Path(call_tool.__code__.co_filename).read_text(encoding="utf-8")


def test_contributing_lists_the_sections_every_skill_has():
    # It listed "suitable tasks, interaction layer, ..." while the files use other headings
    contributing = (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8")
    skill = (REPO / "skills" / "mbti-intj.md").read_text(encoding="utf-8")
    headings = [line for line in skill.splitlines() if line.startswith("## ")]
    assert len(headings) == 5
    for heading in headings:
        assert f"`{heading}`" in contributing


def persona_names():
    """{"intj": "Cold Chief of Staff", ...} from the first line of each skill"""
    names = {}
    for skill in sorted((REPO / "skills").glob("mbti-*.md")):
        title = skill.read_text(encoding="utf-8").splitlines()[0]
        names[skill.stem.removeprefix("mbti-")] = title.split(" - ", 1)[1].strip()
    return names


def test_claude_md_uses_the_persona_names_of_the_skills():
    # It still called INTJ "Architect" and INFP "Mediator" after the skills were renamed
    claude_md = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    table = dict(re.findall(r"\| `([a-z]{4})` \| ([^|]+?) (?=\|)", claude_md))
    assert table == persona_names()


def test_claude_md_says_how_to_use_the_persona_like_the_server():
    # It only said "Answer in that persona". A skill describes a user of the type, so in-repo mode
    # gave Claude none of what the server's "Using this persona" part says: which layers to follow,
    # to stay clear of the "Avoid" list, and that a saved adjustment wins over the persona
    from mcp_server import ADJUSTMENTS_FIRST, USAGE_INSTRUCTION
    claude_md = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    steps = claude_md.split("## Personas", 1)[1].split("\n## ", 1)[0]
    usage = " ".join(USAGE_INSTRUCTION.split())
    for part in ("follow its interaction layer (format and tone) and its architecture layer (way of working)",
                 'stay clear of what frustrates this type and of everything under "Avoid"',
                 "aim for its north star"):
        assert part in usage, part
        assert part in " ".join(steps.split()), part
    assert "disagrees with the persona, follow the adjustment" in ADJUSTMENTS_FIRST
    assert "disagrees with the persona, follow the adjustment" in steps
    assert "written for a user of that type" in steps
    assert "notes for maintainers" in steps


def test_claude_setup_guide_uses_the_persona_names_of_the_skills():
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    names = persona_names()
    examples = re.findall(r"switch to the ([A-Z]{4}) \(([^)]+)\) persona", guide)
    assert examples
    for mbti_type, name in examples:
        assert name == names[mbti_type.lower()]


def test_every_pain_point_in_the_readme_names_a_persona():
    # "Idea Translator" and "Agile Coach" are no persona's name, so a reader could not tell which
    # type to load for them
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    needs = [line for line in readme.splitlines() if line.strip().startswith("What you need:")]
    assert len(needs) == 4
    names = persona_names()
    for line in needs:
        match = re.search(r"the \*\*([A-Z]{4})\*\* persona", line)
        assert match, line
        mbti_type = match.group(1).lower()
        assert mbti_type in names
        # The quoted style is either the persona's own name, or the name follows in brackets
        style = re.search(r'\*\*"([^"]+)"\*\*', line).group(1)
        assert style == names[mbti_type] or f"({names[mbti_type]})" in line


def test_troubleshooting_says_what_the_server_prints_in_a_terminal():
    # It said the server "prints nothing and waits for input" after the server was changed to print
    # a note and exit, so a user checking a working command thought it was broken
    from mcp_server import terminal_notice
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    troubleshooting = guide.split("## Troubleshooting", 1)[1].split("\n## ", 1)[0]
    assert "waits for input" not in troubleshooting
    assert "prints a short note that it is an MCP server" in troubleshooting
    assert terminal_notice({}).startswith("MindPersona is an MCP server")
    assert "claude mcp add" in terminal_notice({})


def test_readme_says_to_paste_a_copy_that_tells_the_model_to_use_the_persona():
    # It said to paste a skills/ file into any chat app. A skill only describes a user of the type;
    # the "Using this persona" part that tells the model to answer that way is added by the server
    # and the platform copies, so a pasted skill could leave the answers unchanged
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    section = readme.split("### Any chat app", 1)[1].split("\n### ", 1)[0]
    assert "skprompt.txt" in section
    assert "Open a file in [`skills/`]" not in section
    assert "Using this persona" in section
    skprompt = (REPO / "platform" / "semantic-kernel" / "intj" / "skprompt.txt").read_text(encoding="utf-8")
    assert "## Using this persona" in skprompt and "<!--" not in skprompt
    skill = (REPO / "skills" / "mbti-intj.md").read_text(encoding="utf-8")
    assert "## Using this persona" not in skill


def test_readme_solution_names_only_what_mindpersona_does():
    # The Solution table said the layers are built with "Workflow + Multi-Agent" and "Memory + RAG".
    # MindPersona has neither: each layer is text in the persona prompt, and the memory is a file
    # of saved adjustments added to it, so readers expected features that do not exist
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    solution = readme.split("## Solution", 1)[1].split("### Interaction Layer", 1)[0]
    table = [line for line in solution.splitlines() if line.startswith("| ")]
    assert len(table) == 4
    for line in table:
        assert "Multi-Agent" not in line and "RAG" not in line, line
    assert "memory/customized-<type>.md" in solution
    code = "\n".join(p.read_text(encoding="utf-8") for p in [REPO / "platform" / "claude" / "mcp_server.py",
                                                            REPO / "mindpersona" / "cli.py"])
    for word in ("embedding", "vector", "retriev"):
        assert word not in code.lower()


def test_clone_setup_installs_into_a_virtualenv():
    # The guides ran pip on the system python3. Pythons from Homebrew, uv, Ubuntu and Debian refuse
    # that with "externally-managed-environment" (PEP 668), so the clone setup stopped at its first
    # pip command
    sections = [
        (REPO / "readme.md", "### Claude Code (MCP server)", "\n### "),
        (REPO / "platform" / "claude" / "README.md", "## Setup from a clone", "\n## "),
        (REPO / "CONTRIBUTING.md", "## Development setup", "\n## "),
    ]
    for path, start, end in sections:
        section = path.read_text(encoding="utf-8").split(start, 1)[1].split(end, 1)[0]
        assert "python3 -m venv .venv" in section, path
        assert ".venv/bin/pip install -r platform/claude/requirements.txt" in section, path
        bare_pip = [line for line in section.splitlines()
                    if re.match(r"\s*(python3? -m )?pip3? install", line)]
        assert not bare_pip, (path, bare_pip)
        if "claude mcp add" in section:
            adds = [line for line in section.splitlines() if line.strip().startswith("claude mcp add")]
            assert all(".venv" in line for line in adds), (path, adds)
            assert "which python3" not in section, path
    assert ".venv/" in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_every_clone_command_runs_the_server_with_the_virtualenv_python():
    # The "Default persona" example ran `python /absolute/path/to/mcp_server.py --persona intj`.
    # The dependencies are in .venv, so that python had no mcp ("No module named mcp"), and macOS
    # has no `python` command at all, so the server failed to connect
    for path in (REPO / "readme.md", REPO / "platform" / "claude" / "README.md"):
        adds = [line for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith("claude mcp add") and "mcp_server.py" in line]
        assert adds, path
        unix = [line for line in adds if "\\" not in line]
        assert unix, path
        for line in unix:
            assert '"$(pwd)/.venv/bin/python" "$(pwd)/platform/claude/mcp_server.py"' in line, (path, line)
        for line in adds:
            assert ".venv" in line, (path, line)


def test_claude_setup_guide_names_every_tool_the_user_can_ask_for():
    guide = (REPO / "platform" / "claude" / "README.md").read_text(encoding="utf-8")
    for name in ("load_persona", "list_adjustments", "remove_adjustment"):
        assert f"`{name}`" in guide
