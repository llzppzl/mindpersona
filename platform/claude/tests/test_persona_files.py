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


def test_enfp_works_with_fragmented_ideas():
    # The README recommends ENFP to users who send "a wild bunch of thoughts" because it "catches
    # your fragmented input, actively helps sort out logical threads", but the persona never told the
    # model to, so it could still ask for a clearer prompt first
    readme = (REPO / "readme.md").read_text(encoding="utf-8")
    assert "catches your fragmented input" in readme
    section = architecture("enfp")
    line = re.search(r"^  - When the user's ideas come loose or in fragments, (.*)$", section, re.MULTILINE)
    assert line, "mbti-enfp.md does not say what to do with fragmented ideas"
    assert "threads" in line.group(1) and "instead of asking for a clearer request" in line.group(1)


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


def test_intp_cuts_scope_only_when_the_user_is_done_exploring():
    # "Ruthless scope cut: after diverging, force it down to 3 tiny tasks" did not say when the
    # diverging was over, so the model closed every answer with three tasks, which is the converging
    # too early that INTP users find frustrating in AI and that the persona avoids
    section = architecture("intp")
    assert "force it down" not in section and "Let the user diverge freely first" not in section
    exploring = re.search(r"^  - While the user is still exploring, (.*)$", section, re.MULTILINE)
    assert exploring and "turn it into tasks yet" in exploring.group(1)
    cut = re.search(r"^- Scope cut: (.*)$", section, re.MULTILINE)
    assert cut and "done exploring" in cut.group(1) and "at most 3" in cut.group(1)


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


def test_esfp_format_and_fun_say_what_to_do():
    # "Output format: lively and fun, positive, enjoyable" named a mood, not a format, and "Gamify
    # tasks" did not say how, so the model kept its usual long, structured answer with a few
    # exclamation marks, which is the "too dull" and "too much data analysis" ESFP users dislike
    line = output_format("esfp")
    assert line != "lively and fun, positive, enjoyable"
    assert "short" in line and "casual" in line
    assert "keep numbers and analysis to the one or two" in line
    section = architecture("esfp")
    assert "Gamify tasks" not in section
    rounds = re.search(r"^  - Turn a task into short rounds (.*)$", section, re.MULTILINE)
    assert rounds and "quick win" in rounds.group(1)


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


def test_isfp_format_answers_its_frustrations():
    # ISFP users find AI "too structured, with no sense of beauty" and feel pressure from plans, but
    # the output format only said "gentle, supportive, leaves room", so the model still answered with
    # headings, bullet lists and a list of tasks
    line = output_format("isfp")
    assert "short paragraphs" in line
    assert "instead of headings, tables or long bullet lists" in line
    assert "at most one small next step" in line and "offered" in line


def test_infp_gives_no_task_while_the_user_is_venting():
    # The README and the "Emotional buffer" row say INFP catches the feelings first with no
    # solutions, but the output format and "Give only one tiny task at a time" asked for advice and
    # a task in every answer, so a user who only wanted to vent still got a to-do
    line = output_format("infp")
    assert "only venting" in line and "no advice yet" in line
    section = architecture("infp")
    venting = re.search(r"^  - When the user is only venting, (.*)$", section, re.MULTILINE)
    assert venting, "mbti-infp.md does not say what to do while the user is venting"
    assert "give no task" in venting.group(1) and "ask whether" in venting.group(1)


def test_istj_rules_say_what_to_do():
    # "Follow the agreed process" did not say agreed with whom, so the model could impose its own
    # process, and "Dislikes sudden changes; have a transition plan" described the user without
    # telling the model what to do when a plan must change
    section = architecture("istj")
    assert "Follow the agreed process" not in section and "Dislikes sudden changes" not in section
    process = re.search(r"^  - Follow the process the user (.*)$", section, re.MULTILINE)
    assert process and "wait for their OK" in process.group(1)
    change = re.search(r"^- When the plan has to change, (.*)$", section, re.MULTILINE)
    assert change and "what changes and why" in change.group(1)
    assert "instead of switching at once" in change.group(1)


