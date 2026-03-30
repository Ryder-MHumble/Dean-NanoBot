# DeanAgent API Catalog（代码对齐）

后端基址：`http://10.1.132.21:8001`
后端项目：`/home/ubuntu/workspace/DeanAgent-Backend`

说明：
- 以 `app/api/v1/*.py` 与运行时 OpenAPI 为准。
- 本文只列 agent 高频查询接口。

## A. 信源体系

### `GET /api/v1/sources/catalog`（首选）
用途：信源全景检索（分页 + 分面）。

常用参数：
- 过滤：`dimension(s),group(s),tag(s),crawl_method,schedule,is_enabled,health_status(es),keyword`
- 排序：`sort_by,order`
- 分页：`page,page_size`
- 分面：`include_facets`

关键字段：
- `total_sources, filtered_sources, page, total_pages`
- `items[]`：`id,name,dimension,group,tags,is_enabled,health_status,schedule,last_crawl_at`
- `facets`：`dimensions/groups/tags/...`

### `GET /api/v1/sources/facets`
用途：只获取分面候选值。

### `GET /api/v1/sources`
用途：兼容简单列表（数组）。

### 其他常用
- `GET /api/v1/sources/{source_id}`
- `GET /api/v1/sources/{source_id}/logs?limit=20`

## B. 政策与人事

### `GET /api/v1/intel/policy/feed`
参数：`category,importance,min_match_score,keyword,source_*,limit,offset`

关键字段：
- `item_count`
- `items[]`: `date,title,source,importance,category,matchScore,summary,funding,sourceUrl`

### `GET /api/v1/intel/policy/opportunities`
参数：`status,min_match_score,limit,offset`

关键字段（常见）：
- `item_count`
- `items[]`: `title,source,matchScore,funding,deadline/status,sourceUrl`

### `GET /api/v1/intel/personnel/feed`
参数：`importance,min_match_score,keyword,source_*,limit,offset`

关键字段：
- `item_count`
- `items[]`: `date,title,source,importance,matchScore,changes,sourceUrl`

### `GET /api/v1/intel/personnel/changes`
参数：`department,action,keyword,limit,offset`

关键字段：
- `item_count`
- `items[]`: `name,action,position,department,date,source`

### `GET /api/v1/intel/personnel/enriched-feed`
参数：`group,importance,min_relevance,keyword,source_*,limit,offset`

关键字段（常见）：
- `total_count`（以及 `action_count/watch_count`）
- `items[]`: `relevance,group,actionSuggestion,background,aiInsight,...`

## C. 科技前沿

### `GET /api/v1/intel/tech-frontier/topics`
参数：`heat_trend,our_status,keyword,limit,offset`

### `GET /api/v1/intel/tech-frontier/signals`
参数：`topic_id,signal_type,keyword,source_*,limit,offset`

### `GET /api/v1/intel/tech-frontier/opportunities`
参数：`priority,type,keyword,limit,offset`

### `GET /api/v1/intel/tech-frontier/stats`
参数：无

## D. 高校生态

### `GET /api/v1/intel/university/feed`
参数：`group,source_*,keyword,date_from,date_to,page,page_size`

关键字段：
- `total,page,page_size,total_pages`
- `items[]`: `title,url,published_at,source_name,group,url_hash`

### `GET /api/v1/intel/university/overview`
### `GET /api/v1/intel/university/research`
参数（research）：`type,influence,page,page_size`

### `GET /api/v1/intel/university/sources`
参数：`group`

## E. 学者、学生、高校领导

### `GET /api/v1/scholars`
参数（高频）：
- 机构筛选：`university,department,position`
- 标记筛选：`is_academician,is_potential_recruit,is_adjunct_supervisor,has_email,is_cobuild_scholar`
- 搜索：`keyword`
- 分页：`page,page_size`

关键字段：`total,page,page_size,total_pages,items[]`

### `GET /api/v1/students`
参数：`institution|home_university,grade|enrollment_year,mentor_name,name,email,student_no,status,keyword,page,page_size`

关键字段：`total,page,page_size,total_pages,items[]`

### `GET /api/v1/students/options`
参数：`enrollment_year`
用途：获取年级/高校/导师筛选候选值。

### `GET /api/v1/leadership`
参数：`keyword,page,page_size`

### `GET /api/v1/leadership/all`
参数：`keyword`

### `GET /api/v1/leadership/{institution_id}`
用途：单机构高校领导详情。

## F. 每日简报

### `GET /api/v1/intel/daily-briefing/report`
参数：`target_date,force`

### `GET /api/v1/intel/daily-briefing/metrics`
参数：`target_date`
