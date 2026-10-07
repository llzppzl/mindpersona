# MindPersona
[English](./readme.md) | [中文](./README-zh.md)
> Give your AI Agent a "personality" — stop settling for generic responses

## Pain Points

1. **You are a "get-things-done, straight-to-the-point" type**
   Your problem: It's meeting time, you need to quickly assess pros and cons of a plan. You throw the question to AI, and it serves you a formulaic essay: 200 words of industry background, sprinkled with "however, admittedly," and finally a disclaimer "specific situations require specific analysis." Watching this runaround wastes your time and spikes your blood pressure. Now you have to repeatedly emphasize "no formalities, no disclaimers, data tables only" for every query — communication overhead is exhausting.
   What you need: A **"Cold Chief of Staff"** style Agent. It knows not to hedge, not to waste words, and delivers precise conclusions like "Option A has 30% risk, Option B saves 50K, recommend B."

2. **You are a "high-sensitive person who needs positive reinforcement"**
   Your problem: Feeling terrible today, work piling up, brain completely crashed. You reach out to AI for help. It instantly dumps a half-hour-by-half-hour "perfect schedule" and tells you to start the Pomodoro technique immediately. Facing these cold commands, your suffocation kicks in — no motivation to execute, just more desire to escape. In that vulnerable moment, the machine's "absolute rationality" becomes invisible pressure.
   What you need: A **"Trusted Partner"** style Agent. It catches your emotions first, tells you "it's okay to have a bad day," then breaks tasks into tiny, pressure-free micro-tasks, coaxing you to start.

3. **You are a "think randomly, brainstorm out loud" type creator**
   Your problem: A brilliant but extremely fragmented idea pops into your head. You excitedly send this wild bunch of thoughts to AI hoping for a collision. But since it can't handle this "loose expression," it downgrades you to a bland conventional outline. Watching those generic phrases, you start doubting yourself: "Is my expression too poor? Is my Prompt written wrong?" You just wanted to chat about an idea, but got forced to learn structured prompt writing.
   What you need: An **"Idea Translator"** style Agent. It understands your divergent thinking, catches your fragmented input, actively helps sort out logical threads — instead of demanding perfectly formed instructions from the start.

4. **You are a "perfect planner, always stuck at execution" flexible responder**
   Your problem: Using AI for planning is excellent — it always delivers flawless execution plans. But the moment you start doing, you get stuck. Because your work habit is to iterate while doing, easily derailed by unexpected events. Yet current AI only focuses on "generating the perfect plan" — if you didn't complete yesterday's task, that perfect schedule becomes useless today. It won't pull you back mid-execution or adjust based on your progress.
   What you need: An **"Agile Coach"** style Agent. Plans are worthless without execution. You need it to adjust course when you're stuck, pull you back when you drift, providing "dynamic companionship" as an execution guardrail — instead of dumping a rigid table at once.

---

## Problem

Generic Agents are like "diplomats with no personality" — they don't make mistakes for anyone, but for people with specific personality types, they're either too rough, too rigid, too cold, or too abstract.

**Root cause**: LLMs' RLHF alignment pursues the "greatest common divisor," which is severely misaligned with users' highly differentiated cognitive models (MBTI).

## Solution

**MBTI Three-Layer Mapping Framework** — achieving personal cognitive alignment through three technical layers:

| Layer | Technical Approach | Matched MBTI Dimension |
|-------|-------------------|------------------------|
| Interaction | System Prompt + Template Constraints | S/N (format), T/F (tone) |
| Architecture | Workflow + Multi-Agent | J/P (execution push) |
| Memory | Memory + RAG | Universal for all personalities |

### Interaction Layer: How to Speak

| Type | Content Format | Communication Tone |
|------|---------------|-------------------|
| S-type | Specific data, historical cases, tables | Pragmatic executor |
| N-type | Grand visions, underlying logic, mind maps | Strategic advisor |
| T-type | Cold logic, hitting pain points | Ruthless critic |
| F-type | Emotional value, understanding & acceptance | Highly empathetic listener |

### Architecture Layer: How to Get Things Done

| Type | Workflow Style | Agent Role |
|------|--------------|------------|
| J-type | WBS waterfall with node acceptance | Machine: fill in sequence |
| P-type | Agile iteration, diverge-converge dual track | Guardrail: prevent derailment |

### Memory Layer: Remember Who You Are

Accumulate "minefields" and "north star metrics" to eliminate repeated tuning costs.

