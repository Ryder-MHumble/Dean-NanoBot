# Intent To API Map（OpenClaw 2026-03）

## 1. 信源与覆盖

| 用户意图 | 主接口 | 典型参数 |
| --- | --- | --- |
| 看全部信源与状态 | `GET /api/v1/sources/catalog` | `include_facets=true,page_size=200` |
| 按维度/分组/标签筛信源 | `GET /api/v1/sources/catalog` | `dimension(s),group(s),tag(s)` |
| 看可选筛选项（维度/分组/标签） | `GET /api/v1/sources/facets` | 同 catalog 过滤参数 |
| 看某个信源详情/日志 | `GET /api/v1/sources/{source_id}` / `.../logs` | `source_id,limit` |

## 2. 政策与人事动态

| 用户意图 | 主接口 | 典型参数 |
| --- | --- | --- |
| 看政策动态/政策机会线索 | `GET /api/v1/intel/policy/feed` | `category,importance,min_match_score,keyword,limit,offset` |
| 看人事任免/领导变动 | `GET /api/v1/intel/personnel/feed` | `importance,min_match_score,keyword,limit,offset` |
| 限定来源 | `policy/personnel feed` | `source_id/source_ids/source_name/source_names` |

## 3. 学者与学生

| 用户意图 | 主接口 | 典型参数 |
| --- | --- | --- |
| 查学者目录 | `GET /api/v1/scholars` | `university,department,position,keyword,page,page_size` |
| 查院士/共建导师/潜在引进 | `GET /api/v1/scholars` | `is_academician,is_adjunct_supervisor,is_potential_recruit` |
| 查学生目录 | `GET /api/v1/students` | `institution,mentor_name,enrollment_year,status,keyword` |

## 4. 高校领导

| 用户意图 | 主接口 | 典型参数 |
| --- | --- | --- |
| 拉高校领导模块数据 | `GET /api/v1/leadership` | `keyword,page,page_size` |

## 5. 路由优先级

1. 先问“覆盖面/有哪些信源”：优先 `sources/catalog`。
2. 问“政策、人事动态”：优先 `intel/*/feed`。
3. 问“学者/导师/学生”：优先 `scholars` 或 `students`。
4. 问“高校领导列表”：优先 `leadership`。
