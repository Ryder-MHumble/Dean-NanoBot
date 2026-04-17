#!/usr/bin/env python3
"""
Optimized Report Generator for Sentiment Monitoring - V3.0

双维度报告：
1. 官方账号运营分析 — 官方账号帖子表现、评论主题、竞品账号对比
2. 全网舆情洞察    — 声量总览、关键风险（附链接）、正向机会、立即执行清单

设计原则：
- 少即是多：只展示有决策价值的内容
- 每个发现必须附"所以呢"：具体可执行行动
- 避免空话：不写"加强内容运营"这类通用建议
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

MODE_CONFIGS: Dict[str, Dict[str, int]] = {
    "fast": {
        "high_risk_limit": 3,
        "medium_risk_limit": 2,
        "risk_title_chars": 60,
        "risk_keywords_per_item": 3,
        "checklist_limit": 5,
        "checklist_high_risk_limit": 2,
        "checklist_medium_risk_limit": 1,
        "benchmark_case_limit": 2,
        "benchmark_action_limit": 2,
    },
    "standard": {
        "high_risk_limit": 4,
        "medium_risk_limit": 3,
        "risk_title_chars": 80,
        "risk_keywords_per_item": 4,
        "checklist_limit": 6,
        "checklist_high_risk_limit": 3,
        "checklist_medium_risk_limit": 2,
        "benchmark_case_limit": 4,
        "benchmark_action_limit": 3,
    },
}


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_sentiment_emoji(sentiment: str) -> str:
    emojis = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}
    return emojis.get(sentiment, "⚪")


def format_number(num) -> str:
    num = int(num) if num else 0
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)


def get_platform_name(platform: str) -> str:
    config = load_config()
    return config.get("platform_names_cn", {}).get(platform, platform)


def get_rank_priority(index: int) -> str:
    """Convert a 1-based rank into a stable P1/P2/P3 priority label."""
    if index <= 1:
        return "P1"
    if index <= 3:
        return "P2"
    return "P3"


def get_risk_priority(severity: str) -> str:
    """Map risk severity to a user-facing priority label."""
    if severity == "high":
        return "P1"
    if severity == "medium":
        return "P2"
    return "P3"


def normalize_mode(mode: str) -> str:
    normalized = (mode or "standard").strip().lower()
    if normalized not in MODE_CONFIGS:
        return "standard"
    return normalized


def format_publish_time(item: Dict[str, Any]) -> str:
    raw_ts = item.get("publish_time") or item.get("created_at") or 0
    if not raw_ts:
        return "时间缺失"
    ts = float(raw_ts)
    if ts > 10_000_000_000:
        ts /= 1000
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def get_institution_label(item: Dict[str, Any], group: str = "primary_entities") -> str:
    matches = item.get("entity_match", {}).get(group, [])
    if not matches:
        return "机构待确认"
    return " / ".join(match["display_name"] for match in matches)


def get_relevance_reason(item: Dict[str, Any]) -> str:
    reason = item.get("entity_match", {}).get("relevance_reason", "")
    return reason or "仅命中弱相关别名，已转人工复核"


def get_action_suggestions(risk_type: str, config: Dict[str, Any]) -> List[str]:
    templates = config.get("risk_action_templates", {})
    return templates.get(risk_type, templates.get("待研判", []))


# ============================================================
# Part 1: 官方账号运营分析
# ============================================================

def generate_account_report(
    account_analysis: Dict,
    fullvolume_analysis: Optional[Dict] = None,
    mode: str = "standard",
) -> str:
    """生成维度一：官方账号运营分析"""
    mode_config = MODE_CONFIGS[normalize_mode(mode)]
    total_posts = account_analysis.get("total_posts", 0)
    total_comments = account_analysis.get("total_comments", 0)
    accounts = account_analysis.get("accounts", [])

    if total_posts == 0:
        return """## 一、官方账号运营分析

> 暂无官方账号数据（数据库中尚无 source_keyword 以 @ 开头的内容）

---

