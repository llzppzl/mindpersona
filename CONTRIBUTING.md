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

1. Edit or create `skills/mbti-{type}.md`, following the format of the existing files (suitable tasks, interaction layer, architecture layer, memory layer)
2. Run `python scripts/sync_platforms.py` to update the copies in `platform/semantic-kernel/` and `platform/saas/IMPORT_GUIDE.md`
3. Commit them together. CI runs `python scripts/sync_platforms.py --check` and fails if the copies are out of sync

Don't edit the platform copies directly: the next sync overwrites them. A `<!-- comment -->` on a line of its own in a skill is for maintainers and is left out of the copies.

## Code style

- Python 3.10+
- Follow PEP 8
- Every new feature needs tests
