# Scholar API Catalog（通用版）

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 所有接口均为 `GET` 请求，参数走 query string。
- 含中文的参数值必须做 URL 编码；命令行建议统一使用 `curl -G --data-urlencode`。

## 1) 学者列表

### `GET /api/v1/scholars`

用途：学者主检索接口，适合绝大多数学者问答。

参数：
- `university`: 高校名称（模糊匹配）
- `department`: 院系名称（模糊匹配）
- `position`: 职称（精确）
- `is_academician`: 是否院士
- `is_potential_recruit`: 是否潜在招募对象
- `is_advisor_committee`: 是否顾问委员会成员
- `is_adjunct_supervisor`: 是否兼职导师
- `has_email`: 是否有邮箱
- `region`: `国内` / `国际`
- `affiliation_type`: `高校` / `企业（公司）` / `研究机构` / `其他`
- `keyword`: 姓名/英文名/bio/研究方向/关键词检索
- `community_name`, `community_type`
- `project_category`, `project_subcategory`
- `project_categories`, `project_subcategories`
- `event_types`, `participated_event_id`
- `is_cobuild_scholar`
- `institution_group`, `institution_category`
- `custom_field_key`, `custom_field_value`
- `page`, `page_size`

关键返回字段：
- `total`, `page`, `page_size`, `total_pages`
- `items[]`:
  - `url_hash`, `name`, `name_en`
  - `university`, `department`, `position`
  - `academic_titles`, `is_academician`
  - `research_areas`, `email`, `profile_url`
  - `is_potential_recruit`, `is_advisor_committee`
  - `adjunct_supervisor`, `is_cobuild_scholar`
  - `project_tags`, `event_tags`

说明：
- 当前没有 `name` 精确筛选参数；查具体学者时应使用 `keyword=<姓名>` 并结合 `university/department` 做消歧。

## 2) 学者统计

### `GET /api/v1/scholars/stats`

用途：在当前筛选条件下返回统计总览。

参数：
- 与 `/api/v1/scholars` 基本一致。

关键返回字段：
- `total`
- `academicians`
- `potential_recruits`
- `advisor_committee`
- `adjunct_supervisors`
- `by_university[]`
- `by_department[]`
- `by_position[]`

## 3) 学者详情

### `GET /api/v1/scholars/{url_hash}`

用途：拉取单位学者完整档案。

关键返回字段：
- 基本信息：`name`, `university`, `department`, `position`
- 研究信息：`research_areas`, `keywords`, `bio`, `bio_en`
- 联系方式：`email`, `phone`, `office`
- 链接：`profile_url`, `lab_url`, `google_scholar_url`, `dblp_url`, `orcid`
- 成果：`representative_publications`, `patents`, `awards`
- 与两院关系：`is_advisor_committee`, `adjunct_supervisor`, `joint_research_projects`, `joint_management_roles`
- 标签：`project_tags`, `event_tags`
- 动态：`recent_updates`
- 其他：`supervised_students_count`, `custom_fields`

## 4) 导师指导学生

### `GET /api/v1/scholars/{url_hash}/students`

用途：查询指定导师下的指导学生记录。

关键返回字段：
- `total`
- `faculty_url_hash`
- `items[]`
  - `id`, `name`, `student_no`
  - `home_university`, `enrollment_year`
  - `status`, `major`

## 5) 调用顺序建议

1. 学者问答默认先查 `/scholars`。
2. 需要总量或分布时再补 `/scholars/stats`。
3. 需要简介、成果、联系方式、与两院关系时补 `/scholars/{url_hash}`。
4. 需要导师学生关系时，在唯一学者确定后再调 `/students`。

## 6) 能力边界提示（对外说明）

- 当前仅保证本文档列出的参数与字段可用。
- 原始主页链接依赖 `profile_url` 是否存在；没有则只能返回无链接条目。
- 若接口返回 `5xx`、超时或非法请求错误，应明确说明“当前接口暂时不可用”，不要伪造成“未命中”。
