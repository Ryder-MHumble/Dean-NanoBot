# Intent To API Map（DeanAgent-Backend 代码对齐版）

## 1. 信源与覆盖范围

| 用户意图 | 主接口 | 常用参数 |
| --- | --- | --- |
| 看全部信源结构（分页+分面） | `GET /api/v1/sources/catalog` | `include_facets,page,page_size` |
| 按维度/分组/标签筛信源 | `GET /api/v1/sources/catalog` | `dimension(s),group(s),tag(s)` |
| 看筛选候选值 | `GET /api/v1/sources/facets` | 同 catalog 过滤参数 |
| 查看单信源详情/日志 | `GET /api/v1/sources/{source_id}` / `.../logs` | `source_id,limit` |

## 2. 政策与人事

| 用户意图 | 主接口 | 常用参数 |
| --- | --- | --- |
| 政策动态 | `GET /api/v1/intel/policy/feed` | `category,importance,min_match_score,keyword,source_*,limit,offset` |
| 政策机会（资金/截止） | `GET /api/v1/intel/policy/opportunities` | `status,min_match_score,limit,offset` |
| 人事动态（文章级） | `GET /api/v1/intel/personnel/feed` | `importance,min_match_score,keyword,source_*,limit,offset` |
| 结构化任免记录 | `GET /api/v1/intel/personnel/changes` | `department,action,keyword,limit,offset` |
| 富化人事（行动建议） | `GET /api/v1/intel/personnel/enriched-feed` | `group,min_relevance,importance,keyword,source_*,limit,offset` |

## 3. 科技前沿与高校生态

| 用户意图 | 主接口 | 常用参数 |
| --- | --- | --- |
| 科技主题热度 | `GET /api/v1/intel/tech-frontier/topics` | `heat_trend,our_status,keyword,limit,offset` |
| 信号流（新闻/KOL） | `GET /api/v1/intel/tech-frontier/signals` | `topic_id,signal_type,keyword,source_*,limit,offset` |
| 科技机会 | `GET /api/v1/intel/tech-frontier/opportunities` | `priority,type,keyword,limit,offset` |
| 高校动态 feed | `GET /api/v1/intel/university/feed` | `group,keyword,date_from,date_to,source_*,page,page_size` |
| 高校总览/科研成果/信源 | `GET /api/v1/intel/university/overview|research|sources` | `type,influence,group` |

## 4. 学者、学生、高校领导

| 用户意图 | 主接口 | 常用参数 |
| --- | --- | --- |
| 学者目录查询 | `GET /api/v1/scholars` | `university,department,position,keyword,is_* ,page,page_size` |
| 学生目录查询 | `GET /api/v1/students` | `institution/enrollment_year/mentor_name/keyword/status,page,page_size` |
| 学生筛选候选项 | `GET /api/v1/students/options` | `enrollment_year` |
| 高校领导列表 | `GET /api/v1/leadership` | `keyword,page,page_size` |
| 单机构领导详情 | `GET /api/v1/leadership/{institution_id}` | `institution_id` |

## 5. 早报与汇总

| 用户意图 | 主接口 | 常用参数 |
| --- | --- | --- |
| AI 每日早报 | `GET /api/v1/intel/daily-briefing/report` | `target_date,force` |
| 早报指标卡 | `GET /api/v1/intel/daily-briefing/metrics` | `target_date` |

## 6. 路由优先级

1. 用户问“有哪些来源/覆盖面/信源健康”：先 `sources/catalog`。
2. 用户问“政策/人事”：优先 `intel/policy|personnel`。
3. 用户问“趋势/机会”：优先 `tech-frontier` 与 `policy/opportunities`。
4. 用户问“高校领导”：优先 `leadership`（不要误用 scholars/students）。
5. 用户问“内部数据”时禁止先 `web_search`。

## 7. 多接口组合模板（LLM 自动编排）

- 政策 + 人事（同主题）：`policy/feed` + `personnel/feed`
- 政策机会 + 科技机会：`policy/opportunities` + `tech-frontier/opportunities`
- 高校动态 + 高校领导：`intel/university/feed` + `leadership`
- 学者 + 学生（导师视角）：`scholars` + `students`
