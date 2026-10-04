# Contributing to MindPersona

## Setup

```bash
git clone https://github.com/llzppzl/mindpersona.git
cd mindpersona
pip install -e .          # Python 3.10+
python -m pytest tests -v
```

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

## Code style

- Python 3.10+
- PEP 8
- New features need tests
