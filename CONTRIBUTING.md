# Contributing to MindPersona

## Setup

```bash
git clone https://github.com/llzppzl/mindpersona.git
cd mindpersona
pip install -e .          # Python 3.10+
python -m pytest tests -v
```

`tests/test_stdio_e2e.py` starts the server as a subprocess and talks to it with the MCP client, like Claude Code does. To run it against an installed command instead of this checkout:

```bash
MINDPERSONA_SERVER_CMD="uvx --from . mindpersona" python -m pytest tests/test_stdio_e2e.py
```

CI (`.github/workflows/test.yml`) runs the tests on Python 3.10–3.14, against the oldest allowed mcp (1.3.0), and through `uvx` on Linux and macOS.

`mcp` is pinned below 2: mcp 2.0 replaced the decorator API that `mindpersona/server.py` uses. Porting the server is welcome; lift the pin in `pyproject.toml` and `platform/claude/requirements.txt` in the same PR.

Try your changes in Claude Code without installing:

```bash
claude mcp add mindpersona-dev -s user -- python /absolute/path/to/mindpersona/platform/claude/mcp_server.py
```

## Changing or adding a persona

Each persona is one file: `skills/mbti-<type>.md`. Keep this structure:

- First line: `# ESTJ - 总经理` (type, then nickname). The nickname is shown in prompt descriptions.
- A `## 适用任务` section with a `| 任务 | 使用场景 |` table. The MCP server builds the task index from these rows; it is what Claude uses to recommend a type. If a type has no main task, write one line in brackets instead.
- `## 交互层`, `## 架构层`, `## 记忆层`, as in the existing files.

Run the tests afterwards; `tests/test_load_persona.py` checks that every skill produces an index entry.

Keep skills short. With `--persona`, the whole skill plus the user's adjustments is sent as server instructions, and Claude Code keeps only the first 2,048 characters. `tests/test_default_persona.py` fails if a persona leaves less than 500 characters for adjustments.

## Code style

- Python 3.10+
- PEP 8
- New features need tests
