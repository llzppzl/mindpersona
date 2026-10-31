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


def test_each_letter_line_names_the_letter_in_the_type():
    # INFP said "E/I: E", so an introvert persona was told to answer like an extravert
    for t in TYPES:
        text = (SKILLS / f"mbti-{t}.md").read_text(encoding="utf-8")
        for axis, letter in (("E/I", t[0]), ("S/N", t[1]), ("T/F", t[2]), ("J/P", t[3])):
            line = re.search(rf"^- {axis}: (\w)\b", text, re.MULTILINE)
            assert line, f"mbti-{t}.md has no '- {axis}:' line"
            assert line.group(1) == letter.upper(), f"mbti-{t}.md says {axis}: {line.group(1)}"


def test_enfp_does_not_close_every_idea_with_a_plan():
    # ENFP said "Don't wrap up too early" and avoids "wrapping up too early", but its last rule was
    # "Hard rule: every idea comes with a plan for carrying it out", so the model got both
    text = (SKILLS / "mbti-enfp.md").read_text(encoding="utf-8")
    architecture = re.search(r"## Architecture layer\n(.*?)\n## ", text, re.DOTALL).group(1)
    assert "every idea" not in architecture
    assert "Don't wrap up too early" in architecture
    assert re.search(r"^- Once the ideas have run their course", architecture, re.MULTILINE)


def task_index():
    """{task: set of types} from the Task Index table in readme.md"""
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    table = re.search(r"## Task Index\n(.*?)\n---", readme, re.DOTALL).group(1)
    index = {}
    for task, types in re.findall(r"^\| ([^|]+?) \| [^|]+ \| ([A-Z /]+) \|$", table, re.MULTILINE):
        index[task.lower()] = {t.strip().lower() for t in types.split("/")}
    return index


def best_for():
    """{task: set of types} from the "Best for" table of every skill"""
    found = {}
    for t in TYPES:
        text = (SKILLS / f"mbti-{t}.md").read_text(encoding="utf-8")
        section = re.search(r"## Best for\n(.*?)\n## ", text, re.DOTALL).group(1)
        for task in re.findall(r"^\| ([^|]+?) \| ", section, re.MULTILINE)[1:]:  # [0] is the header
            found.setdefault(task.lower(), set()).add(t)
    return found


def test_task_index_is_read():
    index = task_index()
    assert len(index) == 9
    assert index["option analysis"] == {"intj", "intp"}


def test_best_for_tables_match_the_task_index():
    # A persona that claims a task the README recommends someone else for confuses the choice
    # (load_persona and the README both use the Task Index)
    assert best_for() == task_index()


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
