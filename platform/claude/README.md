# MindPersona MCP Server

## Overview

The MindPersona MCP server lets you use the MBTI persona prompts in Claude Code.

## Setup

1. Install the dependencies:
   ```bash
   cd platform/claude
   pip install -r requirements.txt
   ```

2. Add the MCP server to Claude Code:

   **Find the full path of your Python** (the one you ran `pip install` with):
   ```bash
   # Windows
   where python

   # macOS/Linux
   which python3
   ```

   **Find the full path of mcp_server.py:** in a terminal inside `platform/claude`, run `pwd` (macOS/Linux) or `cd` (Windows) and add `/mcp_server.py` to what it prints.

   **Run one of these commands, with your two paths:**
   ```bash
   # For you, in every project
   claude mcp add mindpersona -s user -- /full/path/to/python3 /full/path/to/mcp_server.py

   # Or only for the current project (saved in .mcp.json, so you can share it with your team)
   claude mcp add mindpersona -s project -- /full/path/to/python3 /full/path/to/mcp_server.py
   ```

3. Restart Claude Code (or close the window and open it again). `claude mcp list` should show `mindpersona: ... ✔ Connected`.

## 使用方式

In the Claude Code prompt box, type `/` and pick a persona prompt. Claude Code shows MCP prompts as `/mcp__<server>__<prompt>`:
- `/mcp__mindpersona__mbti-intj` - switch to the INTJ (Architect) persona
- `/mcp__mindpersona__mbti-infp` - switch to the INFP (Mediator) persona
- ... (the other 14 types work the same way)

## 支持的 MBTI 类型

INTJ, INFP, INTP, INFJ, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENTP, ENFJ, ENFP, ESTJ, ESTP, ESFJ, ESFP
