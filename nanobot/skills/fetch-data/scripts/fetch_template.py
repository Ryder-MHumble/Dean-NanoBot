"""
中关村人工智能研究院 — 数据 API 模板（仅在用户明确要求保存脚本时使用）

默认推荐一次性执行（heredoc），不要落盘新脚本。
本文件仅作为显式“保存脚本”请求的兜底模板。

依赖：pip install requests
Python：3.8+
"""

import json
import requests

BASE_URL = "http://10.1.132.21:8001"

# ═══════════════════════════════════════════════════════════
# 配置区：修改这里切换 API 和过滤条件
# ═══════════════════════════════════════════════════════════

API_ENDPOINT = "/api/v1/sources/catalog"  # 替换为目标 API 路径

# ── 可用 API 端点 ──────────────────────────────────────────
# /api/v1/sources                     信源兼容列表（数组）
# /api/v1/sources/catalog             信源目录（分页+分面）
# /api/v1/sources/facets              信源分面
# /api/v1/intel/policy/feed           政策动态
# /api/v1/intel/personnel/feed        人事动态
# /api/v1/scholars                    学者列表
# /api/v1/students                    学生列表
# /api/v1/leadership                  高校领导列表

params = {
    # ── 信源目录参数（/api/v1/sources/catalog） ──────────────
    "tag": "leadership",
    "page": 1,
    "page_size": 20,
    "include_facets": True,

    # ── 信源兼容列表参数（/api/v1/sources） ─────────────────
    # "dimension": "technology",
    # "is_enabled": True,
    # "health_status": "failing",

    # ── 学者列表参数（/api/v1/scholars） ─────────────────────
    # "university": "清华",
    # "department": "计算机",
    # "position": "教授",
    # "is_academician": True,
    # "is_potential_recruit": True,
    # "has_email": True,
    # "keyword": "人工智能",

    # ── 学生列表参数（/api/v1/students） ─────────────────────
    # "institution": "清华",
    # "enrollment_year": "2024",
    # "mentor_name": "张三",
    # "status": "在读",
    # "page": 1,
    # "page_size": 20,

    # ── 政策/人事 feed 参数 ──────────────────────────────────
    # "category": "国家政策",      # 仅政策 feed 使用
    # "importance": "重要",        # 紧急/重要/关注/一般
    # "min_match_score": 80,       # 0-100
    # "keyword": "人工智能",
    # "source_name": "教育部",
    # "limit": 20,
    # "offset": 0,

    # ── 高校领导列表参数（/api/v1/leadership） ───────────────
    # "keyword": "北大",
    # "page": 1,
    # "page_size": 20,

}

# ═══════════════════════════════════════════════════════════
# 展示函数（通常无需修改）
# ═══════════════════════════════════════════════════════════


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    if endpoint != "/":
        endpoint = endpoint.rstrip("/")
    return endpoint


def _truncate(text: str, max_len: int = 120) -> str:
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "..."


def _display_sources(data):
    items = data if isinstance(data, list) else data.get("items", [])
    print(f"共 {len(items)} 个信源")
    for item in items:
        status = "启用" if item.get("is_enabled") else "停用"
        print(
            f"- {item.get('id', '')} | {item.get('name', '')} | "
            f"{item.get('dimension', '')} | {status} | {item.get('schedule', '')}"
        )


def _display_sources_catalog(data):
    items = data.get("items", [])
    total = data.get("filtered_sources", len(items))
    page = data.get("page", 1)
    total_pages = data.get("total_pages", 1)
    print(f"共 {total} 个信源（第 {page}/{total_pages} 页）")
    for item in items[:20]:
        status = "启用" if item.get("is_enabled") else "停用"
        tags = ",".join(item.get("tags", [])[:3]) if item.get("tags") else ""
        print(
            f"- {item.get('id', '')} | {item.get('name', '')} | {item.get('dimension', '')}"
            f" | {item.get('group', '')} | {status} | {item.get('health_status', '')}"
            f" | {tags}"
        )

    facets = data.get("facets") or {}
    if facets.get("dimensions"):
        print("\n维度分面（前 10）：")
        for facet in facets["dimensions"][:10]:
            print(
                f"  - {facet.get('key', '')}: {facet.get('count', 0)}"
                f" (enabled={facet.get('enabled_count', 0)})"
            )


def _display_source_facets(data):
    print("信源分面：")
    for key in [
        "dimensions",
        "groups",
        "tags",
        "crawl_methods",
        "schedules",
        "health_statuses",
    ]:
        items = data.get(key, [])
        print(f"\n[{key}] top {min(10, len(items))}")
        for item in items[:10]:
            if key == "dimensions":
                print(
                    f"  - {item.get('key', '')}: {item.get('count', 0)}"
                    f" (enabled={item.get('enabled_count', 0)})"
                )
            else:
                print(f"  - {item.get('key', '')}: {item.get('count', 0)}")


