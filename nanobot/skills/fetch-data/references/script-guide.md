# 一次性执行规范（不落盘）

## 强约束

- 默认不要新建 `.py` 文件。
- 默认使用一次性 heredoc 执行：
- 优先使用项目解释器 `./.venv/bin/python`；无虚拟环境时再退回 `python3`。

```bash
./.venv/bin/python - <<'PY'
# your code
PY
```

- 仅当用户明确要求“保存脚本文件”时，才使用 `scripts/fetch_template.py`。

## 通用执行模板

```bash
./.venv/bin/python - <<'PY'
import requests

BASE = "http://10.1.132.21:8001"
PATH = "/api/v1/sources/catalog"
PARAMS = {
    "tag": "leadership",
    "page": 1,
    "page_size": 20,
    "include_facets": True,
}

resp = requests.get(f"{BASE}{PATH}", params=PARAMS, timeout=30)
resp.raise_for_status()
data = resp.json()

items = data.get("items", data if isinstance(data, list) else [])
print("total:", data.get("total", data.get("item_count", len(items))))
for i, it in enumerate(items[:10], 1):
    print(i, it.get("id") or it.get("name"), it.get("dimension"), it.get("is_enabled"))
PY
```

## 展示规则

- 总量 `<= 20`：可全展示。
- 总量 `> 20`：默认展示前 `10` 条，并给出翻页参数建议。
- 优先输出：总量、过滤条件、关键字段摘要；避免直接打印超长原始 JSON。

## 各接口总数字段

- `sources/catalog`：`filtered_sources`（总量）
- `sources`：`len(list)`
- `policy/personnel feed`：`item_count`
- `scholars/students/leadership`：`total`

## 翻页规则

- Feed：`limit + offset`
- 列表：`page + page_size`

## 推荐关键字段

- 信源目录：`id,name,dimension,group,tags,is_enabled,health_status,last_crawl_at`
- 政策：`date,title,source,importance,category,matchScore,sourceUrl`
- 人事：`date,title,source,importance,matchScore,changes`
- 学者：`name,university,department,position,is_academician,email`
- 学生：`name,student_no,home_university,enrollment_year,status,mentor_name`
- 领导：`university_name,source_name,leader_count,new_leader_count,crawled_at`
