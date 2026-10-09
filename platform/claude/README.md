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

## 使用方式

在 Claude 输入框中：
- `/mbti-intj` - 切换到 INTJ 逻辑学家模式
- `/mbti-infp` - 切换到 INFP 知心搭档模式
- ... (其他 14 个 MBTI 同理)

Or just ask in plain words, and Claude loads the persona with the `load_persona` tool:
- "Use ESTJ to analyze this plan"
- "Switch to infp"
- "Which persona fits this task? Pick one for me"

## 支持的 MBTI 类型

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
