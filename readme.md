# MindPersona
[English](./readme.md) | [中文](./README-zh.md)
> Give your AI Agent a "personality" — stop settling for generic responses

## 🚀 Quick Start

### Claude Code (recommended, 1 command)

Needs [uv](https://docs.astral.sh/uv/getting-started/installation/). uv downloads Python 3.10+ for you if you don't have it.

```bash
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
```

Restart Claude Code. Then, in **any** project:

| You type | What happens |
|----------|--------------|
| `Use ESTJ to turn this into a plan for this week` | Claude loads the ESTJ persona (`load_persona` tool) and answers in that style |
| `Which persona fits this? I must choose between two offers by Friday` | Claude picks a type from the Task Index below, tells you why, and loads it |
| `/mcp__mindpersona__mbti-intj` | Loads INTJ as a slash prompt (in the `/` menu it is listed as `/mindpersona:mbti-intj (MCP)`) |
| `Too long. Stop using tables.` | Claude saves this to your personal file and follows it next time |

Your feedback is stored in `~/.mindpersona/memory/customized-<type>.md`. Set `MINDPERSONA_MEMORY_DIR` to keep it somewhere else.

**One persona for everything (optional).** Add `--persona <type>` at the end, and every session answers in that persona without being asked:

```bash
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona --persona intj
```

You can still switch for one task (`Use ENFP to brainstorm this`). To change the default, run `claude mcp remove mindpersona -s user` and add it again with another type.

Without uv:

```bash
pip install git+https://github.com/llzppzl/mindpersona
claude mcp add mindpersona -s user -- mindpersona
```

`claude mcp list` shows `✘ Failed to connect`? See [Troubleshooting](./platform/claude/README.md#troubleshooting).

### Any chat app (no install)

Open a file in [`skills/`](./skills), for example [`skills/mbti-intj.md`](./skills/mbti-intj.md), and paste it into ChatGPT custom instructions, a Claude Project, or your system prompt. The skills are written in Chinese; the model will still answer in your language.

### Other platforms

| Platform | Where |
|----------|-------|
| Semantic Kernel | [`platform/semantic-kernel/`](./platform/semantic-kernel) |
| Coze / Dify | [`platform/saas/IMPORT_GUIDE.md`](./platform/saas/IMPORT_GUIDE.md) |
| API direct | [`platform/api/prompts.yaml`](./platform/api/prompts.yaml) |

### From source

```bash
git clone https://github.com/llzppzl/mindpersona.git
cd mindpersona
pip install -e .          # Python 3.10+
python -m pytest tests
```

---

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
             → Build a workflow that follows your nature or covers your blind spots (J/P)
             → Save it to long-term memory (memory/customized-{mbti}.md)
```

> Don't try to make AI adapt to everyone. Use this framework to make AI obey only you.

---

## 📁 File Structure

| File/Directory | Purpose |
|---------------|---------|
| `CLAUDE.md` | Project instructions (auto-loaded by AI) |
| `skills/mbti-*.md` | Universal baseline (16 MBTI types) |
| `memory/customized-*.md` | Your personal evolution when running from source (installed: `~/.mindpersona/memory/`; never committed) |
| `mindpersona/server.py` | MCP server: slash prompts, `load_persona`, `update_mbti_memory` |
| `tests/` | Tests (`python -m pytest tests`) |
| `platform/` | Cross-platform adaptation layer |
| `platform/claude/` | Claude Code install guide and legacy `mcp_server.py` entry |
| `platform/semantic-kernel/` | Semantic Kernel framework adapter |
| `platform/saas/` | SaaS platform (Coze/Dify) import guide |
| `platform/api/` | API direct prompt index |

---

## Supported MBTI Types

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
