---
name: dean-briefing
description: 每日院长AI早报推送 / Dean's AI Daily Briefing. Fetches structured intelligence data from backend API and delivers a professional DingTalk report covering policy, tech trends, university news, talent dynamics, and events. Preserve backend-provided link order as the priority order, and return the final report directly instead of saving local markdown files. Use when (1) setting up daily 9AM briefing (2) generating today's briefing manually (3) running the dean's briefing
metadata: {"nanobot":{"emoji":"🧠","requires":{"bins":["python3"]}}}
---

# 院长AI早报 (Dean's AI Daily Briefing)

Automated daily intelligence briefing for institute leadership, delivered every morning at 9:00 AM via DingTalk.

## Overview

This skill fetches structured intelligence data from a backend service and delivers a professional, traceable daily briefing to institute leadership via DingTalk.

**Data Modules**:
- **政策情报** (Policy Intel): National and Beijing policy updates
- **科技前沿** (Tech Frontier): AI/tech industry dynamics and funding
- **高校生态** (University Ecosystem): Research breakthroughs, university news
- **人事动态** (Talent Radar): Personnel changes, talent policies
- **智能日程** (Smart Schedule): Upcoming AI conferences and events

## Execution Mode（质量/成本/速度）

- `Standard`（默认）：保持后端段落事实与顺序不变，做极轻量可读性修正（仅标点/断句）。
- `Fast`（按需）：仅在用户明确要求“更快发送”时启用，保持后端段落原样直接发送。

## When to Use

Use this skill when the user asks:
- "发送院长早报" / "Send dean's briefing"
- "生成今天的AI早报" / "Generate today's AI briefing"
- "推送早报" / "Push the morning briefing"
- "设置每天9点早报定时推送" / "Set up daily 9AM briefing"
- "院长早报" / "Dean's briefing"

## Workflow

### 1. Run the script

```bash
python3 nanobot/skills/dean-briefing/scripts/generate_briefing.py
```

The script fetches the API, renders all paragraphs with embedded links, and outputs the final DingTalk Markdown report to stdout.

### 2. Extract the report

Take everything between `GENERATED BRIEFING` and the final `====` separator. That is the complete, ready-to-send message.

**Do NOT re-summarize or re-categorize the paragraphs.** The backend has already written them correctly. Re-writing loses content and creates errors.

The only acceptable touch-up: if a sentence is missing a closing period, add one.

Keep the paragraph order exactly as returned by the backend. Treat that order as the final priority order.

### 3. Send the report

```python
message(content=report, channel="dingtalk", chat_id=chat_id)
```

If the user is asking in the current conversation rather than a push channel, paste the report directly in the reply. Do not save it to a local `.md` file unless the user explicitly asks for export.

Run quality gate validation before sending:

```bash
python3 nanobot/skills/dean-briefing/scripts/validate_intel_report.py --require-priority false --max-chars 6000 --file - <<< "$report_content"
```

If validation fails, revise the report first.

## Cron Integration

### Set up daily briefing at 9 AM:
```python
cron(
    action="add",
    message="发送院长AI早报：从API获取今日情报数据，格式化为钉钉消息并推送",
    cron_expr="0 9 * * *"
)
```

### When cron triggers:
The agent will receive the message and should:
1. Read this SKILL.md
2. Run `generate_briefing.py`
3. Extract the report from stdout
4. Send via message tool

## Error Handling

1. **API unreachable** (`http://10.1.132.21:8001/`): script exits with code 1, check server connectivity
2. **Empty or malformed response**: script reports specific parsing error
3. **`requests` not installed**: run `pip3 install -r requirements.txt`
4. **Quality gate failed**: re-check `references/quality-gate.md`,补齐链接或压缩长度后重发

## Examples

### Example 1: Manual briefing
User: "帮我生成今天的院长早报"

Agent:
1. `python3 nanobot/skills/dean-briefing/scripts/generate_briefing.py`
2. Extract report from stdout
3. Validate quality gate, then send via message tool (or reply directly in chat without creating local report files)

## References

- `references/quality-gate.md` - Final delivery quality gate

### Example 2: Set up daily automation
User: "设置每天早上9点自动推送院长早报"

Agent:
1. `cron(action="add", message="发送院长AI早报：从API获取今日情报数据，格式化为钉钉消息并推送", cron_expr="0 9 * * *")`
2. Confirm job created