**Universal Memory (skills/mbti-*.md)**: Based on MBTI theory's typical preferences
**Personal Evolution (memory/customized-*.md)**: User feedback accumulation, personalized adjustments

---

## Task Index

| Your Task | Description | Recommended MBTI |
|-----------|-------------|-----------------|
| Execution Output | Quick results (ESTJ) / Drive others (ENTJ) / Execute by rules (ISTJ) | ESTJ / ENTJ / ISTJ |
| Goal Breakdown | Strategic decomposition (ENTJ) / Scheduling + daily tasks (ESTJ) / Acceptance criteria (ISTJ) | ENTJ / ESTJ / ISTJ |
| Option Analysis | Compare pros/cons, give judgment (INTJ) / Find logical flaws (INTP) | INTJ / INTP |
| Decision Making | Prevent overthinking, push forward | ENTJ |
| Emotional Buffer | Catch feelings first, no solutions (INFP) / Companionship (ISFP) | INFP / ISFP |
| Ideation | Open mind (ENFP) / Connect & collide, find opposites (ENTP) / Connect to personal meaning (INFP) | ENFP / ENTP / INFP |
| Logic Analysis | Causal analysis (INTP) / Critical examination (INTJ) / Trace chains (ISTP) | INTP / INTJ / ISTP |
| Cognitive Compression | Structured distillation (ISTJ) / Prioritization (INTJ) | ISTJ / INTJ |
| Growth Motivation | Connect personal vision, find meaning and motivation | ENFJ |

---

## Core Formula

```
Diagnose MBTI → Configure interaction format & tone (S/N + T/F)
             → Build a workflow that goes with your nature or makes up for its blind spots (J/P)
             → Solidify into long-term memory (memory/customized-{mbti}.md)
```

> Don't try to make AI adapt to everyone. Use this framework to make AI obey only you.

---

## 🚀 Quick Start

### Claude Code (MCP server)

```bash
git clone https://github.com/llzppzl/mindpersona.git
cd mindpersona
python3 -m pip install -r platform/claude/requirements.txt
claude mcp add mindpersona -s user -- "$(which python3)" "$(pwd)/platform/claude/mcp_server.py"
```

This needs Python 3.10 or newer (check with `python3 --version`; the python3 that comes with macOS is 3.9). Restart Claude Code. Then:

| You type | What happens |
|----------|--------------|
| `/` and pick `mbti-intj` (or any other type) from the menu | Claude answers as that persona for the rest of the chat |
| "Too long, just give me the conclusion" while a persona is on | Claude saves this as a lasting preference for that persona |

Saved preferences live in `memory/customized-<type>.md` in your clone. They stay on your machine (the folder is git-ignored) and load with the persona from then on. More setup details and troubleshooting: [platform/claude/README.md](./platform/claude/README.md).

### Claude Code, inside this repo (no install)

Open the cloned folder in Claude Code and type a type, like `entj`, or ask "use ENTJ to plan my week". [CLAUDE.md](./CLAUDE.md) tells Claude where the personas and your saved preferences are.

### Any chat app (no install)

Open a file in [`skills/`](./skills), for example [`skills/mbti-intj.md`](./skills/mbti-intj.md), and paste it into ChatGPT custom instructions, a Claude Project or your system prompt.

### Other platforms

| Platform | Guide |
|----------|-------|
| Semantic Kernel | [platform/semantic-kernel/](./platform/semantic-kernel/) |
| Coze / Dify | [platform/saas/IMPORT_GUIDE.md](./platform/saas/IMPORT_GUIDE.md) |
| Direct API | [platform/api/prompts.yaml](./platform/api/prompts.yaml) |

### Not sure which type to pick?

Use the Task Index above, or describe your task and ask: "Which MBTI persona fits this: I have to make a big decision with little time?"

---

## 📁 File Structure

| File/Directory | Purpose |
|---------------|---------|
| `CLAUDE.md` | Project instructions (auto-loaded by AI) |
| `skills/mbti-*.md` | Universal baseline (16 MBTI types) |
| `memory/customized-*.md` | Your personal evolution (local, not uploaded to git) |
| `platform/` | Cross-platform adaptation layer |
| `platform/claude/` | Claude MCP Server adapter |
| `platform/semantic-kernel/` | Semantic Kernel framework adapter |
| `platform/saas/` | SaaS platform (Coze/Dify) import guide |
| `platform/api/` | API direct prompt index |

---

## Supported MBTI Types

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
