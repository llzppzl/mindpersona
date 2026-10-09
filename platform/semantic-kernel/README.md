# MindPersona for Semantic Kernel

Each folder here is one persona as a Semantic Kernel prompt function: `skprompt.txt` (the prompt) and `config.json` (description and execution settings). The folders are generated from [`skills/`](../../skills); don't edit them by hand (see [CONTRIBUTING.md](../../CONTRIBUTING.md)).

## Load the personas

Semantic Kernel plugin names may only contain letters, digits and `_`, so `kernel.add_plugin(parent_directory="platform", plugin_name="semantic-kernel")` fails on this folder's name. Load the persona folders into a plugin named `mindpersona` instead (Python, `pip install semantic-kernel`, run from the repo root):

```python
from pathlib import Path

from semantic_kernel import Kernel
from semantic_kernel.functions import KernelFunctionFromPrompt, KernelPlugin

PERSONAS = Path("platform/semantic-kernel")

kernel = Kernel()
kernel.add_plugin(KernelPlugin(
    name="mindpersona",
    functions=[
        KernelFunctionFromPrompt.from_directory(path=str(folder), plugin_name="mindpersona")
        for folder in sorted(PERSONAS.iterdir())
        if (folder / "skprompt.txt").is_file()
    ],
))
```

This gives 16 functions, `mindpersona.intj` to `mindpersona.esfp`.

## Use a persona as the system message

The prompts have no input variables: a persona describes how to answer, so it belongs in the system message, not in the user's turn.

```python
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments


async def persona_chat(persona: str) -> ChatHistory:
    function = kernel.get_function("mindpersona", persona)
    system_message = await function.prompt_template.render(kernel, KernelArguments())
    return ChatHistory(system_message=system_message)

# chat = await persona_chat("intj")
# chat.add_user_message("Compare these two plans for me: ...")
# Then send `chat` with your chat completion service.
```

The prompts are written in Chinese. To make sure the model answers in another language, add a line such as `Always answer in English.` to the system message.
