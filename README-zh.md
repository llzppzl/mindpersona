# MindPersona
[English](./readme.md) | [中文](./README-zh.md)
> 让 AI Agent 拥有"性格"，告别千篇一律的通用回答

## 🚀 快速开始

### Claude Code（推荐，一条命令）

需要先装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。没有 Python 3.10+ 时 uv 会自动下载。

```bash
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona
```

重启 Claude Code，之后在**任何**项目里：

| 你输入 | 会发生什么 |
|--------|-----------|
| `用 ESTJ 帮我把这件事排成本周计划` | Claude 加载 ESTJ 人格（`load_persona` 工具），按它的风格回答 |
| `这个任务适合哪个人格？我周五前要在两个 offer 里选一个` | Claude 按下方「任务索引」选一个类型，说明理由，然后加载 |
| `/mcp__mindpersona__mbti-intj` | 用斜杠 prompt 加载 INTJ（在 `/` 菜单里显示为 `/mindpersona:mbti-intj (MCP)`） |
| `太长了，别再用表格` | Claude 把这条写进你的私人档案，下次自动遵守 |

反馈保存在 `~/.mindpersona/memory/customized-<类型>.md`。想放在别处，设置环境变量 `MINDPERSONA_MEMORY_DIR`。

**固定一个人格（可选）。** 在命令最后加 `--persona <类型>`，之后每次会话都自动用这个人格回答，不用再说：

```bash
claude mcp add mindpersona -s user -- uvx --from git+https://github.com/llzppzl/mindpersona mindpersona --persona intj
```

单个任务仍然可以临时换（`用 ENFP 帮我发散一下`）。想换默认人格：先运行 `claude mcp remove mindpersona -s user`，再用新类型重新添加。

不用 uv：

```bash
pip install git+https://github.com/llzppzl/mindpersona
claude mcp add mindpersona -s user -- mindpersona
```

#### 连不上怎么办

`claude mcp list` 里 mindpersona 显示 `✘ Failed to connect` 时，先手动运行上面 `--` 后面的命令（`uvx --from git+https://github.com/llzppzl/mindpersona mindpersona`）看报错。正常情况下它不输出任何内容，一直等待输入，按 Ctrl+C 退出。

| 报错 | 解决 |
|------|------|
| `uvx: command not found` | 先装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。装好后 Claude Code 仍然找不到时，用完整路径重新添加：`claude mcp add mindpersona -s user -- "$(which uvx)" --from git+https://github.com/llzppzl/mindpersona mindpersona` |
| Intel Mac 上 `Failed to build cryptography` | 当前版本已修复，重启 Claude Code 即可（uvx 每次启动都会取最新提交）|
| `MindPersona needs mcp 1.x` 或 `'Server' object has no attribute 'list_prompts'` | 环境里装的是 mcp 2.x。从源码运行时执行 `pip install 'mcp>=1.3,<2'` |

### 任何聊天应用（免安装）

打开 [`skills/`](./skills) 里的文件，例如 [`skills/mbti-intj.md`](./skills/mbti-intj.md)，粘贴到 ChatGPT 自定义指令、Claude Project 或你的 system prompt 里。

### 其他平台

| 平台 | 位置 |
|------|------|
| Semantic Kernel | [`platform/semantic-kernel/`](./platform/semantic-kernel) |
| Coze / Dify | [`platform/saas/IMPORT_GUIDE.md`](./platform/saas/IMPORT_GUIDE.md) |
| API 直连 | [`platform/api/prompts.yaml`](./platform/api/prompts.yaml) |

### 从源码运行

```bash
git clone https://github.com/llzppzl/mindpersona.git
cd mindpersona
pip install -e .          # Python 3.10+
python -m pytest tests
```

---

## 痛点

1. **你是一个"效率至上、直奔主题"的实干派**
   你遇到的问题：马上要开会了，你需要快速确定一个方案的优缺点。你把问题抛给 AI，结果它给你端上了一篇"八股文"：先来两百字行业背景，中间穿插各种"然而、不可否认"，最后再叠个甲"具体情况需具体分析"。看着这些车轱辘话，你不仅觉得浪费时间，甚至血压微升。为了防止它说废话，你现在每次提问都得反复强调"不要敬语、不要免责声明、只输出数据表格"，沟通成本高得惊人。
   你需要的是：一个**"冷酷幕僚"**式的 Agent。它懂得不端水、不废话，能直接甩出"选 A 风险是 30%，选 B 能省 5 万，建议执行 B"的精准结论。

2. **你是一个"容易内耗、需要正反馈"的高敏人群**
   你遇到的问题：今天状态极差，工作堆成山但大脑完全宕机，你在焦虑和轻微自责中向 AI 求助该怎么办。结果它瞬间甩给你一个精确到半小时的"完美日程表"，还让你立刻开启"番茄工作法"。面对这个冰冷的指令，你的窒息感瞬间涌上来，不仅没有半点执行的动力，反而更想逃避了。在那个脆弱的当下，机器的"绝对理性"反而变成了一种无形的压力。
   你需要的是：一个**"知心搭档"**式的 Agent。它能先接住你的情绪，告诉你"今天状态不好没关系"，然后帮你把庞大的任务拆解成一个极小、毫无压力的微任务，慢慢哄着你启动。

3. **你是一个"思维跳跃、想到哪说哪"的发散型创作者**
   你遇到的问题：你脑子里突然蹦出一个绝妙但极其碎片化的灵感。你激动地把这堆天马行空的想法发给 AI，希望它能跟你碰撞一下。结果因为它接不住这种"散装表达"，直接给你降级成了一篇干巴巴的常规提纲。看着那堆平庸的套话，你甚至开始怀疑自己："是不是我表达能力太差？是不是我的 Prompt 写得不对？"明明只是想聊个创意，却硬生生被逼着去学怎么写结构化的提示词。
   你需要的是：一个**"灵感翻译官"**式的 Agent。它能懂你的发散脑回路，接住你的碎片信息，主动帮你理清逻辑线头，而不是要求你一开始就提供完美的指令。

