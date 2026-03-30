#!/usr/bin/env python3
"""
院长AI早报生成脚本

从后台服务获取每日情报简报数据，解析结构化JSON并格式化为
钉钉Markdown消息，供 nanobot agent 进行二次LLM润色后推送。

API: http://10.1.132.21:8001//api/v1/intel/daily-briefing/report
"""

import json
import sys
import os
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ 缺少依赖: requests", file=sys.stderr)
    print("   请运行: pip3 install requests", file=sys.stderr)
    sys.exit(1)

API_URL = "http://10.1.132.21:8001//api/v1/intel/daily-briefing/report"

# Module ID to Chinese name mapping
MODULE_NAMES = {
    "policy-intel":    "政策情报",
    "tech-frontier":   "科技前沿",
    "university-eco":  "高校生态",
    "talent-radar":    "人事动态",
    "smart-schedule":  "智能日程",
}


def fetch_briefing_data() -> dict:
    """从 Intel API 获取当日早报数据。"""
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    if "date" not in data or "paragraphs" not in data:
        raise ValueError("API 返回数据结构不完整，缺少 date 或 paragraphs 字段")
    return data


def render_paragraph(parts: list) -> str:
    """
    将混合段落（字符串 + 链接对象）渲染为 DingTalk Markdown 文本。

    parts 中每个元素可以是：
    - str: 直接拼接
    - dict: {"text": "...", "url": "https://...", "sourceName": "..."}
            有 url 时渲染为 [text](url)，否则渲染为 text
    """
    result = []
    for part in parts:
        if isinstance(part, str):
            result.append(part)
        elif isinstance(part, dict):
            text = part.get("text", "")
            url = part.get("url", "")
            if url:
                result.append(f"[{text}]({url})")
            elif text:
                result.append(text)
    return "".join(result).strip()


def format_metric_cards(metric_cards: list) -> str:
    """将数据概览卡片格式化为钉钉列表。"""
    if not metric_cards:
        return ""
    lines = ["### 📊 数据总览", ""]
    for card in metric_cards:
        title = card.get("title", "")
        metrics = card.get("metrics", [])
        metric_parts = []
        for m in metrics:
            label = m.get("label", "")
            value = m.get("value", "")
            if label and value:
                metric_parts.append(f"{label}: **{value}**")
        if metric_parts:
            lines.append(f"- **{title}** — " + " | ".join(metric_parts))
    return "\n".join(lines)


def format_paragraphs(paragraphs: list) -> str:
    """将段落数组格式化为今日要报正文。"""
    if not paragraphs:
        return "### 📰 今日要报\n\n暂无内容"
    lines = ["### 📰 今日要报", ""]
    for para_parts in paragraphs:
        rendered = render_paragraph(para_parts)
        if rendered:
            lines.append(rendered)
            lines.append("")
    return "\n".join(lines).rstrip()


def generate_dingtalk_report(data: dict) -> str:
    """将 API 返回的 JSON 数据格式化为钉钉 Markdown 早报。"""
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    summary = data.get("summary", "")
    article_count = data.get("article_count", 0)
    paragraphs = data.get("paragraphs", [])

    sections = []

    # ── 标题 ──────────────────────────────────────────
    sections.append(f"## 🧠 院长AI早报 · {date_str}")
    sections.append("")
    sections.append(f"> 今日监测 **{article_count}** 篇资讯")
    if summary:
        sections.append(f"> {summary}")
    sections.append("")
    sections.append("---")
    sections.append("")

    # ── 正文段落（忠实还原，不重新归类）─────────────────
    for para_parts in paragraphs:
        rendered = render_paragraph(para_parts)
        if rendered:
            sections.append(rendered)
            sections.append("")

    sections.append("---")
    sections.append(f"*Nanobot 院长AI早报 · 每日09:00自动推送*")

    return "\n".join(sections)


def main():
    print("=" * 60)
    print("🧠 院长AI早报生成系统")
    print("=" * 60)

    # Step 1: 获取数据
    print("📡 正在从API获取早报数据...")
    try:
        data = fetch_briefing_data()
        date = data.get("date", "unknown")
        count = data.get("article_count", 0)
        paragraphs_count = len(data.get("paragraphs", []))
        print(f"✅ 数据获取成功")
        print(f"   日期: {date}")
        print(f"   文章总数: {count}")
        print(f"   段落数: {paragraphs_count}")
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败: 无法连接到 43.98.254.243:8001", file=sys.stderr)
        print("   请检查服务器是否正常运行", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ API请求失败: HTTP {e.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ 请求超时: API响应时间超过30秒", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ 数据格式错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 获取数据时发生未知错误: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: 格式化
    print("\n📝 正在格式化为钉钉Markdown...")
    try:
        report = generate_dingtalk_report(data)
        char_count = len(report)
        print(f"✅ 格式化完成 (字符数: {char_count})")
        if char_count > 4000:
            print(f"⚠️  内容较长 ({char_count} 字符)，LLM润色时请适当精简")
    except Exception as e:
        print(f"❌ 格式化失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 3: 输出报告（供 nanobot agent 读取并进行LLM润色）
    print("\n" + "=" * 60)
    print("GENERATED BRIEFING")
    print("=" * 60 + "\n")
    print(report)

    print("\n" + "=" * 60)
    print("✅ 院长AI早报生成完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  已中断", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
