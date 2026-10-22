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

1. Install the dependencies:
   ```bash
   cd platform/claude
   pip install -r requirements.txt
   ```

2. Add the MCP server to Claude Code:

   **Find the full path of your Python** (the one you ran `pip install` with):
   ```bash
   # Windows
   where python

   # macOS/Linux
   which python3
   ```

   **Find the full path of mcp_server.py:** in a terminal inside `platform/claude`, run `pwd` (macOS/Linux) or `cd` (Windows) and add `/mcp_server.py` to what it prints.

   **Run one of these commands, with your two paths:**
   ```bash
   # For you, in every project
   claude mcp add mindpersona -s user -- /full/path/to/python3 /full/path/to/mcp_server.py

   # Or only for the current project (saved in .mcp.json, so you can share it with your team)
   claude mcp add mindpersona -s project -- /full/path/to/python3 /full/path/to/mcp_server.py
   ```

3. Restart Claude Code (or close the window and open it again). `claude mcp list` should show `mindpersona: ... ✔ Connected`.

## Troubleshooting

If `claude mcp list` shows `✘ Failed to connect` for mindpersona, run the command after `--` yourself (`python /absolute/path/to/mcp_server.py`) to see the error. When it works, it prints nothing and waits for input. Press Ctrl+C to quit.

| Error | Fix |
|-------|-----|
| `MindPersona needs mcp 1.x` or `'Server' object has no attribute 'list_prompts'` | mcp 2.x is installed. Run `pip install 'mcp>=1.22,<2'` (or `pip install -r requirements.txt` again) |
| `Failed to build cryptography` on an Intel Mac | Run `pip install -r requirements.txt` again. It installs a cryptography version that has Intel wheels |
| `No module named mcp` | The python in `claude mcp add` is not the one you installed the dependencies with. Add the server again with the full path from `which python3` |

## Usage

In the Claude Code prompt box, type `/` and pick a persona prompt. Claude Code shows MCP prompts as `/mcp__<server>__<prompt>`:
- `/mcp__mindpersona__mbti-intj` - switch to the INTJ (Architect) persona
- `/mcp__mindpersona__mbti-infp` - switch to the INFP (Mediator) persona
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
