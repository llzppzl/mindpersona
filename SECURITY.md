# Security and privacy

MindPersona is a set of persona prompts and a small local MCP server. This page says what it stores, what it sends, and how to report a problem.

## What is stored, and where

- **Saved adjustments**: when you give feedback about how a persona should answer, the model calls the `update_mbti_memory` tool, which appends a one-line summary to `memory/customized-<type>.md` in your copy of the repository. (The one-command `uvx` install keeps them in `~/.mindpersona/memory` instead, or in `MINDPERSONA_MEMORY_DIR` if you set it.)
- `memory/customized-*.md` is in `.gitignore`, so your adjustments are not committed or pushed with the repository.
- Nothing else is stored. The server keeps no logs and no conversation history.

## What is sent, and to whom

- The MCP server makes **no network requests**. It talks only to the app that started it (for example Claude Code), over stdin and stdout.
- When you load a persona, the app adds the persona text **and your saved adjustments** to the conversation, so they are sent to that app's model provider like the rest of your messages.

## Things to know

- **Saved adjustments become part of the prompt** every time you load that persona. Anything saved there steers the model in every later session. Check them from time to time: ask "What do you remember about how to answer me?" (the `list_adjustments` tool) and "Forget number 2" (`remove_adjustment`), or open `memory/customized-*.md` and delete lines you don't want; they are plain text.
- Text that the model reads (a web page, a file, a document) could try to make it save an "adjustment", or remove one. The tool descriptions and the persona's instructions tell the model to do that only when you ask in the conversation, but a model can still be tricked. Only keep lines you recognize, and if one you saved is gone, add it again.
- On the other platforms (Semantic Kernel, Coze, Dify, the direct API) there is no server: you copy the persona text yourself, and nothing is saved by MindPersona.

## Reporting a vulnerability

Please don't post exploit details in a public issue. Use GitHub's private reporting (the repository's **Security** tab → **Report a vulnerability**) if it's available; otherwise open an issue that only says you have found a security problem, and the maintainer will contact you.
