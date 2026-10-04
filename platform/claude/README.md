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
- Slash prompts: `/mcp__mindpersona__mbti-intj`, `/mcp__mindpersona__mbti-infp`, and so on for all 16 types.
- Complain when the style is off (`too long`, `stop hedging`). Claude calls `update_mbti_memory`, and the rule is applied every time you load that type again.

Feedback is stored in `~/.mindpersona/memory/customized-<type>.md`. Set `MINDPERSONA_MEMORY_DIR` to change the location.

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
| `mbti-<type>` | prompt | Persona text, your personal adjustments, feedback instructions |
| `load_persona` | tool | Same text as the prompt; its description includes the task index so Claude can recommend a type |
| `update_mbti_memory` | tool | Appends one-line feedback to `customized-<type>.md` |

---

中文说明见 [README-zh.md](../../README-zh.md#-快速开始)。
