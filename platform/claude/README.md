# MindPersona MCP Server

## Overview

The MindPersona MCP server lets you use the MBTI persona prompts in Claude Code.

## Quick setup (recommended)

With [uv](https://docs.astral.sh/uv/) installed, one command adds the server; no clone and no Python setup needed:

```bash
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
```

Restart Claude Code. uv downloads the server and a recent Python the first time. Saved adjustments are kept in `~/.mindpersona/memory` (set `MINDPERSONA_MEMORY_DIR` to use another folder).

## Setup from a clone

This needs Python 3.10 or newer (check with `python3 --version`; the python3 that comes with macOS is 3.9).

1. In the root of your clone, create a virtualenv and install the dependencies into it. Recent Pythons (from Homebrew, uv, Ubuntu or Debian) refuse `pip install` outside a virtualenv, and it keeps the server's packages apart from your other projects:
   ```bash
   python3 -m venv .venv

   # macOS/Linux
   .venv/bin/pip install -r platform/claude/requirements.txt

   # Windows
   .venv\Scripts\pip install -r platform\claude\requirements.txt
   ```

2. Add the MCP server to Claude Code, with the virtualenv's Python and the full path of mcp_server.py. On macOS/Linux, from the root of your clone:
   ```bash
   # For you, in every project
   claude mcp add mindpersona -s user -- "$(pwd)/.venv/bin/python" "$(pwd)/platform/claude/mcp_server.py"

   # Or only for the current project (saved in .mcp.json, so you can share it with your team)
   claude mcp add mindpersona -s project -- "$(pwd)/.venv/bin/python" "$(pwd)/platform/claude/mcp_server.py"
   ```

   On Windows, run `cd` in the root of your clone to see its full path, and use it in both places:
   ```bash
   claude mcp add mindpersona -s user -- C:\full\path\to\mindpersona\.venv\Scripts\python.exe C:\full\path\to\mindpersona\platform\claude\mcp_server.py
   ```

3. Restart Claude Code (or close the window and open it again). `claude mcp list` should show `mindpersona: ... ✔ Connected`.

## Troubleshooting

If `claude mcp list` shows `✘ Failed to connect` for mindpersona, run the command after `--` yourself (`python /absolute/path/to/mcp_server.py`) to see the error. When it works, it prints a short note that it is an MCP server, with the `claude mcp add` line for that command, and exits: then the command is fine, and the problem is in how it was added (check the paths in `claude mcp get mindpersona`). Anything else it prints is the error; the table below has the common ones.

| Error | Fix |
|-------|-----|
| `MindPersona needs mcp 1.x` or `'Server' object has no attribute 'list_prompts'` | mcp 2.x is installed and your copy of MindPersona is from before it supported mcp 2. Update it (`git pull`, or install it again) |
| `error: externally-managed-environment` from pip | You ran pip on your system Python, which Homebrew, uv, Ubuntu and Debian don't allow. Create the virtualenv from step 1 and use its pip and python |
| `Failed to build cryptography` on an Intel Mac | Run `.venv/bin/pip install -r platform/claude/requirements.txt` again. It installs a cryptography version that has Intel wheels |
| `MindPersona needs Python 3.10 or newer`, or `No matching distribution found for mcp` from pip | Your Python is too old. Install Python 3.10 or newer, delete `.venv`, create it again with the new Python (for example `python3.12 -m venv .venv`), install the dependencies and add the server again. Or use the quick setup with uv, which brings its own Python |
| `No module named mcp` | The python in `claude mcp add` is not the one you installed the dependencies with. Add the server again with the full path of the virtualenv's python (`.venv/bin/python`, or `.venv\Scripts\python.exe` on Windows) |

## Usage

In the Claude Code prompt box, type `/` and pick a persona prompt. Claude Code shows MCP prompts as `/mcp__<server>__<prompt>`:
- `/mcp__mindpersona__mbti-intj` - switch to the INTJ (Cold Chief of Staff) persona
- `/mcp__mindpersona__mbti-infp` - switch to the INFP (Trusted Partner) persona
- ... (the other 14 types work the same way)

Or just ask in plain words, and Claude loads the persona with the `load_persona` tool:
- "Use ESTJ to analyze this plan"
- "Switch to infp"
- "Which persona fits this task? Pick one for me"

Feedback about how to answer you ("too long, give me the conclusion first") is saved and loads with the persona from then on. To see or undo it, just ask:
- "What do you remember about how to answer me?" (Claude calls `list_adjustments`)
- "Forget number 2" (Claude calls `remove_adjustment`)

## Supported MBTI types

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP

## Default persona

To use one persona in every session without typing a prompt, add `--persona <type>` at the end of the server command:

```bash
# With the quick setup
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona --persona intj

# From a clone
claude mcp add mindpersona -s user -- python /absolute/path/to/mcp_server.py --persona intj
```

The persona, with your saved adjustments, is sent to Claude as the server's instructions when a session starts. You can still switch to another persona with a `/mcp__mindpersona__mbti-<type>` prompt or by asking for it. Instead of `--persona` you can set the `MINDPERSONA_PERSONA` environment variable (`claude mcp add ... -e MINDPERSONA_PERSONA=intj -- ...`). To stop using a default, remove the server and add it again without `--persona`. An unknown type stops the server with a message listing the valid types.
