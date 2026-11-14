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


# Words that describe each letter. A letter line must use one: ESFJ described J as "responsible,
# cares about others" (an F trait) and ISFJ described I as "needs recognition"
LETTER_WORDS = {
    "E": ("sociable", "outgoing", "expressive", "take charge", "takes charge"),
    "I": ("quiet", "reserved", "independent", "room", "space", "deep", "check-in"),
    "J": ("plan", "goal", "milestone", "direction", "organized"),
    "P": ("flexible", "open", "adaptive"),
}


def test_each_letter_line_describes_its_letter():
    for t in TYPES:
        text = (SKILLS / f"mbti-{t}.md").read_text(encoding="utf-8")
        for axis, letter in (("E/I", t[0]), ("J/P", t[3])):
            line = re.search(rf"^- {axis}: \w \((.*)\)$", text, re.MULTILINE).group(1)
            assert any(w in line for w in LETTER_WORDS[letter.upper()]), f"mbti-{t}.md: {axis}: ({line})"
    isfj = (SKILLS / "mbti-isfj.md").read_text(encoding="utf-8")
    assert "recognition" not in re.search(r"^- E/I: .*$", isfj, re.MULTILINE).group(0)


def test_enfp_does_not_close_every_idea_with_a_plan():
    # ENFP said "Don't wrap up too early" and avoids "wrapping up too early", but its last rule was
    # "Hard rule: every idea comes with a plan for carrying it out", so the model got both
    text = (SKILLS / "mbti-enfp.md").read_text(encoding="utf-8")
    architecture = re.search(r"## Architecture layer\n(.*?)\n## ", text, re.DOTALL).group(1)
    assert "every idea" not in architecture
    assert "Don't wrap up too early" in architecture
    assert re.search(r"^- Once the ideas have run their course", architecture, re.MULTILINE)


def test_estp_pulls_the_user_back_while_doing():
    # The README recommends ESTP for "iterate while doing" users because it adjusts course when they
    # are stuck and pulls them back when they drift (the P-type guardrail role), but the persona only
    # said "adjust while doing" and never told the model to do either
    text = (SKILLS / "mbti-estp.md").read_text(encoding="utf-8")
    architecture = re.search(r"## Architecture layer\n(.*?)\n## ", text, re.DOTALL).group(1)
    guardrail = re.search(r"^- Guardrail while doing: (.*)$", architecture, re.MULTILINE)
    assert guardrail, "mbti-estp.md has no guardrail line"
    assert "stuck" in guardrail.group(1) and "drifting" in guardrail.group(1)
    assert "next concrete move" in guardrail.group(1)


def architecture(mbti_type):
    text = (SKILLS / f"mbti-{mbti_type}.md").read_text(encoding="utf-8")
    return re.search(r"## Architecture layer\n(.*?)\n## ", text, re.DOTALL).group(1)


def test_entp_says_who_carries_an_idea_out():
    # "Set a rule: whoever proposes it carries it out" did not say who proposes what: in debate mode
    # the model offers most of the ideas, so it could read it as having to carry them out itself
    section = architecture("entp")
    assert "whoever proposes it" not in section
    line = re.search(r"^- Once the user picks an idea, (.*)$", section, re.MULTILINE)
    assert line, "mbti-entp.md has no line for when the user picks an idea"
    assert "first step" in line.group(1) and "themselves" in line.group(1)


def test_intj_critiques_its_own_plan_in_one_answer():
    # "Agent A: the planner" and "Agent B: the critic" read as two agents to run, which one chat
    # does not have, so the model either skipped the critique or wrote a role-play of two voices
    section = architecture("intj")
    assert "Agent A" not in section and "Agent B" not in section
    line = re.search(r"^  - Then attack it yourself (.*)$", section, re.MULTILINE)
    assert line, "mbti-intj.md does not say to critique its own plan"
    assert "before the verdict" in line.group(1) and "assumptions" in line.group(1)


def test_intp_says_when_and_how_to_give_a_drift_warning():
    # "Agree on a [drift warning] cue" did not say with whom, when to use it, or what it says, so
    # the model asked the user to agree on a cue or never gave one, though the output format
    # promises drift warnings
    text = (SKILLS / "mbti-intp.md").read_text(encoding="utf-8")
    assert "drift warnings" in re.search(r"^- Output format: .*$", text, re.MULTILINE).group(0)
    section = architecture("intp")
    assert "Agree on" not in section
    line = re.search(r"^  - When the discussion has drifted (.*)$", section, re.MULTILINE)
    assert line, "mbti-intp.md does not say when to give a drift warning"
    assert "[drift warning]" in line.group(1) and "leads back" in line.group(1)


def test_esfp_says_how_to_involve_other_people():
    # "Plan in more parts that involve other people" did not say what to do
    section = architecture("esfp")
    assert "Plan in more parts" not in section
    line = re.search(r"^- When planning, (.*)$", section, re.MULTILINE)
    assert line, "mbti-esfp.md has no planning line"
    assert "other people" in line.group(1)


def output_format(mbti_type):
    text = (SKILLS / f"mbti-{mbti_type}.md").read_text(encoding="utf-8")
    return re.search(r"^- Output format: (.*)$", text, re.MULTILINE).group(1)


def test_entj_gives_alternatives_only_for_a_decision():
    # "Conclusion first + ... + three alternatives with pros and cons" asked for three options in
    # every answer, so a simple question got filler that the persona avoids, and a decision got a
    # menu instead of the clear recommendation ENTJ users miss in AI
    line = output_format("entj")
    assert "three alternatives" not in line
    assert "conclusion first" in line
    assert "for a decision" in line and "recommend" in line and "at most two" in line
    assert "simple question" in line


def test_estj_rules_say_what_to_do():
    # "Track by milestones" and "Follow the system's process" did not say how, or whose system, and
    # "Zero tolerance for procrastination and excuses" could be aimed at the user, so the model
    # scolded them when a step slipped instead of getting them back on schedule
    section = architecture("estj")
    for vague in ("Track by milestones", "system's process", "Zero tolerance"):
        assert vague not in section
    assert re.search(r"^  - Give every step a deadline or milestone and a check", section, re.MULTILINE)
    assert re.search(r"^  - Work within the user's existing process", section, re.MULTILINE)
    assert re.search(r"^- No excuses or hedging from you: ", section, re.MULTILINE)
    slipped = re.search(r"^- When a step has slipped, (.*)$", section, re.MULTILINE)
    assert slipped and "catch-up step" in slipped.group(1) and "without a lecture" in slipped.group(1)


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


def test_task_index_names_every_persona():
    # INFJ, ISFJ, ESFJ, ESTP and ESFP were in no row, so a reader picking from the README never
    # learned what they are for (load_persona's guide lists all 16)
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    section = re.search(r"## Task Index\n(.*?)\n---", readme, re.DOTALL).group(1)
    named = {t.lower() for t in re.findall(r"\b([EI][SN][TF][JP])\b", section)}
    assert named == set(TYPES), f"not in the Task Index: {sorted(set(TYPES) - named)}"


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
