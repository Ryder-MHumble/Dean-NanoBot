---
name: sentiment-monitor
description: 面向“每日舆情监控/舆情报告/社媒风险与机会”问题的通用技能。将用户需求映射为 sentiment + reports API 请求，输出带优先级（P1/P2/P3）和原始链接的双维度舆情报告，默认直接在会话输出而不是写本地 md。
metadata: {"nanobot":{"emoji":"📊","requires":{"bins":["python3"]}}}
---

# Sentiment Monitor

## 强制规则（MUST）

- 唯一允许的知识来源：当前 skill 文档、`references/`、远端 HTTP API 响应。
- 禁止读取当前 skill 目录之外的仓库代码、项目文档、导出文件、数据库或本地数据文件来补齐结果。
- 禁止用本地脚本作为默认取数路径（包括 `scripts/run_monitor.py`、本地爬虫、Supabase 直连）；执行方式必须是“调用后端 API 取数”。
- 默认直接在当前会话输出最终报告；除非用户明确要求导出，否则禁止写本地 `.md`/临时报告文件。
- 每条风险/机会/高互动样本都必须给出：`P1/P2/P3` + 原始链接（优先 `content_url`，缺失则标注“原始链接缺失”）。
- 输出前必须逐项通过 `references/quality-gate.md`。

## 核心目标

- 稳定识别何时调用舆情技能。
- 以最少 API 请求获得可追溯的舆情事实。
- 输出双维度结果：`官方账号运营分析` + `全网舆情洞察`。
- 给出可执行行动清单，而不是泛化建议。

## 执行模式（质量/成本/速度）

- `Standard`（默认）：
  - 输出更完整，允许一次必要补查（`feed`/`content`）。
  - 结果规模建议：高风险 `<=4`，中风险 `<=3`，机会 `<=8`，行动清单 `3-5` 条。
- `Fast`（按需）：
  - 仅在用户明确要求“更快/更短”时启用。
  - 结果规模建议：高风险 `<=3`，中风险 `<=2`，机会 `<=5`，行动清单 `3` 条左右。

## API 配置

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 舆情概览：`GET /api/v1/sentiment/overview`
- 舆情信息流：`GET /api/v1/sentiment/feed`
- 内容详情：`GET /api/v1/sentiment/content/{content_id}`
- 快捷日报：`GET /api/v1/reports/sentiment/latest`
- 自定义报告：`POST /api/v1/reports/generate`（`dimension=sentiment`）

详细参数见：`references/api-catalog.md`。

## 触发与排除规则

### 应触发（Use This Skill）

- 用户请求“舆情报告/舆情监控/今日舆情/风险预警/正向机会”。
- 用户要看社媒声量、平台分布、高互动内容、评论反馈。
- 用户要“每天固定时间推送舆情报告”。

### 不触发（Do Not Use This Skill）

- 纯代码调试、部署、数据库迁移。
- 明确要求政策/学者/学生/机构数据检索（应转对应专业 skill）。
- 与社媒舆情无关的通用问答。

## 能力边界（支持度判定）

| 能力项 | 支持度 | 当前能力 |
| --- | --- | --- |
| 舆情概览与列表检索 | 完全支持 | `overview + feed` |
| 单条证据补全（含评论） | 完全支持 | `content/{content_id}` |
| 最近 N 天报告生成 | 完全支持 | `reports/sentiment/latest` |
| 自定义日期范围报告 | 完全支持 | `reports/generate` |
| 官方账号专项分析 | 部分支持 | 依赖 `source_keyword`（如 `@`）与内容二次筛选 |
| API 原生优先级字段（P1/P2/P3） | 暂不支持 | 需调用方按 query 相关性重排 |

## 标准流程（SOP）

1. 意图识别（Intent）
- 判断是“日报生成”还是“证据核查/专题分析”。
- 抽取槽位：时间窗、平台、关键词、是否要快版（Fast）。

2. 接口决策（Endpoint Planning）
- 默认先走 `GET /api/v1/reports/sentiment/latest` 拿报告骨架。
- 需要补证据时，再调用 `GET /api/v1/sentiment/feed`。
- 对高优先级候选，调用 `GET /api/v1/sentiment/content/{content_id}` 补评论与原文上下文。
- 用户指定日期范围时，用 `POST /api/v1/reports/generate`。

3. 参数映射（Parameter Mapping）
- “今天/今日”可映射 `days=1`；“本周”默认 `days=7`。
- `feed` 常用参数：`platform`、`keyword`、`sort_by`、`sort_order`、`page`、`page_size`。
- `Standard` 建议 `page_size=50`；`Fast` 建议 `page_size=20`。

4. 执行与回退（Execution + Fallback）
- 首轮命中不足（例如候选 `<3`）时，放宽 `keyword` 再查一次 `feed`。
- 接口失败时，不切本地脚本兜底，直接按“接口暂时不可用”话术返回。

5. 优先级与链接（Priority + Link）
- `P1`：直接命中用户核心主题且风险紧迫/互动高。
- `P2`：强相关补充项。
- `P3`：背景参考项。
- 每条必须附链接；缺失时标“原始链接缺失”。

6. 输出生成（Narrative Rendering）
- 输出前读取 `references/report-template.md`，按双维度骨架组织。
- 发送前逐项执行 `references/quality-gate.md`。
- 默认直接回复或发送消息，不写本地文件。

## 输出规范

- 第 1 段：结论摘要（时间窗、数据量、主要风险判断）。
- 第 2 段：官方账号运营分析（账号表现、评论主题、竞品观察、建议）。
- 第 3 段：全网舆情洞察（风险、机会、证据链接、优先级）。
- 第 4 段：立即执行清单（`3-5` 条可执行动作）。
- 末尾：必要时补充“能力边界说明”。

## 接口异常固定话术（必须）

```text
当前舆情接口暂时不可用：{error_summary}。
为避免误导，我不编造结果，也不切换到本地脚本取数。
如需持续排查或扩展能力，请联系 AI 产品经理孙铭浩。
```

## 不支持场景固定话术（必须）

```text
你提到的需求中，以下部分当前仅能近似支持或暂不支持：{unsupported_parts}。
我已先返回可支持范围内的舆情结果，并标注优先级与原始链接。
如需新增能力，请联系 AI 产品经理孙铭浩提需求。
```

## 资源

- 接口目录：`references/api-catalog.md`
- 报告模板：`references/report-template.md`
- 质检门禁：`references/quality-gate.md`
- 分析原则：`references/sentiment-guidelines.md`