def _display_policy(data):
    items = data.get("items", [])
    total = data.get("item_count", len(items))
    show = items if total <= 20 else items[:10]

    print(f"共 {total} 条政策动态（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(show, 1):
        print(f"\n[{i}] {item.get('date', 'N/A')} | {item.get('importance', '')} | {item.get('source', '')}")
        print(f"    标题：{item.get('title', '')}")
        if item.get("category"):
            print(f"    分类：{item['category']}")
        if item.get("matchScore") is not None:
            print(f"    匹配度：{item['matchScore']}")
        if item.get("summary"):
            print(f"    摘要：{_truncate(item['summary'])}")
        if item.get("funding"):
            print(f"    资金：{item['funding']}")
        print(f"    链接：{item.get('sourceUrl', item.get('source_url', 'N/A'))}")

    if total > 20:
        print("\n... 请调整 offset 获取更多")


def _display_personnel(data):
    items = data.get("items", [])
    total = data.get("item_count", len(items))
    show = items if total <= 20 else items[:10]

    print(f"共 {total} 条人事动态（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(show, 1):
        print(f"\n[{i}] {item.get('date', 'N/A')} | {item.get('importance', '')} | {item.get('source', '')}")
        print(f"    标题：{item.get('title', '')}")
        if item.get("matchScore") is not None:
            print(f"    匹配度：{item['matchScore']}")
        for change in item.get("changes", []):
            if isinstance(change, dict):
                print(
                    f"    ▸ {change.get('action', '')}：{change.get('name', '')} -> "
                    f"{change.get('position', '')}（{change.get('department', '')}）"
                )
            else:
                print(f"    ▸ {change}")
        print(f"    链接：{item.get('sourceUrl', item.get('source_url', 'N/A'))}")

    if total > 20:
        print("\n... 请调整 offset 获取更多")


def _display_scholars(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    show = items if total <= 20 else items[:10]

    print(f"共 {total} 位学者（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(show, 1):
        titles = "、".join(item.get("academic_titles", []) or [])
        tags = []
        if item.get("is_academician"):
            tags.append("院士")
        if item.get("is_potential_recruit"):
            tags.append("潜在引进")
        tag_txt = f" [{' / '.join(tags)}]" if tags else ""

        print(f"\n[{i}] {item.get('name', '')}{tag_txt} ({item.get('name_en', '')})")
        print(
            f"    {item.get('university', '')} · {item.get('department', '')} · "
            f"{item.get('position', '')}"
        )
        if titles:
            print(f"    头衔：{titles}")
        if item.get("research_areas"):
            print(f"    研究方向：{'、'.join((item.get('research_areas') or [])[:3])}")
        if item.get("email"):
            print(f"    邮箱：{item['email']}")
        if item.get("profile_url"):
            print(f"    主页：{item['profile_url']}")

    if total > 20:
        print("\n... 请调整 page 获取更多")


def _display_students(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    show = items if total <= 20 else items[:10]

    print(f"共 {total} 位学生（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(show, 1):
        print(f"\n[{i}] {item.get('name', '')} | 学号：{item.get('student_no', '')}")
        print(
            f"    学校：{item.get('home_university', '')} | 入学：{item.get('enrollment_year', '')} "
            f"| 状态：{item.get('status', '')}"
        )
        print(f"    导师：{item.get('mentor_name', '')} | 专业：{item.get('major', '')}")
        if item.get("email"):
            print(f"    邮箱：{item['email']}")
        if item.get("phone"):
            print(f"    电话：{item['phone']}")

    if total > 20:
        print("\n... 请调整 page 获取更多")


def _display_leadership(data):
    items = data.get("items", [])
    total = data.get("total", len(items))
    show = items if total <= 20 else items[:10]

    print(f"共 {total} 条高校领导数据（{'全部展示' if total <= 20 else '展示前10条'}）")
    for i, item in enumerate(show, 1):
        print(f"\n[{i}] {item.get('university_name', '')} | {item.get('source_name', '')}")
        print(
            f"    领导总数：{item.get('leader_count', 0)} | "
            f"新增：{item.get('new_leader_count', 0)}"
        )
        print(
            f"    抓取时间：{item.get('crawled_at', 'N/A')} | "
            f"分组：{item.get('group', '')} | 维度：{item.get('dimension', '')}"
        )
        role_counts = item.get("role_counts") or {}
        if role_counts:
            role_text = ", ".join(f"{k}:{v}" for k, v in role_counts.items())
            print(f"    角色分布：{role_text}")
        if item.get("source_url"):
            print(f"    链接：{item['source_url']}")

    if total > 20:
        print("\n... 请调整 page 获取更多")


DISPLAY_MAP = {
    "/api/v1/sources": _display_sources,
    "/api/v1/sources/catalog": _display_sources_catalog,
    "/api/v1/sources/facets": _display_source_facets,
    "/api/v1/intel/policy/feed": _display_policy,
    "/api/v1/intel/personnel/feed": _display_personnel,
    "/api/v1/scholars": _display_scholars,
    "/api/v1/students": _display_students,
    "/api/v1/leadership": _display_leadership,
}


if __name__ == "__main__":
    endpoint = _normalize_endpoint(API_ENDPOINT)
    url = f"{BASE_URL}{endpoint}"

    print(f"请求：GET {url}")
    print(f"参数：{params}\n")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.ConnectionError:
        print("连接失败：请检查后端服务是否可达（http://10.1.132.21:8001/）")
        raise SystemExit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"请求失败：HTTP {exc.response.status_code}")
        print(exc.response.text[:500])
        raise SystemExit(1)
    except requests.exceptions.RequestException as exc:
        print(f"请求失败：{exc}")
        raise SystemExit(1)

    display_fn = DISPLAY_MAP.get(endpoint)
    if display_fn:
        display_fn(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
