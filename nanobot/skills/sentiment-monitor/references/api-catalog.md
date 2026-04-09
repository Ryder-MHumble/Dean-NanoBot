# Sentiment API Catalog（通用版）

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 优先走后端 HTTP API；不依赖本地爬虫、本地脚本产物或 Supabase 直连。
- `GET` 参数走 query string；`POST` 使用 JSON body。
- 含中文的 query 参数值建议 URL 编码；命令行可使用 `curl -G --data-urlencode`。

## 1) 舆情概览

### `GET /api/v1/sentiment/overview`

用途：获取全量舆情概览统计，适合先判断总体声量与平台分布。

参数：
- 无

关键返回字段：
- `total_contents`
- `total_comments`
- `total_engagement`
- `platforms[]`：`platform`, `platform_label`, `content_count`, `total_likes`, `total_comments`, `total_shares`, `total_collected`
- `top_content[]`：`content_id`, `title`, `description`, `content_url`, `platform`, `liked_count`, `comment_count`, `share_count`
- `keywords[]`

## 2) 舆情信息流

### `GET /api/v1/sentiment/feed`

用途：分页获取舆情内容列表，支持平台/关键词过滤和排序。

参数：
- `platform`: 平台过滤（常见值：`xhs` / `dy` / `bili` / `zhihu`）
- `keyword`: 标题/描述/作者关键词
- `sort_by`: `publish_time` / `liked_count` / `comment_count` / `share_count`
- `sort_order`: `asc` / `desc`
- `page`: `>=1`
- `page_size`: `1-100`

关键返回字段：
- `total`, `page`, `page_size`, `total_pages`
- `items[]`：
  - 基础：`content_id`, `platform`, `content_type`, `title`, `description`, `content_url`
  - 作者：`user_id`, `nickname`, `avatar`, `ip_location`
  - 互动：`liked_count`, `comment_count`, `share_count`, `collected_count`
  - 追溯：`source_keyword`, `publish_time`

## 3) 单条内容详情（含评论）

### `GET /api/v1/sentiment/content/{content_id}`

用途：对候选风险/机会条目做证据补全（评论、互动、原文链接）。

参数：
- Path: `content_id`（必填）

关键返回字段：
- 内容主字段：同 `feed.items[]`
- `comments[]`：`comment_id`, `content`, `nickname`, `like_count`, `publish_time`, `parent_comment_id`

## 4) 舆情报告快捷接口

### `GET /api/v1/reports/sentiment/latest`

用途：直接获取最近 N 天舆情报告（默认 markdown）。

参数：
- `days`: `1-30`，默认 `7`
- `output_format`: 默认 `markdown`

关键返回字段：
- `metadata.title`
- `metadata.generated_at`
- `metadata.data_range`
- `metadata.dimension`
- `metadata.total_items`
- `content`
- `format`

## 5) 舆情报告生成接口（自定义日期范围）

### `POST /api/v1/reports/generate`

用途：按自定义时间窗生成舆情报告。

请求体：
- `dimension`: 固定 `sentiment`
- `date_range`: `[start_iso, end_iso]`
- `output_format`: `markdown` / `json` / `html`
- `filters`: 可选对象

关键返回字段：
- `metadata`（同上）
- `content`
- `format`

## 6) 调用顺序建议

1. 日报默认路径：先 `GET /api/v1/reports/sentiment/latest`（`days=1` 或 `7`）。
2. 若需补强可追溯证据：再调用 `GET /api/v1/sentiment/feed` 拉取候选条目。
3. 对高优先级条目（风险/机会）逐条调用 `GET /api/v1/sentiment/content/{content_id}` 补评论证据。
4. 若用户指定时间窗：改走 `POST /api/v1/reports/generate`（`dimension=sentiment` + `date_range`）。
5. 输出前执行 `references/quality-gate.md`，确保 `P1/P2/P3 + 原始链接 + 可执行清单` 完整。

## 7) 能力边界提示

- 当前接口未直接提供 `P1/P2/P3` 字段，优先级需由调用方按 query 相关性重排。
- 若条目缺少 `content_url`，必须显式标注“原始链接缺失”。
- 接口异常（5xx/超时/连接失败）时，应明确“当前舆情接口暂时不可用”，不要伪造成“未命中”。
