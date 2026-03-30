# OpenClaw API Catalog（fetch-data 专用）

后端地址：`http://10.1.132.21:8001`

说明：
- 以运行中服务返回为准，不写死信源总量。
- 详情路由清单参考 `docs/api/API_REFERENCE.md`（仓库自动生成）。

## 1) 信源目录（首选）

### `GET /api/v1/sources/catalog`
用途：全量信源检索，支持分页 + 分面 + 多维过滤。

查询参数（常用）：
- `dimension`, `dimensions`
- `group`, `groups`
- `tag`, `tags`
- `crawl_method`, `schedule`
- `is_enabled`
- `health_status`, `health_statuses`
- `keyword`
- `sort_by`（默认 `dimension_priority`）、`order`（默认 `asc`）
- `page`（默认 `1`）、`page_size`（默认 `100`）
- `include_facets`（默认 `true`）

关键响应字段：
- `total_sources`, `filtered_sources`, `page`, `total_pages`
- `items[]`: `id,name,dimension,group,tags,is_enabled,health_status,schedule,last_crawl_at`
- `facets`: `dimensions/groups/tags/crawl_methods/schedules/health_statuses`

### `GET /api/v1/sources/facets`
用途：仅取当前筛选条件下的分面统计。
参数：同 catalog 的过滤参数（不含分页排序）。

### `GET /api/v1/sources`
用途：兼容列表接口（已支持多维过滤），返回数组。

### 其他信源控制接口
- `GET /api/v1/sources/{source_id}`
- `GET /api/v1/sources/{source_id}/logs?limit=20`
- `PATCH /api/v1/sources/{source_id}`（启用/禁用）
- `POST /api/v1/sources/{source_id}/trigger`

## 2) 政策与人事 Feed

### `GET /api/v1/intel/policy/feed`
常用参数：
- `category`, `importance`, `min_match_score`, `keyword`
- `source_id/source_ids/source_name/source_names`
- `limit`（默认 `50`）、`offset`（默认 `0`）

关键字段：
- `item_count`, `items[]`
- item 常见字段：`date,title,source,importance,category,matchScore,summary,funding,sourceUrl`

### `GET /api/v1/intel/personnel/feed`
常用参数：
- `importance`, `min_match_score`, `keyword`
- `source_id/source_ids/source_name/source_names`
- `limit`（默认 `50`）、`offset`（默认 `0`）

关键字段：
- `item_count`, `items[]`
- item 常见字段：`date,title,source,importance,matchScore,changes,sourceUrl`

## 3) 学者

### `GET /api/v1/scholars`
常用参数：
- 机构/身份：`university,department,position,region,affiliation_type`
- 标签状态：`is_academician,is_potential_recruit,is_advisor_committee,is_adjunct_supervisor,has_email,is_cobuild_scholar`
- 项目活动：`project_category,project_subcategory,project_categories,project_subcategories,event_types,participated_event_id`
- 搜索：`keyword`
- 分页：`page`（默认 `1`）, `page_size`（默认 `20`）

关键字段：
- `total,page,page_size,total_pages`
- `items[]`: `url_hash,name,university,department,position,academic_titles,is_academician,email,profile_url`

## 4) 学生

### `GET /api/v1/students`
常用参数：
- `institution,grade,enrollment_year,home_university`
- `mentor_name,name,email,student_no,status,keyword`
- `page`（默认 `1`）, `page_size`（默认 `20`）

关键字段：
- `total,page,page_size,total_pages`
- `items[]`: `id,name,student_no,home_university,enrollment_year,status,mentor_name,major,email`

## 5) 高校领导

### `GET /api/v1/leadership`
常用参数：`keyword,page,page_size`

关键字段：
- `total,page,page_size`
- `items[]`: `source_id,institution_id,university_name,source_name,leader_count,new_leader_count,crawled_at,group,dimension,role_counts,source_url`

## 6) 常用组合查询示例

- 高校领导信源：`/api/v1/sources/catalog?tag=leadership`
- 师资信源：`/api/v1/sources/catalog?dimension=scholars`
- 共建导师：`/api/v1/scholars?is_adjunct_supervisor=true`
- 某导师学生：`/api/v1/students?mentor_name=张三&page=1&page_size=20`
