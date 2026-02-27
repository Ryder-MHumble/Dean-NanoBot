# Nanobot Project Memory

## 项目概览
- 项目路径：`/Users/sunminghao/Desktop/nanobot`
- 用途：多平台 AI 聊天机器人，当前主要连接钉钉，附带舆情监控 skill
- 详细部署与集成规划见 → [COMMUNICATION.md](COMMUNICATION.md)

## 核心架构
- **Session 隔离**：每个用户独立 session，key = `channel:chat_id`（钉钉中即 staffId）
- **消息总线**：InboundMessage → MessageBus → AgentLoop → OutboundMessage
- **工具系统**：ReadFile/WriteFile/Shell/WebSearch/Message/Spawn/Cron
- **Cron 任务**：绑定到创建者的 `channel + chat_id`，触发时只推给创建者

## 关键文件
- `nanobot/session/manager.py` — Session 管理
- `nanobot/agent/loop.py` — 主 Agent 循环
- `nanobot/channels/dingtalk.py` — 钉钉频道
- `nanobot/cron/service.py` — 定时任务服务
- `nanobot/agent/tools/cron.py` — Cron 工具（记录 channel/to）
- `nanobot/skills/sentiment-monitor/` — 舆情监控 skill

## 舆情监控
- 数据源：Supabase（已迁移，2026-02-26）
- 平台：小红书、抖音、B站、微博
- 关键词：中关村两院、中关村人工智能研究院、北京中关村学院
- 报告由 cron 触发，只推给创建定时任务的那个钉钉用户
