# Python 脚本生成规范

## 脚本基本结构

```python
import requests
from datetime import datetime

BASE_URL = "http://43.98.254.243:8001"

params = { ... }  # 根据用户需求填写

resp = requests.get(f"{BASE_URL}/api/v1/<endpoint>", params=params)
resp.raise_for_status()
data = resp.json()

_display(data)
```

---

## 展示规则

- 结果总数 ≤ 20 条：逐条完整展示
- 结果总数 > 20 条：统计摘要 + 前 10 条详情

总数字段因 API 而异：
- Policy / Personnel / Sentiment overview：`item_count`（对应返回条数，`limit` 控制）
- University feed / Faculty：`total`（全部匹配数）
- Sentiment feed：`total`

---

## 各 API 展示函数

### 1. 政策动态

```python
def _display(data):
    items = data.get("items", [])
    total = data.get("item_count", len(items))
    print(f"共 {total} 条政策数据（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        print(f"\n{'━'*50}")
        print(f"[{i}] {item.get('date','N/A')} | {item.get('importance','')} | {item.get('source','')}")
        print(f"    标题：{item['title']}")
        if item.get("summary"):
            s = item["summary"]
            print(f"    摘要：{s[:120]}{'...' if len(s) > 120 else ''}")
        if item.get("funding"):
            print(f"    资金：{item['funding']}")
        if item.get("daysLeft") is not None:
            print(f"    距截止：{item['daysLeft']} 天")
        print(f"    链接：{item.get('sourceUrl','N/A')}")
    if total > 20:
        print(f"\n... 还有 {total-10} 条，请调整 offset 参数获取更多")
```

### 2. 人事动态

```python
def _display(data):
    items = data.get("items", [])
    total = data.get("item_count", len(items))
    print(f"共 {total} 条人事动态（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        print(f"\n{'━'*50}")
        print(f"[{i}] {item.get('date','N/A')} | {item.get('source','')} | {item.get('importance','')}")
        print(f"    标题：{item['title']}")
        for c in item.get("changes", []):
            print(f"    ▸ {c.get('action','')}：{c.get('name','')} → {c.get('position','')}（{c.get('department','')}）")
        print(f"    链接：{item.get('sourceUrl','N/A')}")
    if total > 20:
        print(f"\n... 还有 {total-10} 条，调整 offset 获取更多")
```

### 3. 高校动态

```python
def _display(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    print(f"共 {total} 条高校动态（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        pub = (item.get("published_at") or "N/A").split("T")[0]
        print(f"\n[{i}] {pub} | {item.get('source_name','')}")
        print(f"    {item.get('title','')}")
        print(f"    {item.get('url','N/A')}")
    if total > 20:
        print(f"\n... 共 {total} 条，调整 page 参数获取更多")
```

### 4. 社媒内容信息流

```python
def _ts_to_date(ts, platform):
    """时间戳转日期字符串（xhs 毫秒，dy 秒）"""
    if not ts:
        return "N/A"
    try:
        secs = ts / 1000 if platform == "xhs" else ts
        return datetime.fromtimestamp(secs).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)

PLATFORM_LABEL = {"xhs": "小红书", "dy": "抖音", "bilibili": "哔哩哔哩", "weibo": "微博"}

def _display(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    print(f"共 {total} 条社媒内容（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        platform = item.get("platform", "")
        pub = _ts_to_date(item.get("publish_time"), platform)
        print(f"\n{'━'*50}")
        print(f"[{i}] [{PLATFORM_LABEL.get(platform, platform)}] {pub} | @{item.get('nickname','')} | {item.get('ip_location','')}")
        print(f"    标题：{item.get('title','（无标题）')}")
        desc = item.get("description", "")
        if desc:
            print(f"    内容：{desc[:100]}{'...' if len(desc) > 100 else ''}")
        print(f"    互动：点赞 {item.get('liked_count',0)} | 评论 {item.get('comment_count',0)} | 分享 {item.get('share_count',0)} | 收藏 {item.get('collected_count',0)}")
        if item.get("source_keyword"):
            print(f"    关键词：{item['source_keyword']}")
        print(f"    链接：{item.get('content_url','N/A')}")
    if total > 20:
        print(f"\n... 共 {total} 条，调整 page 参数获取更多")
```

### 5. 师资列表

```python
def _display(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    print(f"共 {total} 位学者（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        titles = "、".join(item.get("academic_titles", []))
        areas = "、".join(item.get("research_areas", [])[:3])
        academician = " 【院士】" if item.get("is_academician") else ""
        print(f"\n{'━'*50}")
        print(f"[{i}] {item.get('name','')} ({item.get('name_en','')}){academician}")
        print(f"    {item.get('university','')} · {item.get('department','')} · {item.get('position','')}")
        if titles:
            print(f"    头衔：{titles}")
        if areas:
            print(f"    研究方向：{areas}")
        if item.get("email"):
            print(f"    邮箱：{item['email']}")
        print(f"    主页：{item.get('profile_url','N/A')}")
    if total > 20:
        print(f"\n... 共 {total} 位，调整 page 参数获取更多")
```

---

## 参数填写指南

| 用户表述 | 对应参数 |
|---------|---------|
| 「教育部的政策」 | `source_name="教育部"` （政策 feed）|
| 「北京教育局相关」 | `source_name="北京市教委"` （政策 feed）|
| 「小红书上的舆情」 | `platform="xhs"` （社媒 feed）|
| 「所有平台的舆情」 | 不传 `platform`（社媒 feed）|
| 「关于中关村的内容」 | `keyword="中关村"` |
| 「清华的教授」 | `university="清华"`, `position="教授"` （师资）|
| 「AI 方向的研究员」 | `keyword="人工智能"`, `position="研究员"` （师资）|
| 「只看院士」 | `is_academician=true` （师资）|
| 「有联系方式的」 | `has_email=true` （师资）|
| 「最近一个月」 | `date_from="2026-02-01"` （高校 feed）|
| 「按热度排序」 | `sort_by="liked_count"` （社媒 feed）|

---

## 完整示例：社媒舆情脚本

```python
import requests
from datetime import datetime

BASE_URL = "http://43.98.254.243:8001"

params = {
    "platform": "xhs",        # 小红书
    "keyword": "中关村人工智能",
    "sort_by": "liked_count",
    "sort_order": "desc",
    "page": 1,
    "page_size": 20,
}

resp = requests.get(f"{BASE_URL}/api/v1/sentiment/feed", params=params)
resp.raise_for_status()
data = resp.json()

items = data.get("items", [])
total = data.get("total", len(items))

print(f"共 {total} 条小红书内容（{'全部展示' if total <= 20 else '展示前10条'}）\n")
show = items if total <= 20 else items[:10]

for i, item in enumerate(show, 1):
    ts = item.get("publish_time")
    try:
        pub = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M") if ts else "N/A"
    except Exception:
        pub = "N/A"
    print(f"{'━'*50}")
    print(f"[{i}] {pub} | @{item.get('nickname','')} | {item.get('ip_location','')}")
    print(f"    标题：{item.get('title','（无标题）')}")
    desc = item.get("description", "")
    if desc:
        print(f"    内容：{desc[:100]}{'...' if len(desc) > 100 else ''}")
    print(f"    互动：点赞 {item.get('liked_count',0)} | 评论 {item.get('comment_count',0)} | 收藏 {item.get('collected_count',0)}")
    print(f"    链接：{item.get('content_url','N/A')}\n")

if total > 20:
    print(f"... 还有 {total-10} 条，调整 page 参数获取更多")
```
