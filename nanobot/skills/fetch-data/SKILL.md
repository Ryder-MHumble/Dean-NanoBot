---
name: fetch-data
description: Use when users ask for Dean backend data from /api/v1. Route intent to the correct endpoint set (sources/intel/scholars/students/leadership), execute one-shot queries, and return concise structured results with pagination guidance.
---
# Dean Fetch Data Skill

## 背景（必须理解）

- Nanobot 与后端服务部署在同一台服务器。
- 后端项目目录：`/home/ubuntu/workspace/DeanAgent-Backend`
- 后端基址：`http://10.1.132.21:8001`
- 后端真实能力以代码和 OpenAPI 为准：
- `DeanAgent-Backend/app/api/v1/router.py`
- `DeanAgent-Backend/app/api/v1/intel/router.py`
- `DeanAgent-Backend/app/api/v1/*.py`
- `DeanAgent-Backend/openapi.json`

## 强约束

- 内部数据问题优先走后端 API，不先用 `web_search`。
- 仅当内部 API 明确无结果或不可用时，才允许外部搜索，并说明原因。
- 默认一次性执行查询（python heredoc 或 curl），不要落盘新脚本。
- 只有用户明确要求“保存脚本”时，才使用 `scripts/fetch_template.py`。

## LLM 查询规划层（让用户少描述）

当用户描述模糊时，先做“查询规划”再调用 API：

1. 意图拆解（可多意图并存）
- 示例：“北大最近有什么政策和领导变化” -> `policy/feed` + `leadership`

2. 参数自动补全（不强依赖用户精确输入）
- 机构别名归一：`北大 -> 北京大学`，`清华 -> 清华大学`
- 时间词归一：
- “最近/近期” -> 默认近 30 天（若接口无时间参数，保留为排序/分页策略）
- “本周/本月” -> 对应日期区间
- 重要性词归一：
- “紧急/高优/重点” -> `importance=紧急|重要`
- 主题词映射：
- “机会/申报/资金”优先补路由到 `policy/opportunities`
- “行动建议/怎么跟进”优先补路由到 `personnel/enriched-feed`

3. 多接口编排
- 先并行拉取候选数据，再在回复层聚合：
- 并行：互不依赖（如 `policy/feed` 与 `leadership`）
- 串行：有依赖（如先 `sources/catalog` 再按 `source_id` 拉 feed）

4. 低置信度才追问
- 若参数缺失不影响首轮结果：先查再给“可选精化建议”
- 若缺失会导致歧义严重（如机构名不明确）：只追问 1 个关键问题

## 分层路由策略（按用户意图）

1. 信源覆盖/筛选面板：
- `GET /api/v1/sources/catalog`（首选）
- `GET /api/v1/sources/facets`（需要候选值时）

2. 政策情报：
- 动态列表：`GET /api/v1/intel/policy/feed`
- 机会看板：`GET /api/v1/intel/policy/opportunities`
- 汇总统计：`GET /api/v1/intel/policy/stats`

3. 人事情报：
- 文章级动态：`GET /api/v1/intel/personnel/feed`
- 结构化任免：`GET /api/v1/intel/personnel/changes`
- LLM 富化动态：`GET /api/v1/intel/personnel/enriched-feed`
- 统计：`GET /api/v1/intel/personnel/stats` / `.../enriched-stats`

4. 科技前沿：
- `GET /api/v1/intel/tech-frontier/topics`
- `GET /api/v1/intel/tech-frontier/signals`
- `GET /api/v1/intel/tech-frontier/opportunities`
- `GET /api/v1/intel/tech-frontier/stats`

5. 高校生态：
- `GET /api/v1/intel/university/feed`
- `GET /api/v1/intel/university/overview`
- `GET /api/v1/intel/university/research`
- `GET /api/v1/intel/university/sources`

6. 学者与学生：
- `GET /api/v1/scholars`
- `GET /api/v1/students`
- `GET /api/v1/students/options`

7. 高校领导：
- 列表：`GET /api/v1/leadership`
- 全量：`GET /api/v1/leadership/all`
- 单机构：`GET /api/v1/leadership/{institution_id}`

8. 每日简报：
- `GET /api/v1/intel/daily-briefing/report`
- `GET /api/v1/intel/daily-briefing/metrics`

## 执行流程

1. 先读 `references/intent-map.md` 定路由。
2. 再读 `references/api-catalog.md` 确认参数与字段。
3. 按 `references/script-guide.md` 一次性执行请求。
4. 输出“总量 + 前 N 条 + 翻页建议 + 下一步可选过滤”。

## 参数抽取要点

- 来源过滤：`source_id/source_ids/source_name/source_names`
- 目录过滤：`dimension(s),group(s),tag(s),health_status(es),is_enabled`
- 匹配阈值：`min_match_score`（政策/人事）或 `min_relevance`（富化人事）
- 翻页：
- feed 类：`limit/offset`
- list 类：`page/page_size`

## 参考文件

- 路由映射：`references/intent-map.md`
- 接口参数：`references/api-catalog.md`
- 执行与展示：`references/script-guide.md`
- 信源专项：`references/sources.md`
