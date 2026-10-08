# MindPersona for the direct API

Use a persona as the system prompt of any chat API (Claude, OpenAI, a local model, ...).

[`prompts.yaml`](./prompts.yaml) lists the 16 personas: `id`, a short `description`, `traits`, and the `file` with the prompt (relative to this folder). The prompt is the skill file itself.

## Load a persona

```python
import re
from pathlib import Path

import yaml  # pip install pyyaml

API_DIR = Path("platform/api")  # this folder, from the repo root


def persona_prompt(persona_id: str) -> str:
    index = yaml.safe_load((API_DIR / "prompts.yaml").read_text(encoding="utf-8"))
    entry = next(p for p in index["prompts"] if p["id"] == persona_id)
    text = (API_DIR / entry["file"]).read_text(encoding="utf-8")
    # Lines like <!-- ... --> are notes for maintainers, not part of the prompt
    return re.sub(r"^[ \t]*<!--.*?-->[ \t]*\n", "", text, flags=re.MULTILINE).strip()


system_prompt = persona_prompt("mbti-intj")
# Send system_prompt as the system prompt of your chat request.
```

## Personal adjustments

The Claude Code MCP server saves a user's feedback to `memory/customized-<type>.md` and loads it with the persona. With the direct API, keep your own list of adjustments and append it to the system prompt, for example:

```python
adjustments = ["Lead with the conclusion.", "Use tables for comparisons."]
system_prompt += "\n\n## Personal adjustments\n\n" + "\n".join(f"- {a}" for a in adjustments)
```

## Choosing a persona

`description` and `traits` in `prompts.yaml`, and the Task Index in the [README](../../readme.md#task-index), say what each persona is good for.
