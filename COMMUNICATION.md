# Nanobot 服务器部署 & Dean-Agent 集成规划

更新时间：2026-02-26

## 背景

计划将 nanobot 部署到服务器上，并与 **Dean-Agent 系统**的数据打通，
目标是让舆情数据、对话数据等在两个系统之间共享和流通。

## 当前已知架构特性

### Session 机制
- 每个用户独立 session（key = `dingtalk:<staffId>`）
- Session 文件存储在服务器的 `~/.nanobot/sessions/` 目录
- 10 个用户 = 10 个独立 session 文件，互不干扰

### 消息推送机制
- Cron 定时任务绑定到创建者的 staffId
- 舆情报告**不会**自动广播给所有用户
- 如需多人接收，每人须单独创建 cron 任务，或需要扩展"广播"能力

### 数据存储
- 舆情数据：Supabase（云端，已支持远程访问）
- Session 历史：本地 JSONL 文件（部署到服务器后存服务器本地）
- Cron 任务：本地 JSON 文件（`~/.nanobot/cron.json`）

## 待解决的能力缺口（与 Dean-Agent 打通所需）

### 数据层
- [ ] Session 历史数据持久化到 Supabase（当前仅存本地文件）
- [ ] 统一数据模型：nanobot 对话记录 ↔ Dean-Agent 数据结构
- [ ] 舆情报告结果写入共享数据库（当前仅输出到终端/钉钉消息）

### 消息推送层
- [ ] 实现"广播"能力：一次推送给多个指定钉钉用户
- [ ] 推送目标列表配置化（而非依赖每人手动创建 cron）
- [ ] 支持群消息推送（当前只支持私聊）

### 集成层
- [ ] nanobot → Dean-Agent 的数据输出接口（API 或共享 DB）
- [ ] Dean-Agent → nanobot 的触发接口（Webhook 或消息队列）
- [ ] 统一身份认证（钉钉 staffId ↔ Dean-Agent 用户 ID 的映射）

### 部署层
- [ ] Docker 化部署（项目已有 Dockerfile）
- [ ] 环境变量管理（钉钉 client_id/secret、Supabase key 等敏感配置）
- [ ] 服务监控与自动重启
