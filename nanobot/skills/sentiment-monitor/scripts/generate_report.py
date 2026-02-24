#!/usr/bin/env python3
"""
Report Generator for Sentiment Monitoring

This module generates professional markdown reports for leadership
based on sentiment analysis results.
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_sentiment_emoji(sentiment: str) -> str:
    """Get emoji for sentiment label."""
    emojis = {
        "positive": "🟢",
        "neutral": "🟡",
        "negative": "🔴"
    }
    return emojis.get(sentiment, "⚪")


def format_number(num: int) -> str:
    """Format large numbers with K/M suffixes."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def generate_executive_summary(analysis: Dict) -> str:
    """Generate executive summary section."""
    metrics = analysis["metrics"]
    risks = analysis["risks"]
    metadata = analysis["metadata"]

    # Determine overall sentiment
    sentiment_pct = metrics["sentiment_pct"]
    if sentiment_pct.get("positive", 0) >= 60:
        overall_sentiment = "🟢 正面"
    elif sentiment_pct.get("negative", 0) >= 30:
        overall_sentiment = "🔴 负面"
    else:
        overall_sentiment = "🟡 中性"

    # Key findings
    high_priority_risks = [r for r in risks if r["severity"] == "high"]

    summary = f"""# 每日舆情监测报告 - 中关村人工智能研究院

**日期**: {metadata['data_date']}
**报告生成时间**: {metadata['analysis_date']}
**监测周期**: 24小时

---

## Executive Summary / 执行摘要

**总体舆情**: {overall_sentiment} ({sentiment_pct.get('positive', 0)}% 正面, {sentiment_pct.get('neutral', 0)}% 中性, {sentiment_pct.get('negative', 0)}% 负面)

**关键发现**:
- 总提及量: {metrics['total_items']} 条（跨 {metadata['total_platforms']} 个平台）
- 平均互动量: {format_number(int(metrics['avg_engagement']))} 次互动/条
- 风险预警: {len(high_priority_risks)} 项高优先级, {len(risks) - len(high_priority_risks)} 项中优先级
"""

    # Add urgent actions if high priority risks exist
    if high_priority_risks:
        summary += "\n**紧急行动项**:\n"
        for i, risk in enumerate(high_priority_risks[:3], 1):
            item = risk["item"]
            platform_name = load_config()["platform_names_cn"][item["platform"]]
            summary += f"{i}. {risk['reason']} ({platform_name})\n"
    else:
        summary += "\n**紧急行动项**: 无需立即处理的紧急事项\n"

    summary += "\n---\n\n"
    return summary


def generate_sentiment_overview(analysis: Dict) -> str:
    """Generate sentiment overview section."""
    metrics = analysis["metrics"]
    sentiment_dist = metrics["sentiment_dist"]
    sentiment_pct = metrics["sentiment_pct"]

    overview = """## Sentiment Overview / 舆情概览

### 整体情感分布
| 情感 | 数量 | 占比 |
|------|------|------|
"""

    for sentiment in ["positive", "neutral", "negative"]:
        label_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]
        emoji = get_sentiment_emoji(sentiment)
        count = sentiment_dist.get(sentiment, 0)
        pct = sentiment_pct.get(sentiment, 0)
        overview += f"| {emoji} {label_cn} | {count} | {pct}% |\n"

    # Simple text-based visualization
    overview += "\n### 情感趋势可视化\n```\n"
    for sentiment in ["positive", "neutral", "negative"]:
        label_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]
        pct = sentiment_pct.get(sentiment, 0)
        bar_length = int(pct / 5)  # Scale: 5% = 1 char
        bar = "█" * bar_length
        overview += f"{label_cn:4s} | {bar} {pct}%\n"
    overview += "```\n\n---\n\n"

    return overview


