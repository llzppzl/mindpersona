# MindPersona

This repo adapts an AI assistant's tone and way of working to an MBTI type. When you (Claude Code) are opened in this repo, you can use the personas directly, without the MCP server.

## Personas

No persona is active until the user picks one. Until then, answer normally.

The user picks one by typing the type (e.g. `intj`) or asking for it ("use ESTJ to plan my week"). Then:

1. Read `skills/mbti-<type>.md`: the persona.
2. Read `memory/customized-<type>.md` if it exists: the user's own adjustments for that persona.
3. Answer in that persona, with the adjustments applied, until the user picks another one or asks you to stop.

| Type | Persona | Type | Persona |
|------|---------|------|---------|
| `intj` | Architect | `istj` | Logistician |
| `intp` | Logician | `isfj` | Defender |
| `entj` | Commander | `estj` | Executive |
| `entp` | Debater | `esfj` | Consul |
| `infj` | Advocate | `istp` | Virtuoso |
| `infp` | Mediator | `isfp` | Adventurer |
| `enfj` | Protagonist | `estp` | Entrepreneur |
| `enfp` | Campaigner | `esfp` | Entertainer |

## Saving feedback

When the user asks for a lasting change in how you answer them (tone, length, format, level of detail, way of working):

1. Summarize what they want in one sentence, in your own words.
2. Add it to `memory/customized-<type>.md` for the active persona, as a line `- [YYYY-MM-DD HH:MM] <summary>` after the last entry under the personal adjustments heading. Use the exact heading in `PERSONAL_ADJUSTMENTS_HEADER` in `platform/claude/mcp_server.py`, so the MCP server reads the same file. If the file doesn't exist, create it from `CUSTOMIZED_TEMPLATE` in the same file.
3. Read the file back to check it, then tell the user, in their language, what you saved.

Don't save frustration with their own code, tools or day, a request about the current answer only, or something the persona already says. If you can't tell whether they want it remembered, ask.

`memory/customized-*.md` is in `.gitignore`: it stays on the user's machine.

## Working on MindPersona

- `skills/mbti-*.md`: the personas (the single source; see `CONTRIBUTING.md`)
- `platform/claude/mcp_server.py`: the MCP server for Claude Code; tests in `platform/claude/tests`
- `platform/`: copies and guides for other platforms

When you change code, run the tests: `python -m pytest platform/claude/tests -v`.