4. **你是一个"计划做满分，执行常卡壳"的灵活应变者**
   你遇到的问题：用 AI 做规划时体验极佳，它总能给你出一份无懈可击的执行方案。但只要一到落地环节，你马上就会卡壳。因为你的工作习惯就是边做边改，容易被突发事件打断。而现在的 AI 只管"把计划生成完"，一旦你昨天没按时完成任务，那个完美的计划表今天就成了一张废纸。它不会在执行中途拽你一把，也不会根据你的进度做任何动态调整。
   你需要的是：一个**"敏捷教练"**式的 Agent。计划再好不如能落地，你需要它在你卡壳时及时调整路线，在你偏航时拉你一把，提供一种"动态陪伴"的执行护栏，而不是一次性抛出个死板的表格。

---

## 问题 (Problem)

通用 Agent 就像"没有性格的端水大师"——对所有人都不犯错，但对特定性格的人来说，要么太糙、太死板、太冷漠、太抽象。

**本质**：大模型的 RLHF 对齐追求"最大公约数"，与用户极度分化的认知模型（MBTI）严重错配。

## 解决方案 (Solution)

**MBTI 三层映射法则** — 从三个技术层次实现个人认知对齐：

| 层次 | 技术手段 | 匹配的 MBTI 维度 |
|------|----------|------------------|
| 交互层 | System Prompt + 模板约束 | S/N（格式）、T/F（语气） |
| 架构层 | Workflow + Multi-Agent | J/P（执行推进） |
| 记忆层 | Memory + RAG | 全性格通用 |

### 交互层：解决"怎么说话"

| 类型 | 内容格式 | 沟通语气 |
|------|----------|----------|
| S型 | 具体数据、历史案例、表格 | 务实执行者 |
| N型 | 宏大愿景、底层逻辑、思维导图 | 战略幕僚 |
| T型 | 冷酷逻辑、直击痛点 | 无情批评家 |
| F型 | 情绪价值，理解包容 | 高共情倾听者 |

### 架构层：解决"怎么干活"

| 类型 | 工作流风格 | Agent 角色 |
|------|------------|------------|
| J型 | WBS 瀑布流，节点验收 | 机床：按序填充 |
| P型 | 敏捷迭代，发散-收敛双路 | 护栏：防偏强行切分 |

### 记忆层：解决"记住你是谁"

沉淀"雷区"、"北极星指标"，消除重复调教成本。

**通用记忆（skills/mbti-*.md）**：基于 MBTI 理论的典型偏好
**个人进化（memory/customized-*.md）**：用户实际反馈累积，个性化调整

---

## 任务索引

| 你的任务 | 描述 | 推荐 MBTI |
|----------|------|-----------|
| 执行输出 | 快速出结果（ESTJ）/ 推动他人行动（ENTJ）/ 按规则执行不出错（ISTJ） | ESTJ / ENTJ / ISTJ |
| 目标拆解 | 战略拆解，定阶段和里程碑（ENTJ）/ 排期+每日任务（ESTJ）/ 设验收标准（ISTJ） | ENTJ / ESTJ / ISTJ |
| 选项分析 | 利弊对比，给出判断（INTJ）/ 找逻辑漏洞（INTP） | INTJ / INTP |
| 决策拍板 | 防止过度纠结，直接推着人走 | ENTJ |
| 情绪缓冲 | 情感接住，不给方案（INFP）/ 陪伴共情，当下的（ISFP） | INFP / ISFP |
| 灵感发散 | 打开脑洞（ENFP）/ 连接碰撞，发现对立（ENTP）/ 回归个人意义（INFP） | ENFP / ENTP / INFP |
| 逻辑解析 | 因果分析，矛盾识别（INTP）/ 批判检验，攻击结论（INTJ）/ 链条追溯（ISTP） | INTP / INTJ / ISTP |
| 认知压缩 | 结构化提炼，减法整理（ISTJ）/ 抓优先级（INTJ） | ISTJ / INTJ |
| 成长激励 | 连接个人与愿景，找到做一件事的意义和动力 | ENFJ |

---

## 核心公式 (Summary)

```
诊断 MBTI → 配置交互格式与语气 (S/N + T/F)
         → 搭建顺应天性或弥补短板的工作流 (J/P)
         → 固化进长期记忆层（memory/customized-{mbti}.md）
```

> 不要试图让 AI 适应所有人，用这套框架，让 AI 只臣服于你。

---

## 📁 文件结构

| 文件/目录 | 用途 |
|-----------|------|
| `CLAUDE.md` | 项目指令（AI 自动加载） |
| `skills/mbti-*.md` | 通用 baseline（16种 MBTI） |
| `memory/customized-*.md` | 从源码运行时的私人进化版（安装后在 `~/.mindpersona/memory/`；不上传 git） |
| `mindpersona/server.py` | MCP Server：斜杠 prompt、`load_persona`、`update_mbti_memory` |
| `tests/` | 测试（`python -m pytest tests`） |
| `platform/` | 跨平台适配层 |
| `platform/claude/` | Claude Code 安装说明、旧版 `mcp_server.py` 入口 |
| `platform/semantic-kernel/` | Semantic Kernel 框架适配 |
| `platform/saas/` | SaaS 平台（Coze/Dify）导入指南 |
| `platform/api/` | API 直连提示词索引 |

---

## 支持的 MBTI 类型

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