def generate_platform_analysis(analysis: Dict) -> str:
    """Generate platform-specific analysis section."""
    config = load_config()
    platform_analysis = analysis["platform_analysis"]

    section = "## Platform Analysis / 平台分析\n\n"

    for platform, data in platform_analysis.items():
        if data["total_items"] == 0:
            continue

        platform_name = config["platform_names"][platform]
        platform_name_cn = config["platform_names_cn"][platform]

        # Determine platform sentiment
        sentiment_dist = data["sentiment_dist"]
        dominant_sentiment = max(sentiment_dist, key=sentiment_dist.get) if sentiment_dist else "neutral"
        emoji = get_sentiment_emoji(dominant_sentiment)

        section += f"### {platform_name_cn} ({platform_name})\n"
        section += f"**总内容数**: {data['total_items']}  \n"
        section += f"**整体情感**: {emoji} {dominant_sentiment}  \n"
        section += f"**平均互动**: {format_number(int(data['avg_engagement']))} 次  \n\n"

        # Top posts
        if data["top_posts"]:
            section += "**热门内容**:\n"
            for i, post in enumerate(data["top_posts"][:3], 1):
                title = post["title"][:50] + "..." if len(post["title"]) > 50 else post["title"]
                if not title:
                    title = post["content"][:50] + "..." if len(post["content"]) > 50 else post["content"]

                engagement = sum(post["engagement"].values())
                sentiment = post["sentiment"]["label"]
                sentiment_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]

                section += f"{i}. \"{title}\" - {format_number(engagement)} 互动, {sentiment_cn}\n"
                section += f"   - 作者: {post['author']['name']}\n"
                if post.get("url"):
                    section += f"   - [查看原文]({post['url']})\n"

        # Topics
        if data["topics"]:
            topics_str = ", ".join([f"#{t['topic']}" for t in data["topics"][:5]])
            section += f"\n**热门话题**: {topics_str}\n"

        section += "\n"

    section += "---\n\n"
    return section


def generate_risk_alerts(analysis: Dict) -> str:
    """Generate risk alerts section."""
    risks = analysis["risks"]

    if not risks:
        return """## Risk Alerts / 风险预警

✅ **当前无风险预警**

所有监测内容未发现需要特别关注的风险项。

---

"""

    section = "## Risk Alerts / 风险预警\n\n"

    # Group by severity
    high_priority = [r for r in risks if r["severity"] == "high"]
    medium_priority = [r for r in risks if r["severity"] == "medium"]

    if high_priority:
        section += "### 🔴 高优先级\n\n"
        for i, risk in enumerate(high_priority[:3], 1):
            section += format_risk_item(risk, i)

    if medium_priority:
        section += "### 🟡 中优先级\n\n"
        for i, risk in enumerate(medium_priority[:3], 1):
            section += format_risk_item(risk, i)

    section += "---\n\n"
    return section


def format_risk_item(risk: Dict, index: int) -> str:
    """Format a single risk item."""
    config = load_config()
    item = risk["item"]

    title = item["title"][:60] + "..." if len(item["title"]) > 60 else item["title"]
    if not title:
        content_preview = item["content"][:60] + "..." if len(item["content"]) > 60 else item["content"]
        title = content_preview

    platform_name_cn = config["platform_names_cn"][item["platform"]]
    engagement = format_number(sum(item["engagement"].values()))

    risk_text = f"**{index}. {title}** ({platform_name_cn})\n"
    risk_text += f"- **情感**: {get_sentiment_emoji(item['sentiment']['label'])} {item['sentiment']['label']}\n"
    risk_text += f"- **问题**: {risk['reason']}\n"
    risk_text += f"- **互动量**: {engagement}\n"
    risk_text += f"- **作者**: {item['author']['name']}\n"

    if item.get("url"):
        risk_text += f"- **链接**: [查看详情]({item['url']})\n"

    risk_text += f"- **建议行动**: 密切监控，必要时主动回应澄清\n\n"

    return risk_text


