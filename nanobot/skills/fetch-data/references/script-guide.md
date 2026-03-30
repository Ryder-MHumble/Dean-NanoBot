# 一次性执行规范（Dean 同机部署）

## 执行方式

- 默认不落盘脚本。
- 首选：`./.venv/bin/python - <<'PY'`；无虚拟环境时退回 `python3`。
- 仅用户明确要求保存脚本时，才使用 `scripts/fetch_template.py`。

## 通用模板

```bash
./.venv/bin/python - <<'PY'
import requests

BASE = "http://10.1.132.21:8001"
PATH = "/api/v1/leadership"
PARAMS = {"keyword": "北京大学", "page": 1, "page_size": 20}

resp = requests.get(f"{BASE}{PATH}", params=PARAMS, timeout=30)
resp.raise_for_status()
data = resp.json()

if isinstance(data, list):
    total = len(data)
    items = data
else:
    total = data.get("filtered_sources", data.get("item_count", data.get("total", 0)))
    items = data.get("items", [])

print(f"total={total}")
for i, it in enumerate(items[:10], 1):
    print(i, it)
PY
```

## 展示规则

- `<=20`：可全展示。
- `>20`：默认展示前 10 条，并给翻页建议。
- 回复优先顺序：总量 -> 关键字段摘要 -> 下一步筛选建议。

## 模糊查询执行策略（新增）

- 先生成“查询计划”再请求：
- `intent_list`: 识别 1~3 个子意图
- `param_hypothesis`: 每个意图的默认参数猜测
- `confidence`: 高/中/低

- 置信度为高/中：
- 直接执行首轮查询（可并行多接口）
- 回复里说明“已按默认假设执行”，并给可选精化参数

- 置信度为低：
- 只问 1 个最关键澄清问题
- 不连续追问多轮

示例：
- “北京高校最近值得关注的人事和政策”：
- 并行调用
- `/api/v1/intel/personnel/feed?importance=重要&limit=20`
- `/api/v1/intel/policy/feed?importance=重要&source_name=北京&limit=20`
- 合并输出“政策 + 人事”双栏目摘要

## 总量字段映射

- `sources/catalog`：`filtered_sources`
- `sources`：`len(list)`
- `policy/personnel/tech-frontier`：多数为 `item_count`
- `personnel/enriched-feed`：`total_count`
- `scholars/students/university feed/leadership`：多数为 `total`

## 翻页字段映射

- Feed 风格：`limit + offset`
- 列表风格：`page + page_size`

## 关键字段建议

- `sources/catalog`：`id,name,dimension,group,tags,is_enabled,health_status,last_crawl_at`
- `policy/feed`：`date,title,source,importance,category,matchScore,sourceUrl`
- `policy/opportunities`：`title,source,matchScore,funding,deadline/status,sourceUrl`
- `personnel/feed`：`date,title,source,importance,matchScore,changes`
- `personnel/enriched-feed`：`name/action,importance,relevance,group,actionSuggestion`
- `tech-frontier/topics`：`id,topic,heat_trend,our_status`
- `tech-frontier/signals`：`topic_id,signal_type,title/source,published_at`
- `university/feed`：`published_at,title,source_name,group,url`
- `scholars`：`name,university,department,position,is_academician,email`
- `students`：`name,student_no,home_university,enrollment_year,status,mentor_name`
- `leadership`：`university_name,source_name,leader_count,new_leader_count,crawled_at`

## 快速路由示例

- “北京大学校领导有哪些” -> `/api/v1/leadership?keyword=北京大学`
- “教育部近 20 条政策” -> `/api/v1/intel/policy/feed?source_name=教育部&limit=20`
- “只看需要行动的人事变化” -> `/api/v1/intel/personnel/enriched-feed?group=action&limit=20`
- “看科技前沿 AI Agent 信号” -> `/api/v1/intel/tech-frontier/signals?keyword=AI Agent&limit=20`
