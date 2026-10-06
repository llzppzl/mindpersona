# MindPersona MCP Server

## 概述

MindPersona MCP Server 允许你在 Claude Code 中使用 MBTI 性格适配 Prompt。

## 安装步骤

1. 安装依赖：
   ```bash
   cd platform/claude
   pip install -r requirements.txt
   ```

2. 添加 MCP Server 到 Claude Code：

   **获取 Python 路径：**
   ```bash
   # Windows
   where python

   # macOS/Linux
   which python3
   ```

   **获取 mcp_server.py 绝对路径：**
   在文件管理器中右键 `platform/claude/mcp_server.py` → 复制文件路径

   **运行以下命令（请替换路径）：**
   ```bash
   # 用户级安装（所有项目可用）
   claude mcp add mindpersona -s user -- python 【mcp_server.py的绝对路径】

   # 或项目级安装（仅当前项目可用，可共享给团队）
   claude mcp add mindpersona -s project -- python 【mcp_server.py的绝对路径】
   ```

3. 重启 Claude Code（或关闭当前窗口后重新打开）

## 连不上怎么办

`claude mcp list` 里 mindpersona 显示 `✘ Failed to connect` 时，先手动运行 `--` 后面的命令（`python 【mcp_server.py的绝对路径】`）看报错。正常情况下它不输出任何内容，一直等待输入，按 Ctrl+C 退出。

| 报错 | 解决 |
|------|------|
| `MindPersona needs mcp 1.x` 或 `'Server' object has no attribute 'list_prompts'` | 环境里装的是 mcp 2.x，执行 `pip install 'mcp>=1.3,<2'`（或重新 `pip install -r requirements.txt`） |
| Intel Mac 上 `Failed to build cryptography` | 重新 `pip install -r requirements.txt`，它会装带 Intel 安装包的 cryptography 版本 |
| `No module named mcp` | `claude mcp add` 里用的 python 和装依赖的 python 不是同一个。用 `which python3` 得到的完整路径重新添加 |

## 使用方式

在 Claude 输入框中：
- `/mbti-intj` - 切换到 INTJ 逻辑学家模式
- `/mbti-infp` - 切换到 INFP 知心搭档模式
- ... (其他 14 个 MBTI 同理)

## 支持的 MBTI 类型

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