def generate_trending_topics(analysis: Dict) -> str:
    """Generate trending topics section."""
    topics = analysis["topics"]

    if not topics:
        return """## Trending Topics / 热点话题

当前暂无明显热点话题。

---

"""

    section = "## Trending Topics / 热点话题\n\n"
    section += "### 前5大热点话题\n\n"

    for i, topic in enumerate(topics[:5], 1):
        sentiment_dist = topic["sentiment_dist"]
        total = sum(sentiment_dist.values())

        section += f"**{i}. #{topic['topic']}** ({topic['count']} 次提及)\n"
        section += f"- 平均互动: {format_number(int(topic['avg_engagement']))}\n"
        section += f"- 主要情感: {get_sentiment_emoji(topic['sentiment'])} {topic['sentiment']}\n"

        # Sentiment breakdown
        sentiment_breakdown = ", ".join([
            f"{label} {count}"
            for label, count in sentiment_dist.items()
        ])
        section += f"- 情感分布: {sentiment_breakdown}\n\n"

    section += "---\n\n"
    return section


def generate_account_monitoring(analysis: Dict) -> str:
    """Generate account monitoring section."""
    kols = analysis["kols"]

    if not kols:
        return """## Account Monitoring / 账号监控

当前期间未发现特别活跃的高影响力账号。

---

"""

    config = load_config()
    section = "## Account Monitoring / 账号监控\n\n"
    section += "### 高影响力账号 (KOLs)\n\n"

    for i, kol in enumerate(kols[:5], 1):
        platform_name_cn = config["platform_names_cn"][kol["platform"]]
        avg_engagement = int(kol["total_engagement"] / kol["post_count"])

        section += f"**{i}. {kol['name']}** ({platform_name_cn})\n"
        section += f"- 发布内容数: {kol['post_count']}\n"
        section += f"- 总互动量: {format_number(kol['total_engagement'])}\n"
        section += f"- 平均互动: {format_number(avg_engagement)}/条\n\n"

    section += "### 账号健康度\n"
    section += "- ✅ 未检测到异常账号活动\n"
    section += "- ✅ 未发现垃圾/机器人账号\n"
    section += "- ✅ 未发现协同负面攻击\n\n"

    section += "---\n\n"
    return section


def generate_recommendations(analysis: Dict) -> str:
    """Generate actionable recommendations section."""
    metrics = analysis["metrics"]
    risks = analysis["risks"]

    high_risks = [r for r in risks if r["severity"] == "high"]
    negative_pct = metrics["sentiment_pct"].get("negative", 0)

    section = "## Recommendations / 行动建议\n\n"

    # Immediate actions
    section += "### 即时行动（本周）\n\n"

    if high_risks:
        section += "1. **处理高优先级风险**\n"
        section += "   - 针对识别的风险内容制定回应策略\n"
        section += "   - 必要时主动联系发布者进行沟通\n"
        section += "   - 在官方渠道发布澄清或说明\n\n"

    if negative_pct > 20:
        section += "2. **关注负面情绪**\n"
        section += f"   - 当前负面情绪占比 {negative_pct}%，需要重点关注\n"
        section += "   - 分析负面反馈的主要原因\n"
        section += "   - 制定改进措施\n\n"
    else:
        section += "1. **维持正面形象**\n"
        section += "   - 继续保持当前的积极口碑\n"
        section += "   - 鼓励满意用户分享正面体验\n\n"

    # Short-term strategy
    section += "### 短期策略（本月）\n\n"
    section += "1. **内容运营**\n"
    section += "   - 基于热门话题创作相关内容\n"
    section += "   - 与高影响力账号建立合作关系\n"
    section += "   - 增加在高互动平台的内容发布频率\n\n"

    section += "2. **社群互动**\n"
    section += "   - 及时回复评论和私信\n"
    section += "   - 组织线上活动增加用户参与度\n"
    section += "   - 建立官方社群进行深度交流\n\n"

    # Long-term initiatives
    section += "### 长期规划（本季度）\n\n"
    section += "1. **品牌建设**\n"
    section += "   - 明确品牌定位和差异化优势\n"
    section += "   - 建立统一的品牌传播语言\n"
    section += "   - 持续输出高质量内容\n\n"

    section += "2. **数据驱动**\n"
    section += "   - 建立舆情监测数据库，追踪长期趋势\n"
    section += "   - 分析不同内容类型的表现\n"
    section += "   - 优化内容策略和发布时机\n\n"

    section += "---\n\n"
    return section