"""

    sections = []
    sections.append("## 一、官方账号运营分析\n")
    sections.append(f"> 数据来源：官方账号爬取数据 | 共 {total_posts} 条帖子 / {total_comments} 条评论\n\n")

    # 1.1 账号概览表
    sections.append("### 1.1 账号概览\n\n")
    sections.append("| 账号 | 平台 | 帖子数 | 总互动量 | 平均互动 | 正面占比 |\n")
    sections.append("|------|------|--------|----------|----------|----------|\n")

    accounts_sorted = sorted(accounts, key=lambda x: x["total_engagement"], reverse=True)
    for acc in accounts_sorted:
        post_count = acc["post_count"]
        total_eng = acc["total_engagement"]
        avg_eng = acc["avg_engagement"]
        sentiment_dist = acc["sentiment_dist"]
        total_sent = sum(sentiment_dist.values()) or 1
        positive_pct = round(sentiment_dist.get("positive", 0) / total_sent * 100)
        platform_name = get_platform_name(acc["platform"])
        sections.append(
            f"| {acc['account']} | {platform_name} | {post_count} | "
            f"{format_number(total_eng)} | {format_number(avg_eng)} | {positive_pct}% |\n"
        )
    sections.append("\n")

    # 1.2 各账号 TOP 帖子
    sections.append("### 1.2 高互动帖子\n\n")
    for acc in accounts_sorted:
        top_posts = acc.get("top_posts", [])
        if not top_posts:
            continue
        sections.append(f"**{acc['account']}**\n\n")
        for i, post in enumerate(top_posts[:mode_config["account_top_posts_per_account"]], 1):
            priority = get_rank_priority(i)
            eng = sum(post["engagement"].values())
            title = post["title"][:50] if post["title"] else post["content"][:50]
            sentiment = post["sentiment"]["label"]
            sent_emoji = get_sentiment_emoji(sentiment)
            sent_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}.get(sentiment, sentiment)
            parts = []
            for k, v in post["engagement"].items():
                if v:
                    label_map = {"likes": "赞", "comments": "评", "shares": "转", "collects": "藏", "views": "播"}
                    parts.append(f"{v}{label_map.get(k, k)}")
            eng_str = " + ".join(parts) + f" = **{format_number(eng)}**" if parts else format_number(eng)
            sections.append(f"{i}. [{priority}] 《{title}》\n")
            sections.append(f"   - 互动：{eng_str} | 情感：{sent_emoji} {sent_cn}\n")
            if post.get("url"):
                sections.append(f"   - 原始链接：[查看原文]({post['url']})\n")
            else:
                sections.append("   - 原始链接：原始链接缺失（需回源补录）\n")
            sections.append("\n")

    # 1.3 评论主题洞察
    comment_themes = account_analysis.get("comment_themes", [])
    if comment_themes:
        sections.append("### 1.3 评论主题洞察\n\n")
        sections.append("用户评论中最高频的关键词及代表性评论：\n\n")
        for theme in comment_themes:
            kw = theme["keyword"]
            count = theme["count"]
            sent_emoji = get_sentiment_emoji(theme["sentiment"])
            sections.append(f"- {sent_emoji} **#{kw}** ({count} 次) ")
            top_comment = theme.get("top_comment", {})
            if top_comment.get("text"):
                author = top_comment.get("author", "")
                sections.append(f"— 代表评论：「{top_comment['text']}」")
                if author:
                    sections.append(f" —{author}")
            sections.append("\n")
        sections.append("\n")

    # 1.4 竞品账号对比
    sections.append(_generate_account_competitor_comparison(accounts_sorted))

    # 1.5 运营建议
    sections.append(
        _generate_account_recommendations(
            accounts_sorted,
            comment_themes,
            account_analysis,
            fullvolume_analysis,
            mode_config,
        )
    )

    sections.append("---\n\n")
    return "".join(sections)


def _generate_account_competitor_comparison(accounts: List[Dict]) -> str:
    """账号维度：竞品账号横向对比"""
    if len(accounts) < 2:
        return ""

    section = "### 1.4 竞品账号对比\n\n"
    section += "| 账号 | 帖子数 | 总互动量 | 平均互动 | 正面占比 | 评论数 |\n"
    section += "|------|--------|----------|----------|----------|--------|\n"
    for acc in accounts:
        sd = acc["sentiment_dist"]
        total_sent = sum(sd.values()) or 1
        pos_pct = round(sd.get("positive", 0) / total_sent * 100)
        section += (
            f"| {acc['account']} | {acc['post_count']} | "
            f"{format_number(acc['total_engagement'])} | "
            f"{format_number(acc['avg_engagement'])} | "
            f"{pos_pct}% | {acc['comment_count']} |\n"
        )
    section += "\n"

    # 简单对比洞察
    if len(accounts) >= 2:
        best = accounts[0]
        others = accounts[1:]
        if others:
            our_avg = best["avg_engagement"]
            competitor_avg = max(a["avg_engagement"] for a in others)
            if our_avg >= competitor_avg:
                section += f"✅ **{best['account']}** 平均互动（{format_number(our_avg)}）高于其他账号，内容表现领先。\n\n"
            else:
                gap_acc = max(others, key=lambda x: x["avg_engagement"])
                section += (
                    f"⚠️ **{gap_acc['account']}** 平均互动（{format_number(gap_acc['avg_engagement'])}）"
                    f"高于 **{best['account']}**（{format_number(our_avg)}），"
                    f"建议研究其高互动内容的选题和形式。\n\n"
                )
    return section


def _generate_account_recommendations(
    accounts: List[Dict],
    comment_themes: List[Dict],
    account_analysis: Dict,
    fullvolume_analysis: Optional[Dict] = None,
    mode_config: Optional[Dict[str, int]] = None,
) -> str:
    """账号维度：选题建议 + 运营行动建议（有理有据，具体可执行）"""
    if mode_config is None:
        mode_config = MODE_CONFIGS["standard"]
    section = "### 1.5 内容运营建议\n\n"

    # 所有账号帖子按互动量排序
    all_top_posts: List[Dict] = []
    for acc in accounts:
        all_top_posts.extend(acc.get("top_posts", []))
    all_top_posts.sort(key=lambda x: sum(x["engagement"].values()), reverse=True)

    # ── 一、基于数据的选题建议 ────────────────────────────────
    topic_suggestions: List[str] = []

    # 1) 从全网趋势话题中找选题机会
    if fullvolume_analysis:
        fv_topics = fullvolume_analysis.get("topics", [])
        # 只取正面/中性、互动量高的话题，负面话题不适合主动蹭
        good_topics = [
            t for t in fv_topics
            if t["sentiment"] in ("positive", "neutral") and t["count"] >= 2
        ]
        good_topics.sort(key=lambda x: x["avg_engagement"], reverse=True)
        for t in good_topics[:mode_config["topic_from_trends_limit"]]:
            topic = t["topic"]
            cnt = t["count"]
            avg_eng = format_number(int(t["avg_engagement"]))
            sent_emoji = get_sentiment_emoji(t["sentiment"])
            topic_suggestions.append(
                f"- {get_rank_priority(len(topic_suggestions) + 1)} | 📌 **选题：#{topic}** — 全网已有 {cnt} 篇相关内容，平均互动 {avg_eng}，"
                f"情感以 {sent_emoji} 为主。建议本周在官方账号发布一条关于「{topic}」的内容，"
                f"借势当前讨论热度。"
            )

    # 2) 从竞品账号高互动帖子中提炼选题角度
    if fullvolume_analysis and len(accounts) >= 2:
        competitor_accounts = accounts[1:]  # 排除第一个（假设是我方账号）
        for comp_acc in competitor_accounts[:mode_config["topic_from_competitor_limit"]]:
            comp_top = comp_acc.get("top_posts", [])
            if comp_top:
                best = comp_top[0]
                eng = sum(best["engagement"].values())
                title = best["title"][:30] if best["title"] else best["content"][:30]
                url_part = (
                    f" | 原始链接：[参考]({best['url']})"
                    if best.get("url")
                    else " | 原始链接：原始链接缺失"
                )
                topic_suggestions.append(
                    f"- {get_rank_priority(len(topic_suggestions) + 1)} | 📌 **借鉴竞品选题**：{comp_acc['account']} 的《{title}》"
                    f"获得 {format_number(eng)} 互动{url_part}。"
                    f"可参考其角度，结合我方特色发布差异化内容。"
                )

    # 3) 自身历史高互动内容 → 延伸系列
    if all_top_posts:
        top = all_top_posts[0]
        eng = sum(top["engagement"].values())
        title = top["title"][:30] if top["title"] else top["content"][:30]
        url_part = (
            f" | 原始链接：[原文]({top['url']})"
            if top.get("url")
            else " | 原始链接：原始链接缺失"
        )
        topic_suggestions.append(
            f"- {get_rank_priority(len(topic_suggestions) + 1)} | 📌 **延伸爆款内容**：《{title}》是近期互动最高的帖子（{format_number(eng)}）{url_part}。"
            f"分析其话题切入角度和内容结构，本周发布一条延续性内容（Part 2 / 相关话题）。"
        )

    # 4) 基于正面评论主题 → 用户喜欢什么就多发什么
    positive_themes = [t for t in comment_themes if t["sentiment"] == "positive"]
    if positive_themes:
        kws = "、".join(f"「{t['keyword']}」" for t in positive_themes[:2])
        top_comment_text = ""
        if positive_themes[0].get("top_comment", {}).get("text"):
            top_comment_text = f"（用户说：「{positive_themes[0]['top_comment']['text'][:40]}...」）"
        topic_suggestions.append(
            f"- {get_rank_priority(len(topic_suggestions) + 1)} | 📌 **放大用户认可点**：评论中 {kws} 出现频率高{top_comment_text}，"
            f"说明用户对这类内容反应积极。建议专门围绕这些话题策划 1-2 篇内容。"
        )

    if topic_suggestions:
        section += "**本周选题建议（有数据支撑）**\n\n"
        section += "\n".join(topic_suggestions[:mode_config["topic_suggestions_limit"]])
        section += "\n\n"

    # ── 二、执行层面建议 ─────────────────────────────────────
    section += "**执行层面**\n\n"
    exec_actions: List[str] = []

    # 负面评论需要回应
    negative_themes = [t for t in comment_themes if t["sentiment"] == "negative"]
    if negative_themes:
        kws = "、".join(f"「{t['keyword']}」" for t in negative_themes[:2])
        exec_actions.append(
            f"- 🎯 **回应用户疑虑**：评论中多次出现 {kws}，发布一条专门解答这些疑虑的内容，"
            f"或在评论区直接回复相关用户。"
        )

    # 低互动账号
    low_acc = [a for a in accounts if a["avg_engagement"] < 100 and a["post_count"] > 0]
    if low_acc:
        acc_name = low_acc[0]["account"]
        exec_actions.append(
            f"- 🎯 **提升 {acc_name} 互动率**：平均互动低于 100，"
            f"下次发布时在结尾加一个问题引导评论（如「你有没有类似经历？」）。"
        )

    # 竞品领先提示
    if len(accounts) >= 2:
        our = accounts[0]
        competitor = max(accounts[1:], key=lambda x: x["avg_engagement"])
        if competitor["avg_engagement"] > our["avg_engagement"]:
            exec_actions.append(
                f"- 🎯 **追赶 {competitor['account']}**："
                f"其平均互动（{format_number(competitor['avg_engagement'])}）"
                f"高于我方（{format_number(our['avg_engagement'])}），"
                f"本周抽 30 分钟研究其近期 3 条高互动帖的选题逻辑。"
            )

    # 回复评论
    if account_analysis.get("total_comments", 0) > 0:
        exec_actions.append(
            "- 🎯 **回复评论**：本周至少回复 5 条用户评论（优先选高赞评论），"
            "有助于提升账号权重和用户黏性。"
        )

    if exec_actions:
        section += "\n".join(exec_actions[:mode_config["exec_actions_limit"]])
        section += "\n\n"

    if not topic_suggestions and not exec_actions:
        section += "暂无足够数据生成具体建议，请在数据积累后重新运行报告。\n\n"

    return section


# ============================================================
# Part 2: 全网舆情洞察
# ============================================================

def generate_fullvolume_report(fullvolume_analysis: Dict, mode: str = "standard") -> str:
    """生成维度二：全网舆情洞察"""
    normalized_mode = normalize_mode(mode)
    mode_config = MODE_CONFIGS[normalized_mode]
    metrics = fullvolume_analysis.get("metrics", {})
    total_items = metrics.get("total_items", 0)

    if total_items == 0:
        return """## 二、全网舆情洞察

