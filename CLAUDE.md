# MindPersona

This file is for working on MindPersona itself. Personas don't come from here: the MCP server in `mindpersona/server.py` serves them in any project (install: `platform/claude/README.md`). Don't adopt a persona in this repo unless the user loads one.

## Layout

| Path | What it is |
|------|------------|
| `skills/mbti-*.md` | The 16 personas. `parse_skill` reads the title line (`# INTJ - 冷酷幕僚长`) and the `## 适用任务` table to build the task index in the `load_persona` description, so keep both formats. |
| `mindpersona/server.py` | The MCP server: `mbti-<type>` prompts; the `load_persona`, `update_mbti_memory`, `list_adjustments` and `remove_adjustment` tools; server instructions, which carry the whole persona when started with `--persona`. |
| `memory/customized-*.md` | Saved adjustments when the server runs from this checkout (git-ignored). Installed copies use `~/.mindpersona/memory`; `MINDPERSONA_MEMORY_DIR` overrides both. |
| `platform/claude/` | Claude Code guide. `mcp_server.py` only keeps old `python .../mcp_server.py` configs working. |
| `tests/` | pytest. `test_stdio_e2e.py` starts the real server over stdio. |

## Adjustments

The server owns `customized-<type>.md`: one adjustment per line, `- [YYYY-MM-DD HH:MM] rule`, under `## 你的私人调整`. The numbers that `list_adjustments` and `remove_adjustment` use are line positions, so change the files through the tools. If you edit one by hand, keep one line per adjustment.

## Limits

- Claude Code keeps the first 2,048 characters of server instructions. With `--persona`, they hold the skill, its adjustments and `TRIGGER_INSTRUCTION`, so keep skills and that text short. `tests/test_default_persona.py` keeps every persona at 1,548 characters or less, which leaves room for adjustments.
- `mcp` is pinned below 2 because `server.py` uses the 1.x decorator API. Lift the pin in `pyproject.toml` and `platform/claude/requirements.txt` together.

## Checks

```bash
pip install -e . pytest
python -m pytest -q tests
```

User-facing changes go in `readme.md` and `README-zh.md` (keep both in step) and, for Claude Code details, `platform/claude/README.md`.
