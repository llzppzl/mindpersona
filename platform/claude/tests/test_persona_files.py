"""Every persona file is present and complete, and the API index points at them.

Contributors add or edit personas by hand (see CONTRIBUTING.md); these checks catch a missing
type, a misnamed file, a missing section or a stale entry in platform/api/prompts.yaml.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILLS = REPO / "skills"
TYPES = ["intj", "intp", "infj", "infp", "istj", "isfj", "istp", "isfp",
         "entj", "entp", "enfj", "enfp", "estj", "esfj", "estp", "esfp"]


def sections(path):
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("## ")]


def test_one_skill_file_per_type():
    assert sorted(p.name for p in SKILLS.glob("*.md")) == sorted(f"mbti-{t}.md" for t in TYPES)


def test_each_skill_starts_with_its_type():
    for t in TYPES:
        first = (SKILLS / f"mbti-{t}.md").read_text(encoding="utf-8").splitlines()[0]
        assert re.match(rf"# {t.upper()} - \S", first), f"mbti-{t}.md starts with {first!r}"


def test_every_skill_has_the_same_sections():
    expected = sections(SKILLS / "mbti-intj.md")
    assert len(expected) >= 4
    for t in TYPES:
        assert sections(SKILLS / f"mbti-{t}.md") == expected, f"mbti-{t}.md has different sections"


def test_api_index_lists_every_persona_with_an_existing_file():
    index = (REPO / "platform/api/prompts.yaml").read_text(encoding="utf-8")
    ids = re.findall(r'^\s*- id: "mbti-(\w+)"', index, re.MULTILINE)
    files = re.findall(r'^\s*file: "(.+)"', index, re.MULTILINE)
    assert sorted(ids) == sorted(TYPES)
    assert len(files) == len(ids)
    for persona, file in zip(ids, files):
        path = (REPO / "platform/api" / file).resolve()
        assert path == (SKILLS / f"mbti-{persona}.md").resolve(), f"{persona} points at {file}"
        assert path.is_file()
