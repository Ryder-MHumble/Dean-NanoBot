# Institution API Catalog（通用版）

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 所有接口均为 `GET` 请求，参数走 query string。
- 含中文的参数值必须做 URL 编码；命令行建议统一使用 `curl -G --data-urlencode`。

## 1) 机构搜索与详情

### `GET /api/v1/institutions/search`

用途：按机构名称做模糊匹配。

参数：
- `q`: 搜索关键词
- `limit`
- `region`
- `org_type`

关键返回字段：
- `query`, `total`
- `results[]`:
  - `id`, `name`, `entity_type`
  - `region`, `org_type`
  - `parent_id`, `scholar_count`

### `GET /api/v1/institutions/suggest`

用途：根据机构名称返回最佳匹配与建议列表。

参数：
- `institution_name`

关键返回字段：
- `matched`
- `suggestions[]`

### `GET /api/v1/institutions`

用途：机构列表与层级结构。

参数：
- `view`: `flat` / `hierarchy`
- `entity_type`
- `region`
- `org_type`
- `classification`
- `sub_classification`
- `keyword`
- `page`, `page_size`
- `is_adjunct_supervisor`

关键返回字段：
- `total`, `page`, `page_size`, `total_pages`
- `items[]`:
  - `id`, `name`
  - `entity_type`, `region`, `org_type`
  - `classification`, `sub_classification`
  - `priority`, `scholar_count`
  - `student_count_total`, `mentor_count`

### `GET /api/v1/institutions/{institution_id}`

用途：机构完整画像。

关键返回字段：
- 基本信息：`id`, `name`, `region`, `org_type`, `classification`, `priority`
- 数量：`student_count_total`, `mentor_count`, `scholar_count`
- 画像：`university_leaders`, `notable_scholars`, `key_departments`
- 合作：`joint_labs`, `training_cooperation`, `academic_cooperation`, `cooperation_focus`
- 层级：`secondary_institutions`
- 记录来源：`sources`

## 2) 机构统计

### `GET /api/v1/institutions/stats`

用途：机构总览统计。

关键返回字段：
- `total_primary_institutions`
- `total_secondary_institutions`
- `total_scholars`
- `by_category[]`
- `by_priority[]`
- `total_students`
- `total_mentors`

### `GET /api/v1/institutions/taxonomy`

用途：机构分类体系统计与导航。

关键返回字段：
- `total`
- `regions`

## 3) 高校动态与文章

### `GET /api/v1/intel/university/feed`

用途：高校动态文章列表。

参数：
- `group`: `university_news` / `ai_institutes`
- `source_id`, `source_ids`
- `source_name`, `source_names`
- `keyword`
- `date_from`, `date_to`
- `page`, `page_size`

关键返回字段：
- `generated_at`, `total`, `page`, `page_size`, `total_pages`
- `items[]`:
  - `id`, `title`, `url`, `published_at`
  - `source_id`, `source_name`, `group`
  - `tags`, `has_content`, `content`

### `GET /api/v1/intel/university/article/{url_hash}`

用途：单篇文章详情。

关键返回字段：
- `id`, `title`, `url`, `published_at`
- `source_name`, `group`, `tags`
- `content`, `images`

## 4) 高校科研成果

### `GET /api/v1/intel/university/research`

用途：科研成果列表。

参数：
- `type`: `论文` / `专利` / `获奖`
- `influence`: `高` / `中` / `低`
- `page`, `page_size`

关键返回字段：
- `generated_at`, `item_count`, `page`, `page_size`, `total_pages`
- `type_stats`
- `items[]`:
  - `title`, `url`, `date`
  - `source_name`, `group`, `institution`
  - `type`, `influence`, `field`, `authors`
  - `aiAnalysis`, `detail`, `matchScore`, `content`

说明：
- 当前没有 `institution` 查询参数；查特定机构科研成果时需做客户端二次过滤，并明确标注为近似方案。

## 5) 调用顺序建议

1. 查具体机构画像时：先 `/suggest`，再 `/{institution_id}`。
2. 查机构分类/层级时：先 `/institutions` 或 `/taxonomy`。
3. 查机构动态时：先 `/intel/university/feed`，必要时再补 `/article/{url_hash}`。
4. 查科研成果时：先 `/intel/university/research`。

## 6) 能力边界提示（对外说明）

- 当前仅保证本文档列出的参数与字段可用。
- `feed` 没有 `institution_id` 参数，特定机构动态通常只能近似筛选。
- `research` 没有 `institution` 参数，特定机构科研成果通常只能近似筛选。
- 若接口返回 `5xx`、超时、`DB client not initialized` 等错误，应明确说明“当前接口暂时不可用”，不要伪造成“未命中”。
