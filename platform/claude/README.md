# MindPersona for Claude Code

## Install

Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (it downloads Python 3.10+ if needed).

```bash
# All projects
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona

# Only this project (writes .mcp.json, which you can commit for your team)
claude mcp add mindpersona -s project -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
```

Restart Claude Code, then run `claude mcp list` to check that `mindpersona` is connected.

Without uv: `pip install git+https://github.com/llzppzl/mindpersona`, then `claude mcp add mindpersona -s user -- mindpersona`.

## Use

- Just ask: `Use INTJ to review this plan`, or `Which persona fits this task?`. Claude calls the `load_persona` tool.
- Slash prompts: `/mcp__mindpersona__mbti-intj`, `/mcp__mindpersona__mbti-infp`, and so on for all 16 types. The `/` menu lists them as `/mindpersona:mbti-intj (MCP)`.
- Complain when the style is off (`too long`, `stop hedging`). Claude calls `update_mbti_memory`, and the rule is applied every time you load that type again.

Feedback is stored in `~/.mindpersona/memory/customized-<type>.md`. Set `MINDPERSONA_MEMORY_DIR` to change the location.

## Default persona

To use one persona in every session without asking, pass `--persona`:

```bash
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona --persona intj
```

Setting `MINDPERSONA_PERSONA=intj` in the server's environment does the same.

The server sends the persona and your saved adjustments as its MCP server instructions, which Claude Code loads at the start of every session. They are part of the system prompt, so they don't scroll out of a long conversation the way a loaded prompt can. A one-off `Use ENFP to brainstorm this` still switches for that task.

Claude Code keeps the first 2,048 characters of a server's instructions. The instructions for one persona are 1,000–1,250 characters, which leaves room for roughly 15 one-line adjustments. Past that, the server prints a warning to stderr when it starts; shorten your `customized-<type>.md` or set `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH`.

To change the default, remove the server (`claude mcp remove mindpersona -s user`) and add it again.

## Troubleshooting

If `claude mcp list` shows `✘ Failed to connect` for `mindpersona`, run the command after `--` yourself to see the error:

```bash
uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
```

When it works, it prints nothing and waits for input. Press Ctrl+C to quit.

| Error | Fix |
|-------|-----|
| `uvx: command not found` | Install [uv](https://docs.astral.sh/uv/getting-started/installation/). If Claude Code still can't find it, add the server with the full path: `claude mcp add mindpersona -s user -- "$(which uvx)" --from git+https://github.com/llzppzl/mindpersona mindpersona` |
| `Failed to build cryptography` on an Intel Mac | Fixed in the current version. Restart Claude Code; uvx fetches the latest commit each time it starts the server |
| `MindPersona needs mcp 1.x` or `'Server' object has no attribute 'list_prompts'` | mcp 2.x is installed. If you run from source: `pip install 'mcp>=1.3,<2'` |

## Upgrading from the old setup

If you added the server with `python /path/to/platform/claude/mcp_server.py`, that still works. To switch:

```bash
claude mcp remove mindpersona -s user
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
```

When run from a clone, feedback stays in the repo's `memory/` folder. When installed, it goes to `~/.mindpersona/memory/`. Copy your `customized-*.md` files there to keep them.

## Tools and prompts

| Name | Kind | What it does |
|------|------|--------------|
| server instructions | sent when Claude Code connects | Without `--persona`: when to call the tools. With `--persona`: the full persona, in every session |
| `mbti-<type>` | prompt | Persona text, your personal adjustments, feedback instructions |
| `load_persona` | tool | Same text as the prompt; its description includes the task index so Claude can recommend a type |
| `update_mbti_memory` | tool | Appends one-line feedback to `customized-<type>.md` |

---

中文说明见 [README-zh.md](../../README-zh.md#-快速开始)。
