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

## Troubleshooting

If `claude mcp list` shows `✘ Failed to connect` for mindpersona, run the command after `--` yourself (`python /absolute/path/to/mcp_server.py`) to see the error. When it works, it prints nothing and waits for input. Press Ctrl+C to quit.

| Error | Fix |
|-------|-----|
| `MindPersona needs mcp 1.x` or `'Server' object has no attribute 'list_prompts'` | mcp 2.x is installed. Run `pip install 'mcp>=1.3,<2'` (or `pip install -r requirements.txt` again) |
| `Failed to build cryptography` on an Intel Mac | Run `pip install -r requirements.txt` again. It installs a cryptography version that has Intel wheels |
| `No module named mcp` | The python in `claude mcp add` is not the one you installed the dependencies with. Add the server again with the full path from `which python3` |

## 使用方式

在 Claude 输入框中：
- `/mbti-intj` - 切换到 INTJ 逻辑学家模式
- `/mbti-infp` - 切换到 INFP 知心搭档模式
- ... (其他 14 个 MBTI 同理)

## 支持的 MBTI 类型

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
