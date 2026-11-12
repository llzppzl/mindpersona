"""The persona copies for the other platforms say how to use the persona, like the MCP server.

They had only the skill, which describes a user of the type and what frustrates them about AI, with
no instruction to answer that way: pasted into Coze, Dify, Semantic Kernel or a system prompt, the
model was left to guess what the description was for.
"""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import mcp_server
from mcp_server import MBTI_TYPES

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
import sync_platforms

SK_DIR = REPO / "platform" / "semantic-kernel"


def usage(mbti_type):
    return mcp_server.USAGE_INSTRUCTION.format(mbti_type=mbti_type.upper()).strip()


def test_same_usage_text_as_the_mcp_server():
    assert sync_platforms.USAGE_INSTRUCTION == mcp_server.USAGE_INSTRUCTION


@pytest.mark.parametrize("mbti_type", MBTI_TYPES)
def test_semantic_kernel_prompts_say_how_to_use_the_persona(mbti_type):
    skprompt = (SK_DIR / mbti_type / "skprompt.txt").read_text(encoding="utf-8")
    template = json.loads((SK_DIR / mbti_type / "config.json").read_text(encoding="utf-8"))["prompts"][0]["template"]
    for text in (skprompt, template):
        assert text.rstrip().endswith(usage(mbti_type))
        assert text.index("- North star:") < text.index("## Using this persona")


@pytest.mark.parametrize("mbti_type", MBTI_TYPES)
def test_saas_guide_prompts_say_how_to_use_the_persona(mbti_type):
    guide = (REPO / "platform" / "saas" / "IMPORT_GUIDE.md").read_text(encoding="utf-8")
    block = re.search(rf"^## {mbti_type.upper()} - [^\n]*\n\s*### CLEAN Prompt\s*\n\s*```\n(.*?)\n```",
                      guide, re.MULTILINE | re.DOTALL).group(1)
    assert block.endswith(usage(mbti_type))


def test_saas_guide_says_what_each_persona_is_good_for_like_the_server():
    # Its "Good for" column was written apart from the personas: ISFP was for "Art, exploration" and
    # INTJ for "Strategic planning, long-term thinking", while the skills and the Task Index make ISFP
    # calm companionship and INTJ comparing options. A Coze or Dify user picked by that column
    guide = (REPO / "platform" / "saas" / "IMPORT_GUIDE.md").read_text(encoding="utf-8")
    table = dict(re.findall(r"^\| ([EI][SN][TF][JP]) \| [^|]+ \| ([^|]+?) \|$", guide, re.MULTILINE))
    expected = {t: g[0].upper() + g[1:]
                for t, g in re.findall(r"^- ([A-Z]{4}): (.+)$", mcp_server.PERSONA_GUIDE, re.MULTILINE)}
    assert len(expected) == 16
    assert table == expected


def test_api_readme_adds_the_same_usage_text():
    readme = (REPO / "platform" / "api" / "README.md").read_text(encoding="utf-8")
    code = readme[readme.index("```python"):]
    assert mcp_server.USAGE_INSTRUCTION.strip() in code
    assert "USAGE.format(" in code