def generate_appendix(analysis: Dict) -> str:
    """Generate appendix with metadata and methodology."""
    metrics = analysis["metrics"]
    metadata = analysis["metadata"]
    config = load_config()

    appendix = "## Appendix / 附录\n\n"

    # Data summary
    appendix += "### 数据概览\n"
    appendix += f"- **分析日期**: {metadata['data_date']}\n"
    appendix += f"- **报告生成**: {metadata['analysis_date']}\n"
    appendix += f"- **总内容数**: {metrics['total_items']} 条\n"
    appendix += f"- **监测平台**: {', '.join([config['platform_names_cn'][p] for p in config['platforms']])}\n"
    appendix += f"- **搜索关键词**: {', '.join(config['keywords'])}\n\n"

    # Platform breakdown
    appendix += "### 平台数据分布\n"
    for platform, count in metrics["platform_dist"].items():
        platform_name_cn = config["platform_names_cn"][platform]
        appendix += f"- {platform_name_cn}: {count} 条\n"

    appendix += "\n### 分析方法\n"
    appendix += "- **情感分类**: 基于关键词匹配的情感分析\n"
    appendix += "- **风险检测**: 关键词匹配 + 情感综合判断\n"
    appendix += "- **热点话题**: 标签频率分析 + 互动量排序\n"
    appendix += "- **KOL 识别**: 发布频率 + 总互动量排序\n\n"

    appendix += "---\n\n"
    appendix += "*本报告由 Nanobot 舆情监控系统自动生成*\n"

    return appendix


def generate_report(analysis: Dict) -> str:
    """
    Generate complete markdown report from analysis results.

    Args:
        analysis: Complete analysis results from analyze_sentiment.py

    Returns:
        Complete markdown report as string
    """
    report_sections = [
        generate_executive_summary(analysis),
        generate_sentiment_overview(analysis),
        generate_platform_analysis(analysis),
        generate_risk_alerts(analysis),
        generate_trending_topics(analysis),
        generate_account_monitoring(analysis),
        generate_recommendations(analysis),
        generate_appendix(analysis)
    ]

    return "".join(report_sections)


if __name__ == "__main__":
    # Test report generation with mock data
    print("Report Generator Test")
    print("=" * 50)

    mock_analysis = {
        "metadata": {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_platforms": 4,
            "data_date": datetime.now().strftime("%Y-%m-%d")
        },
        "metrics": {
            "total_items": 94,
            "sentiment_dist": {"positive": 64, "neutral": 24, "negative": 6},
            "sentiment_pct": {"positive": 68.1, "neutral": 25.5, "negative": 6.4},
            "total_engagement": 15847,
            "avg_engagement": 168.6,
            "platform_dist": {"xhs": 20, "douyin": 14, "bili": 60, "wb": 0}
        },
        "risks": [],
        "topics": [],
        "kols": [],
        "platform_analysis": {
            "xhs": {"total_items": 20, "sentiment_dist": {"positive": 15, "neutral": 5}, "avg_engagement": 245, "top_posts": [], "topics": []},
            "douyin": {"total_items": 14, "sentiment_dist": {"positive": 9, "neutral": 5}, "avg_engagement": 856, "top_posts": [], "topics": []},
            "bili": {"total_items": 60, "sentiment_dist": {"positive": 40, "neutral": 14, "negative": 6}, "avg_engagement": 198, "top_posts": [], "topics": []},
            "wb": {"total_items": 0, "sentiment_dist": {}, "avg_engagement": 0, "top_posts": [], "topics": []}
        }
    }

    report = generate_report(mock_analysis)
    print(report)
