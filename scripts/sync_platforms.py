"""Regenerate the platform prompt copies from skills/mbti-*.md, so they match skills/.

skills/ is the single source. After changing a skill, run:

    python scripts/sync_platforms.py

This updates:
- platform/semantic-kernel/<type>/skprompt.txt
- the template in platform/semantic-kernel/<type>/config.json
- each type's CLEAN Prompt in platform/saas/IMPORT_GUIDE.md

With --check it writes nothing and exits with 1 if anything is out of date (for CI).
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_DIR / "skills"
SK_DIR = REPO_DIR / "platform" / "semantic-kernel"
SAAS_GUIDE = REPO_DIR / "platform" / "saas" / "IMPORT_GUIDE.md"

# An HTML comment on a line of its own is a note for maintainers, not part of the prompt
COMMENT_LINE = re.compile(r"^[ \t]*<!--.*?-->[ \t]*\n", re.MULTILINE)


def clean_prompt(skill_text: str) -> str:
    """The skill without its comment lines: the prompt the model gets"""
    return COMMENT_LINE.sub("", skill_text).strip()


def without_title(prompt: str) -> str:
    """Drop the "# INTJ - ..." title line (the SaaS guide already has the same heading above each prompt)"""
    lines = prompt.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def load_skills() -> dict:
    """{"intj": clean prompt, ...}"""
    skills = {}
    for path in sorted(SKILLS_DIR.glob("mbti-*.md")):
        mbti = path.stem.removeprefix("mbti-")
        skills[mbti] = clean_prompt(path.read_text(encoding="utf-8"))
    return skills


def expected_files(skills: dict) -> dict:
    """{Path: the content it should have}"""
    files = {}

    for mbti, prompt in skills.items():
        sk = SK_DIR / mbti
        files[sk / "skprompt.txt"] = prompt + "\n"

        config_path = sk / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["prompts"][0]["template"] = prompt
        files[config_path] = json.dumps(config, ensure_ascii=False, indent=2) + "\n"

    guide = SAAS_GUIDE.read_text(encoding="utf-8")
    for mbti, prompt in skills.items():
        # The code block under "### CLEAN Prompt" below the "## INTJ - ..." heading
        block = re.compile(
            rf"(^## {mbti.upper()} - [^\n]*\n\s*### CLEAN Prompt\s*\n\s*```\n)(.*?)(\n```)",
            re.MULTILINE | re.DOTALL,
        )
        if not block.search(guide):
            raise SystemExit(f"{SAAS_GUIDE.relative_to(REPO_DIR)}: no CLEAN Prompt block for {mbti.upper()}")
        guide = block.sub(lambda m: m.group(1) + without_title(prompt) + m.group(3), guide, count=1)
    files[SAAS_GUIDE] = guide

    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only check, write nothing; exit with 1 if anything is out of date")
    args = parser.parse_args()

    skills = load_skills()
    missing = [mbti for mbti in skills if not (SK_DIR / mbti / "config.json").exists()]
    if missing:
        raise SystemExit(f"platform/semantic-kernel has no folder for: {', '.join(missing)}")

    stale = []
    for path, content in expected_files(skills).items():
        if path.read_text(encoding="utf-8") != content:
            stale.append(path.relative_to(REPO_DIR))
            if not args.check:
                path.write_text(content, encoding="utf-8")

    if args.check:
        if stale:
            print("These files are out of sync with skills/:")
            for path in stale:
                print(f"  {path}")
            print("Run: python scripts/sync_platforms.py")
            return 1
        print("All platform prompts match skills/.")
        return 0

    print(f"Updated {len(stale)} file(s)." if stale else "Already in sync.")
    for path in stale:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
