# Policy API Catalog（通用版）

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 所有接口均为 `GET` 请求，参数走 query string。
- 含中文的参数值必须做 URL 编码；命令行建议统一使用 `curl -G --data-urlencode`。
- 推荐先查 `feed`，再按意图补查 `opportunities`。

## 1) 政策动态

### `GET /api/v1/intel/policy/feed`

用途：政策信息检索（规则 + LLM 处理后的 feed）。

参数：
- `category`: `国家政策` / `北京政策` / `领导讲话` / `政策机会`
- `importance`: `紧急` / `重要` / `关注` / `一般`
- `min_match_score`: 0-100
- `keyword`: 标题/摘要/来源/标签检索词
- `source_id`: 单信源 ID（精确）
- `source_ids`: 多信源 ID（逗号分隔，精确）
- `source_name`: 单信源名（模糊）
- `source_names`: 多信源名（逗号分隔，模糊）
- `limit`: 1-200
- `offset`: >=0

关键返回字段（用于生成叙事内容）：
- `item_count`
- `items[]`:
  - `title`, `summary`, `category`, `importance`, `date`
  - `source`, `source_id`, `tags`
  - `matchScore`, `relevance`
  - `funding`, `daysLeft`, `leader`
  - `aiInsight`, `detail`, `content`
  - `sourceUrl`

## 2) 政策机会（资金/申报/招商）

### `GET /api/v1/intel/policy/opportunities`

用途：项目申报/招商/资金机会看板；适合“重大项目”“申报机会”类问题。

参数：
- `status`: `urgent` / `active` / `tracking`
- `min_match_score`: 0-100
- `limit`: 1-200
- `offset`: >=0

关键返回字段：
- `item_count`
- `items[]`:
  - `name`, `agency`, `agencyType`
  - `matchScore`, `funding`
  - `deadline`, `daysLeft`, `status`
  - `aiInsight`, `detail`
  - `sourceUrl`

## 3) 统计

### `GET /api/v1/intel/policy/stats`

返回：
- `total_feed_items`
- `total_opportunities`
- `generated_at`

## 4) 调用顺序建议

1. 单主题问答默认先查 `feed`。
2. 涉及“机会/申报/资金/招商”时同时查 `opportunities`。
3. 当 `keyword` 命中低时，执行正文级二次过滤（见 `intent-map.md`）。
4. 输出时优先展示 `sourceUrl` 完整条目，保证可追溯。

## 5) 能力边界提示（对外说明）

- 当前仅保证本文档列出的参数与字段可用。
- 若用户需求依赖未列出字段（如复杂统计口径、跨系统联查），应明确“当前暂不支持”。
- 对“部分支持”场景，先返回可支持结果，再说明缺口并建议联系 AI 产品经理孙铭浩提需求。
- 若接口返回 `5xx`、超时或非法请求错误，应明确说明“当前接口暂时不可用”，不要伪造成“未命中”。