> 暂无全网关键词数据。

---

"""

    sections = []
    sections.append("## 二、全网舆情洞察\n")

    metadata = fullvolume_analysis.get("metadata", {})
    data_date = metadata.get("data_date", "全量数据")
    sections.append(f"> 数据来源：关键词搜索数据 | 数据范围：{data_date} | 共 {total_items} 条\n\n")

    # 2.1 声量总览（简表）
    sections.append(_generate_volume_overview(fullvolume_analysis))

    # 2.2 关键风险
    sections.append(_generate_focused_risks(fullvolume_analysis, mode_config))

    # 2.3 正向机会
    sections.append(_generate_opportunities(fullvolume_analysis, mode_config))

    # 2.4 立即执行清单
    sections.append(_generate_action_checklist(fullvolume_analysis, mode_config))

    sections.append("---\n\n")
    sections.append(
        f"*本报告由 Nanobot 舆情监控系统自动生成 | 双维度模板 v3.0 | 模式：{normalized_mode} | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    )
    return "".join(sections)


def _generate_volume_overview(analysis: Dict) -> str:
    """2.1 声量总览"""
    metrics = analysis["metrics"]
    sentiment_pct = metrics["sentiment_pct"]
    platform_dist = metrics.get("platform_dist", {})
    comments_data = analysis.get("comments_analysis", {})
    total_comments = comments_data.get("total_comments", 0)

    section = "### 2.1 声量总览\n\n"
    section += (
        f"| 维度 | 数据 |\n"
        f"|------|------|\n"
        f"| 总帖子数 | {metrics['total_items']} 条 |\n"
        f"| 总评论数 | {total_comments} 条 |\n"
        f"| 总互动量 | {format_number(metrics['total_engagement'])} |\n"
        f"| 情感分布 | 🟢 {sentiment_pct.get('positive',0)}% 正面 / "
        f"🟡 {sentiment_pct.get('neutral',0)}% 中性 / "
        f"🔴 {sentiment_pct.get('negative',0)}% 负面 |\n"
    )

    # 平台分布
    if platform_dist:
        platform_str = " / ".join(
            f"{get_platform_name(p)} {c}条" for p, c in platform_dist.items()
        )
        section += f"| 平台分布 | {platform_str} |\n"

    section += "\n"
    return section


def _generate_focused_risks(analysis: Dict, mode_config: Dict[str, int]) -> str:
    """2.2 关键风险（仅有价值的，附回应建议）"""
    risks = analysis.get("risks", [])
    high = [r for r in risks if r["severity"] == "high"]
    medium = [r for r in risks if r["severity"] == "medium"]

    if not risks:
        return "### 2.2 关键风险\n\n✅ **当前无风险预警**，所有监测内容未发现需要关注的风险项。\n\n"

    section = "### 2.2 关键风险\n\n"

    def format_risk(risk: Dict, idx: int, priority: str) -> str:
        item = risk["item"]
        title_chars = mode_config["risk_title_chars"]
        title = item["title"][:title_chars] if item["title"] else item["content"][:title_chars]
        eng = sum(item["engagement"].values())
        platform = get_platform_name(item["platform"])
        author = item["author"]["name"]
        keywords = "、".join(risk["keywords"][:mode_config["risk_keywords_per_item"]])
        color = "🔴" if priority == "high" else "🟡"
        label = get_risk_priority(priority)
        text = f"#### {label} / {color} 风险{idx}：{keywords}\n\n"
        text += f"> 《{title}》\n\n"
        text += f"- 📱 平台：{platform} | 👤 作者：{author} | 📊 互动：{format_number(eng)}\n"
        if item.get("url"):
            text += f"- 原始链接：[查看原文]({item['url']})\n"
        else:
            text += "- 原始链接：原始链接缺失（需回源补录）\n"
        text += f"\n**回应建议**：\n"
        # 根据关键词类型给出具体建议
        complaint_kws = {"投诉", "举报", "骗局", "欺骗", "违规", "虚假"}
        if any(kw in risk["keywords"] for kw in complaint_kws):
            text += (
                "- 48 小时内：评估内容真实性，准备官方澄清；\n"
                "- 若情况属实：直接联系作者私信道歉并说明改进计划；\n"
                "- 若情况不实：发布简洁声明，附事实证据，避免扩大化。\n"
            )
        else:
            text += (
                "- 本周内：在帖子下方留下官方回复，正面回应具体疑虑；\n"
                "- 避免沉默：未回应比回应差，即使只是「感谢反馈，我们在关注」。\n"
            )
        text += "\n"
        return text

    if high:
        section += "**高优先级（48小时内处理）**\n\n"
        for i, r in enumerate(high[:mode_config["high_risk_limit"]], 1):
            section += format_risk(r, i, "high")

    if medium:
        section += "**中优先级（本周内关注）**\n\n"
        for i, r in enumerate(medium[:mode_config["medium_risk_limit"]], 1):
            section += format_risk(r, i, "medium")

    return section


def _generate_opportunities(analysis: Dict, mode_config: Dict[str, int]) -> str:
    """2.3 正向机会：可借势放大的高互动正面内容"""
    all_items = analysis.get("all_items", [])
    positive_items = [
        item for item in all_items
        if item["sentiment"]["label"] == "positive"
    ]

    if not positive_items:
        return "### 2.3 正向机会\n\n当前暂无高互动正面内容可借势。\n\n"

    positive_items.sort(key=lambda x: sum(x["engagement"].values()), reverse=True)
    top_items = positive_items[:mode_config["opportunity_limit"]]

    section = "### 2.3 正向机会\n\n"
    section += "以下高互动正面内容可转发/借势放大：\n\n"

    for i, item in enumerate(top_items, 1):
        priority = get_rank_priority(i)
        eng = sum(item["engagement"].values())
        title_chars = mode_config["opportunity_title_chars"]
        title = item["title"][:title_chars] if item["title"] else item["content"][:title_chars]
        platform = get_platform_name(item["platform"])
        author = item["author"]["name"]

        section += f"{i}. [{priority}] **《{title}》** — {format_number(eng)} 互动\n"
        section += f"   - 来源：{platform} @{author}\n"
        if item.get("url"):
            section += f"   - 原始链接：[查看并转发]({item['url']})\n"
        else:
            section += "   - 原始链接：原始链接缺失（需回源补录）\n"
        # 给出具体可执行行动
        if eng > 1000:
            section += f"   - 💡 互动量高，建议官方账号直接转发，或截图发到内部群分享正面声音。\n"
        else:
            section += f"   - 💡 可在下次推文中引用此内容作为用户真实评价。\n"
        section += "\n"

    return section


def _generate_action_checklist(analysis: Dict, mode_config: Dict[str, int]) -> str:
    """2.4 立即执行清单（3-5 条，具体可执行）"""
    metrics = analysis["metrics"]
    risks = analysis.get("risks", [])
    all_items = analysis.get("all_items", [])
    comments_data = analysis.get("comments_analysis", {})

    high_risks = [r for r in risks if r["severity"] == "high"]
    medium_risks = [r for r in risks if r["severity"] == "medium"]
    high_risk_comments = comments_data.get("high_risk_comments", [])

    section = "### 2.4 立即执行清单\n\n"
    actions = []

    # 行动 1：处理高风险内容
    if high_risks:
        for r in high_risks[:mode_config["checklist_high_risk_limit"]]:
            item = r["item"]
            title = item["title"][:25] if item["title"] else item["content"][:25]
            url_part = (
                f" → [原始链接]({item['url']})"
                if item.get("url")
                else " → 原始链接缺失"
            )
            actions.append(
                f"- [ ] **【48h内 / P1】** 回应高风险内容《{title}...》{url_part}"
                f"（关键词：{', '.join(r['keywords'][:2])}）"
            )

    # 行动 2：回应中风险内容
    if medium_risks and len(actions) < mode_config["checklist_limit"]:
        for r in medium_risks[:mode_config["checklist_medium_risk_limit"]]:
            if len(actions) >= mode_config["checklist_limit"]:
                break
            item = r["item"]
            title = item["title"][:25] if item["title"] else item["content"][:25]
            url_part = (
                f" → [原始链接]({item['url']})"
                if item.get("url")
                else " → 原始链接缺失"
            )
            actions.append(
                f"- [ ] **【本周内 / P2】** 官方回复中风险帖子《{title}...》{url_part}"
            )

    # 行动 3：高风险评论回复
    if high_risk_comments and len(actions) < mode_config["checklist_limit"]:
        actions.append(
            f"- [ ] **【本周内】** 回复 {len(high_risk_comments)} 条高风险评论"
            f"（含关键词：{', '.join(high_risk_comments[0]['keywords'][:2])}）"
        )

    # 行动 4：借势高互动正面内容
    positive_items = sorted(
        [i for i in all_items if i["sentiment"]["label"] == "positive"],
        key=lambda x: sum(x["engagement"].values()), reverse=True
    )
    if positive_items and len(actions) < mode_config["checklist_limit"]:
        top = positive_items[0]
        eng = sum(top["engagement"].values())
        title = top["title"][:25] if top["title"] else top["content"][:25]
        url_part = (
            f" → [原始链接]({top['url']})"
            if top.get("url")
            else " → 原始链接缺失"
        )
        actions.append(
            f"- [ ] **【本周内 / P2】** 转发高互动正面内容《{title}...》"
            f"（互动量 {format_number(eng)}）{url_part}"
        )

    # 行动 5：无风险时的主动策略
    if not high_risks and not medium_risks and len(actions) < mode_config["checklist_limit"]:
        # 找到平台声量最高的，建议发布内容
        platform_dist = metrics.get("platform_dist", {})
        if platform_dist:
            top_platform = max(platform_dist, key=platform_dist.get)
            actions.append(
                f"- [ ] **【本周内】** 在声量最高的 {get_platform_name(top_platform)}"
                f"（共 {platform_dist[top_platform]} 条提及）发布 1 条主动内容，把握当前热度。"
            )

    # 质量门禁要求清单保持 3-5 条，低风险场景补足最少动作数。
    if len(actions) < 3:
        fallback_actions = [
            "- [ ] **【本周内】** 复盘本周互动最高的 3 条正向内容，沉淀 1 条可复用选题模板。",
            "- [ ] **【本周内】** 人工抽样检查 10 条高互动中性内容，识别潜在风险并补充回应策略。",
            "- [ ] **【48h内】** 建立“投诉/举报/退款”关键词巡检表，每天至少复查 2 次。",
        ]
        for fallback in fallback_actions:
            if len(actions) >= 3 or len(actions) >= mode_config["checklist_limit"]:
                break
            if fallback not in actions:
                actions.append(fallback)

    if actions:
        for action in actions[:mode_config["checklist_limit"]]:
            section += action + "\n"
    else:
        section += "- [ ] **【本周内】** 当前无紧急事项，建议安排一次内容选题会，规划下周内容方向。\n"

    section += "\n"
    return section


def _get_negative_comment_evidence(item: Dict[str, Any]) -> str:
    comments = item.get("comments", []) or []
    for comment in comments:
        if (comment.get("sentiment") or {}).get("label") == "negative":
            text = comment.get("content", "").strip()
            if text:
                return text[:80]
    return ""


def _generate_core_summary(analysis: Dict, mode_config: Dict[str, int]) -> str:
    risks = analysis.get("risks", [])
    high_count = len([risk for risk in risks if risk["severity"] == "high"])
    medium_count = len([risk for risk in risks if risk["severity"] == "medium"])
    benchmark_analysis = analysis.get("competitor_analysis", {})
    relevance_summary = analysis.get("relevance_summary", {})
    metrics = analysis.get("metrics", {})

    section = "## 一、核心结论\n\n"
    section += (
        f"- 主监控对象共命中 **{metrics.get('total_items', 0)}** 条高相关帖子，"
        f"其中 **P1 {high_count} 条 / P2 {medium_count} 条** 需要优先处理。\n"
    )
    if not risks:
        section += "- 未发现满足高相关门槛的负面帖子，本次不使用泛“中关村”内容补位。\n"
    if benchmark_analysis:
        section += (
            f"- 兄弟机构对比已纳入 **{len(benchmark_analysis)}** 个样本池，"
            "仅用于对比风险处置与舆情主题，不与我方案例混排。\n"
        )
    low_relevance = relevance_summary.get("low_relevance_items", 0)
    discarded = relevance_summary.get("discarded_items", 0)
    if low_relevance or discarded:
        section += (
            f"- 已剔除 **{low_relevance + discarded}** 条低相关或无法确认归属内容，"
            "避免把泛行业讨论误报为机构舆情。\n"
        )
    section += "\n"
    return section


def _format_primary_risk(risk: Dict[str, Any], idx: int, priority: str, config: Dict[str, Any]) -> str:
    item = risk["item"]
    title = item["title"][:80] if item.get("title") else item["content"][:80]
    keywords = "、".join(risk["keywords"][:4])
    institution = get_institution_label(item, "primary_entities")
    evidence = _get_negative_comment_evidence(item)
    text = f"#### {get_risk_priority(priority)} / {institution} / {risk['risk_type']}\n\n"
    text += f"- 平台：{get_platform_name(item['platform'])}\n"
    text += f"- 发布时间：{format_publish_time(item)}\n"
    text += f"- 帖子摘要：《{title}》\n"
    text += f"- 负面点摘要：{keywords or risk['reason']}\n"
    text += f"- 高相关依据：{risk.get('relevance_reason') or get_relevance_reason(item)}\n"
    if item.get("url"):
        text += f"- 原始链接：[查看原文]({item['url']})\n"
    else:
        text += "- 原始链接：原始链接缺失\n"
    if evidence:
        text += f"- 评论证据：\"{evidence}\"\n"
    text += "\n处理建议：\n"
    for suggestion in get_action_suggestions(risk["risk_type"], config)[:3]:
        text += f"- {suggestion}\n"
    text += "\n"
    return text


def _generate_primary_risk_section(analysis: Dict[str, Any], mode_config: Dict[str, int], config: Dict[str, Any]) -> str:
    risks = analysis.get("risks", [])
    high = [risk for risk in risks if risk["severity"] == "high"]
    medium = [risk for risk in risks if risk["severity"] == "medium"]

    section = "## 二、我方高相关负面案例\n\n"
    if not risks:
        section += "未发现满足高相关门槛的负面帖子。\n\n"
        return section

    if high:
        section += "### 2.1 需立即处理\n\n"
        for idx, risk in enumerate(high[:mode_config["high_risk_limit"]], 1):
            section += _format_primary_risk(risk, idx, "high", config)

    if medium:
        section += "### 2.2 关注跟进\n\n"
        for idx, risk in enumerate(medium[:mode_config["medium_risk_limit"]], 1):
            section += _format_primary_risk(risk, idx, "medium", config)

    return section


def _benchmark_hint(risk_type: str, org_name: str) -> str:
    hints = {
        "招生质疑": f"{org_name} 的招生相关讨论已出现负面反馈，我方应优先检查招生页、FAQ 和报名链路表述。",
        "虚假宣传": f"{org_name} 的案例说明宣传表述容易被放大，我方应先自查外宣材料与事实是否一一对应。",
        "培养体验": f"{org_name} 的培养体验争议提示我方需提前解释项目节奏、导师机制和考核方式。",
        "收费争议": f"{org_name} 的收费争议提醒我方统一收费/奖学金/退款口径，避免评论区二次扩散。",
        "师资质疑": f"{org_name} 的师资质疑表明履历与导师匹配机制需要更早公开，减少误解。",
        "管理投诉": f"{org_name} 的管理投诉案例可作为流程复盘样本，帮助我方提前补齐 SLA 和回应机制。",
    }
    return hints.get(risk_type, f"{org_name} 的案例可作为同类问题的预警样本，建议我方提前做口径和流程自查。")


def _generate_benchmark_section(analysis: Dict[str, Any], mode_config: Dict[str, int]) -> str:
    benchmark_analysis = analysis.get("competitor_analysis", {})
    section = "## 三、兄弟机构对比\n\n"
    if not benchmark_analysis:
        section += "本次未获取到可用于对比的兄弟机构高相关样本。\n\n"
        return section

    section += "以下内容仅用于风险处置对标，不作为我方正式舆情案例。\n\n"
    case_idx = 1
    for org_key, org_data in benchmark_analysis.items():
        org_name = org_data.get("display_name", org_key)
        org_risks = org_data.get("risks", [])
        org_cases = org_risks[:mode_config["benchmark_case_limit"]]
        if not org_cases:
            org_cases = [
                {
                    "item": item,
                    "risk_type": item.get("risk_type", "待研判"),
                    "severity": "medium",
                    "keywords": [item.get("risk_type", "待研判")],
                    "relevance_reason": get_relevance_reason(item),
                }
                for item in org_data.get("top_negative_items", [])[:mode_config["benchmark_case_limit"]]
            ]
        if not org_cases:
            continue

        section += f"### 3.{case_idx} {org_name}\n\n"
        for idx, risk in enumerate(org_cases, 1):
            item = risk["item"]
            title = item["title"][:70] if item.get("title") else item["content"][:70]
            eng = sum(item["engagement"].values())
            priority = get_rank_priority(idx)
            section += f"{idx}. [{priority}] **《{title}》**\n"
            section += f"   - 平台：{get_platform_name(item['platform'])} | 互动：{format_number(eng)} | 类型：{risk['risk_type']}\n"
            section += f"   - 高相关依据：{risk.get('relevance_reason') or get_relevance_reason(item)}\n"
            if item.get("url"):
                section += f"   - 原始链接：[查看原文]({item['url']})\n"
            else:
                section += "   - 原始链接：原始链接缺失\n"
            section += f"   - 对我方启发：{_benchmark_hint(risk['risk_type'], org_name)}\n\n"
        case_idx += 1

    if case_idx == 1:
        section += "本次未获取到可用于对比的兄弟机构高相关样本。\n\n"
    return section


def _generate_prioritized_actions(analysis: Dict[str, Any], mode_config: Dict[str, int]) -> str:
    section = "## 四、立即执行清单\n\n"
    actions: List[str] = []
    risks = analysis.get("risks", [])
    benchmark_analysis = analysis.get("competitor_analysis", {})

    high_risks = [risk for risk in risks if risk["severity"] == "high"]
    medium_risks = [risk for risk in risks if risk["severity"] == "medium"]

    for risk in high_risks[:mode_config["checklist_high_risk_limit"]]:
        item = risk["item"]
        title = item["title"][:25] if item.get("title") else item["content"][:25]
        url_part = f" → [原始链接]({item['url']})" if item.get("url") else " → 原始链接缺失"
        actions.append(
            f"- [ ] **【48h内 / P1】** 核查并回应《{title}...》{url_part}（{risk['risk_type']}）"
        )

    if len(actions) < mode_config["checklist_limit"]:
        for risk in medium_risks[:mode_config["checklist_medium_risk_limit"]]:
            item = risk["item"]
            title = item["title"][:25] if item.get("title") else item["content"][:25]
            url_part = f" → [原始链接]({item['url']})" if item.get("url") else " → 原始链接缺失"
            actions.append(
                f"- [ ] **【本周内 / P2】** 给《{title}...》准备统一回复口径{url_part}"
            )
            if len(actions) >= mode_config["checklist_limit"]:
                break

    if len(actions) < mode_config["checklist_limit"]:
        for org_key, org_data in benchmark_analysis.items():
            org_name = org_data.get("display_name", org_key)
            org_risks = org_data.get("risks", [])
            if not org_risks:
                continue
            ref_item = org_risks[0]["item"]
            ref_url = ref_item.get("url")
            url_part = f" → [参考链接]({ref_url})" if ref_url else ""
            actions.append(
                f"- [ ] **【本周内 / P2】** 对照 {org_name} 的「{org_risks[0]['risk_type']}」案例，完成我方同类页面和回复口径自查{url_part}"
            )
            if len(actions) >= mode_config["checklist_limit"]:
                break

    if len(actions) < 3:
        actions.extend([
            "- [ ] **【本周内】** 人工复核所有被剔除的低相关样本，持续完善别名白名单与排除词。",
            "- [ ] **【本周内】** 复盘本周高相关负面案例，沉淀一版招生/培养/管理回应 FAQ。",
            "- [ ] **【48h内】** 建立“投诉/举报/虚假/退款”关键词二次复核表，避免漏掉高风险帖子。",
        ][: max(0, 3 - len(actions))])

    for action in actions[:mode_config["checklist_limit"]]:
        section += action + "\n"
    section += "\n"
    return section


def _generate_focus_report(analysis: Dict[str, Any], mode: str = "standard") -> str:
    mode_config = MODE_CONFIGS[normalize_mode(mode)]
    config = load_config()
    return "".join([
        _generate_core_summary(analysis, mode_config),
        _generate_primary_risk_section(analysis, mode_config, config),
        _generate_benchmark_section(analysis, mode_config),
        _generate_prioritized_actions(analysis, mode_config),
    ])


# ============================================================
# 主入口
# ============================================================

def generate_report(analysis: Dict, mode: str = "standard") -> str:
    """
    生成完整双维度报告。

    analysis 结构：
    - 新模式（双维度）：
        {
            "account_analysis": {...},    # analyze_account_data() 的结果
            "fullvolume_analysis": {...}, # analyze_all_data() 的结果
            "metadata": {...}
        }
    - 旧模式（单维度，向后兼容）：
        直接传入 analyze_all_data() 的结果

    Returns:
        完整 Markdown 报告字符串
    """
    normalized_mode = normalize_mode(mode)

    # 判断是否为新双维度模式
    if "account_analysis" in analysis or "fullvolume_analysis" in analysis:
        return _generate_dual_report(analysis, normalized_mode)

    # 旧模式向后兼容：仅生成全网维度（使用旧函数）
    return _generate_legacy_report(analysis, normalized_mode)


def _generate_dual_report(analysis: Dict, mode: str = "standard") -> str:
    """生成默认定向处置报告。"""
    metadata = analysis.get("metadata", {})
    data_date = metadata.get("data_date", "全量数据")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    fullvolume_analysis = analysis.get("fullvolume_analysis") or {}
    full_meta = fullvolume_analysis.get("metadata", {})

    primary_targets = " / ".join(full_meta.get("primary_targets", [])) or "北京中关村学院 / 中关村人工智能研究院"
    benchmark_targets = " / ".join(full_meta.get("benchmark_targets", [])) or "深圳河套研究院 / 上海创智研究院"

    header = f"""# 定向舆情处置报告

> **生成时间**：{generated_at} | **数据范围**：{data_date}
> **主监控对象**：{primary_targets}
> **兄弟机构对比**：{benchmark_targets}

---

"""

    if fullvolume_analysis:
        return header + _generate_focus_report(fullvolume_analysis, mode=mode)
    return header + "## 一、核心结论\n\n当前没有可用的高相关舆情数据。\n"


def _generate_legacy_report(analysis: Dict, mode: str = "standard") -> str:
    """旧版兼容入口，统一走定向处置报告。"""
    metadata = analysis.get("metadata", {})
    data_date = metadata.get("data_date", "全量数据")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = f"""# 定向舆情处置报告

> **生成时间**：{generated_at} | **数据范围**：{data_date}

---

"""
    return header + _generate_focus_report(analysis, mode=mode)


# ============================================================
# 旧版函数保留（向后兼容）
# ============================================================

def generate_executive_summary(analysis: Dict) -> str:
    return _generate_legacy_report(analysis, mode="standard")


if __name__ == "__main__":
    print("Report Generator V3 - Dual Dimension")
    print("=" * 70)
    print("✅ Module loaded successfully")
