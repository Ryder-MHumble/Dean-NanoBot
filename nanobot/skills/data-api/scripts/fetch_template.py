"""
中关村人工智能研究院 — 数据 API 通用脚本模板

修改「配置区」中的 API_ENDPOINT 和 params 后直接运行。

依赖：pip install requests
Python：3.8+
"""

import requests
from datetime import datetime

BASE_URL = "http://43.98.254.243:8001"

# ═══════════════════════════════════════════════════════════
# 配置区：修改这里切换 API 和过滤条件
# ═══════════════════════════════════════════════════════════

API_ENDPOINT = "/api/v1/sentiment/feed"    # 替换为目标 API 路径

# ── 可用 API 端点 ──────────────────────────────────────────
# /api/v1/sources/                    信源列表（不需要 params）
# /api/v1/intel/policy/feed           政策动态
# /api/v1/intel/personnel/feed        人事动态
# /api/v1/intel/university/feed       高校动态
# /api/v1/sentiment/feed              社媒内容信息流
# /api/v1/faculty/                    师资列表

params = {
    # ── 社媒 feed 参数 ────────────────────────────────────
    "platform": "xhs",            # xhs=小红书 / dy=抖音 / bilibili / weibo（不填=全部）
    "keyword": "中关村人工智能",
    "sort_by": "liked_count",     # publish_time / liked_count / comment_count / share_count
    "sort_order": "desc",
    "page": 1,
    "page_size": 20,

    # ── 政策/人事 feed 参数 ───────────────────────────────
    # "source_name": "教育部",      # 模糊匹配信源名
    # "keyword": "人工智能",
    # "importance": "重要",         # 紧急/重要/关注/一般
    # "limit": 20,
    # "offset": 0,

    # ── 高校 feed 参数 ────────────────────────────────────
    # "source_name": "清华大学",
    # "group": "ai_institutes",    # university_news/ai_institutes/awards/provincial
    # "date_from": "2026-01-01",
    # "date_to": "2026-03-01",
    # "page": 1,
    # "page_size": 20,

    # ── 师资列表参数 ──────────────────────────────────────
    # "university": "清华",
    # "position": "教授",           # 教授/副教授/研究员/助理教授
    # "keyword": "自然语言处理",
    # "is_academician": True,
    # "has_email": True,
    # "page": 1,
    # "page_size": 20,
}

# ═══════════════════════════════════════════════════════════
# 展示函数（无需修改）
# ═══════════════════════════════════════════════════════════

PLATFORM_LABEL = {"xhs": "小红书", "dy": "抖音", "bilibili": "哔哩哔哩", "weibo": "微博"}


def _ts_to_date(ts, platform="xhs"):
    if not ts:
        return "N/A"
    try:
        secs = ts / 1000 if platform == "xhs" else ts
        return datetime.fromtimestamp(secs).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


def display_sources(data):
    items = data if isinstance(data, list) else data.get("items", [])
    print(f"共 {len(items)} 个信源\n")
    for item in items:
        status = "✓" if item.get("is_enabled") else "✗"
        print(f"[{status}] {item['id']} | {item['name']} | {item.get('dimension','')} | {item.get('schedule','')}")


def display_policy(data):
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
        print(f"\n... 还有 {total-10} 条，调整 offset 获取更多")


def display_personnel(data):
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


def display_university(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    print(f"共 {total} 条高校动态（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        pub = (item.get("published_at") or "N/A").split("T")[0]
        print(f"\n[{i}] {pub} | {item.get('source_name','')}")
        print(f"    {item.get('title','')}")
        print(f"    {item.get('url','N/A')}")
    if total > 20:
        print(f"\n... 共 {total} 条，调整 page 获取更多")


def display_sentiment(data):
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
        print(f"\n... 共 {total} 条，调整 page 获取更多")


def display_faculty(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    print(f"共 {total} 位学者（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(items[:10] if total > 20 else items, 1):
        titles = "、".join(item.get("academic_titles", []))
        areas = "、".join(item.get("research_areas", [])[:3])
        academician = " 【院士】" if item.get("is_academician") else ""
        print(f"\n{'━'*50}")
        print(f"[{i}] {item.get('name','')}{academician} ({item.get('name_en','')})")
        print(f"    {item.get('university','')} · {item.get('department','')} · {item.get('position','')}")
        if titles:
            print(f"    头衔：{titles}")
        if areas:
            print(f"    研究方向：{areas}")
        if item.get("email"):
            print(f"    邮箱：{item['email']}")
        print(f"    主页：{item.get('profile_url','N/A')}")
    if total > 20:
        print(f"\n... 共 {total} 位，调整 page 获取更多")


DISPLAY_MAP = {
    "/api/v1/sources/":                      display_sources,
    "/api/v1/intel/policy/feed":             display_policy,
    "/api/v1/intel/personnel/feed":          display_personnel,
    "/api/v1/intel/university/feed":         display_university,
    "/api/v1/sentiment/feed":                display_sentiment,
    "/api/v1/faculty/":                      display_faculty,
}

# ═══════════════════════════════════════════════════════════
# 执行
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    url = f"{BASE_URL}{API_ENDPOINT}"
    print(f"请求：GET {url}")
    print(f"参数：{params}\n")

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        print("连接失败：请检查后端服务是否可达（http://43.98.254.243:8001）")
        raise SystemExit(1)
    except requests.exceptions.HTTPError as e:
        print(f"请求失败：HTTP {e.response.status_code}")
        print(e.response.text[:300])
        raise SystemExit(1)

    display_fn = DISPLAY_MAP.get(API_ENDPOINT)
    if display_fn:
        display_fn(data)
    else:
        import json
        print(json.dumps(data, ensure_ascii=False, indent=2))