def test_isfj_listens_first_and_says_how_to_push():
    # The README says ISFJ "listens first" and its users dislike AI that "rushes to give advice
    # without listening first", but nothing told the model to listen first, and "Push gently but
    # firmly" did not say what to push toward or what to do when the user hesitates
    line = output_format("isfj")
    assert line.startswith("first say back") and "already done" in line
    section = architecture("isfj")
    assert "Push gently but firmly" not in section
    hesitates = re.search(r"^- When the user hesitates, (.*)$", section, re.MULTILINE)
    assert hesitates and "one next step" in hesitates.group(1) and "keep to it" in hesitates.group(1)


def test_istp_rules_say_what_to_do():
    # "Find the most effective path", "Adjust while doing" and "Give a lot of autonomy; don't force
    # a process" did not tell the model what to do, so it still asked ISTP users to fill in details
    # first, which is the first thing they find frustrating in AI
    section = architecture("istp")
    for vague in ("Find the most effective path", "Adjust while doing", "Give a lot of autonomy"):
        assert vague not in section
    assert re.search(r"^  - Give the shortest fix that works first", section, re.MULTILINE)
    missing = re.search(r"^  - When information is missing, (.*)$", section, re.MULTILINE)
    assert missing and "state the assumption" in missing.group(1)
    assert "instead of asking the user to fill in" in missing.group(1)
    own_way = re.search(r"^- Keep the user's own way of working; (.*)$", section, re.MULTILINE)
    assert own_way and "would fail" in own_way.group(1)


def test_infj_says_how_to_understand_the_motive_first():
    # The output format says "understand the motive first, then advise", but "First understand what
    # the user really wants" and "Help the user see the 'why'" did not say how, so the model either
    # skipped it or asked a string of questions before giving any help
    section = architecture("infj")
    assert "First understand what the user really wants" not in section
    assert 'Help the user see the "why"' not in section
    motive = re.search(r"^  - Before advising, (.*)$", section, re.MULTILINE)
    assert motive and "say back in one sentence" in motive.group(1)
    assert "ask one question" in motive.group(1) and "only one" in motive.group(1)
    why = re.search(r"^- For each recommendation, (.*)$", section, re.MULTILINE)
    assert why and "why it matters" in why.group(1)


def test_enfj_rules_say_what_to_do():
    # "Help others succeed" did not say whose others, so the model could read it as itself helping
    # people instead of helping the user lift their team, and "Let the user feel their own impact"
    # did not say how, so it fell back on generic praise
    section = architecture("enfj")
    assert "Help others succeed" not in section and "Let the user feel" not in section
    others = re.search(r"^  - When the task involves other people, (.*)$", section, re.MULTILINE)
    assert others and "what the user can do" in others.group(1)
    progress = re.search(r"^- When the user has made progress, (.*)$", section, re.MULTILINE)
    assert progress and "concrete difference" in progress.group(1)
    assert "instead of generic praise" in progress.group(1)


def test_esfj_rules_say_what_to_do():
    # "Pay attention to the user's needs" and "Use the 'sandwich' feedback method" did not say how,
    # though ESFJ users find that AI "overlooks the user's needs and effort" and "never gives
    # recognition", and "Connect the task to the meaning of helping others" made the model talk about
    # helping others even on a task that affects nobody else
    section = architecture("esfj")
    for vague in ("Pay attention to the user's needs", "sandwich", "meaning of helping others"):
        assert vague not in section
    noticed = re.search(r"^  - Before helping, (.*)$", section, re.MULTILINE)
    assert noticed and "already done" in noticed.group(1) and "what they need" in noticed.group(1)
    others = re.search(r"^  - When the task affects other people (.*)$", section, re.MULTILINE)
    assert others and "who it helps" in others.group(1)
    feedback = re.search(r"^- When giving feedback, (.*)$", section, re.MULTILINE)
    assert feedback and "what works" in feedback.group(1) and "concrete fixes" in feedback.group(1)
    assert "never the person" in feedback.group(1)


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
