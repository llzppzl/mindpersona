# Contributing to MindPersona

## Development setup

```bash
# Clone the project
git clone https://github.com/llzppzl/mindpersona.git
cd mindpersona

# Install dependencies
pip install -r platform/claude/requirements.txt pytest

# Run the tests
python -m pytest platform/claude/tests -v
```

## Changing or adding a persona

`skills/mbti-{type}.md` is the single source. The copies for other platforms are generated from it:

1. Edit or create `skills/mbti-{type}.md`, with the same sections as the existing files: `## Best for`, `## What frustrates this type about AI`, `## Interaction layer`, `## Architecture layer` and `## Memory layer (typical defaults)`
2. If you change a `## Best for` table, change the [Task Index](./readme.md#task-index) in `readme.md` to match, and the type's line in `PERSONA_GUIDE` in `platform/claude/mcp_server.py` (the `load_persona` tool picks personas with it). The tests fail if a table and the Task Index disagree
3. Run `python scripts/sync_platforms.py` to update the copies in `platform/semantic-kernel/` and `platform/saas/IMPORT_GUIDE.md`
4. Commit them together. CI runs `python scripts/sync_platforms.py --check` and fails if the copies are out of sync

Don't edit the platform copies directly: the next sync overwrites them. A `<!-- comment -->` on a line of its own in a skill is for maintainers: it is left out of the copies and of the text the MCP server sends.

## Code style

- Python 3.10+
- Follow PEP 8
- Every new feature needs tests
