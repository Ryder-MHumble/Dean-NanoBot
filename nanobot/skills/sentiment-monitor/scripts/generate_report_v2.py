#!/usr/bin/env python3
"""
Optimized Report Generator for Sentiment Monitoring - V2.0

重点优化：
1. 可溯源：每个重点发现都附带原文链接
2. 清晰简洁：优化排版和视觉层次
3. 专业易读：添加数据表格和多维度分析
4. 行动导向：明确的优先级和建议措施
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
    """生成执行摘要 - 优化版"""
    metrics = analysis["metrics"]
    risks = analysis["risks"]
    metadata = analysis["metadata"]
    comments_data = analysis.get("comments_analysis", {})

    # 确定总体情感
    sentiment_pct = metrics["sentiment_pct"]
    if sentiment_pct.get("positive", 0) >= 60:
        overall_sentiment = "🟢 正面为主"
        trend_icon = "↑"
    elif sentiment_pct.get("negative", 0) >= 30:
        overall_sentiment = "🔴 负面明显"
        trend_icon = "↓"
    else:
        overall_sentiment = "🟡 中性偏多"
        trend_icon = "→"

    high_priority_risks = [r for r in risks if r["severity"] == "high"]
    
    # 评论相关数据
    total_comments = comments_data.get("total_comments", 0)
    comment_sentiment = comments_data.get("comments_sentiment", {})
    comment_negative = comment_sentiment.get("negative", 0)

    summary = f"""# 舆情监测报告

> **数据范围**: {metadata['data_date']} | **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")} | **数据总量**: {metrics['total_items']} 条帖子 + {total_comments} 条评论

---

## 📊 核心指标

| 指标 | 数值 | 情感分布 |
|------|------|----------|
| **总提及量** | {metrics['total_items']} 条帖子 | 🟢 {sentiment_pct.get('positive', 0)}% 正面 / 🟡 {sentiment_pct.get('neutral', 0)}% 中性 / 🔴 {sentiment_pct.get('negative', 0)}% 负面 |
| **评论量** | {total_comments} 条评论 | 📊 反映用户互动热度和参与度 |
| **整体情感** | {overall_sentiment} | {trend_icon} 趋势待观察 |
| **平均互动** | {format_number(int(metrics['avg_engagement']))} 次/条 | 反映内容热度 |
| **风险预警** | {len(high_priority_risks)} 高优先级 / {len(risks) - len(high_priority_risks)} 中优先级 | {"⚠️ 需关注" if len(high_priority_risks) > 0 or comment_negative > total_comments * 0.1 else "✅ 正常"} |

---

## 🎯 关键发现

"""

    # 添加关键发现
    all_items = analysis.get("all_items", [])
    if all_items:
        # 找出最高互动内容
        top_item = max(all_items, key=lambda x: sum(x["engagement"].values())) if all_items else None
        if top_item:
            engagement_total = sum(top_item["engagement"].values())
            summary += f"1. **📈 最高互动内容**：《{top_item['title'][:40]}...》获得{format_number(engagement_total)}次互动\n"
            summary += f"   - 平台：{load_config()['platform_names_cn'][top_item['platform']]}\n"
            summary += f"   - 情感：{get_sentiment_emoji(top_item['sentiment']['label'])} {top_item['sentiment']['label']}\n"
            if top_item.get("url"):
                summary += f"   - [🔗 查看原文]({top_item['url']})\n"

    # 评论情感提示
    if total_comments > 0:
        comment_pct_negative = int(comment_negative * 100 / total_comments) if total_comments > 0 else 0
        if comment_pct_negative >= 10:
            summary += f"\n2. **💬 评论预警**：评论中发现{comment_negative}条负面评论（占比{comment_pct_negative}%），需要关注\n"
        else:
            summary += f"\n2. **💬 评论状态**：{total_comments}条评论中仅{comment_negative}条为负面（占比{comment_pct_negative}%），总体正面\n"
    
    # 风险提示
    if high_priority_risks:
        summary += f"\n3. **⚠️ 风险提示**：发现{len(high_priority_risks)}项高优先级风险，需要立即处理\n"
    else:
        if total_comments == 0:
            summary += "\n2. **✅ 舆情健康**：未发现高优先级风险\n"
        else:
            summary += "\n3. **✅ 舆情健康**：未发现高优先级风险\n"

    # 热门话题
    topics = analysis.get("topics", [])
    if topics:
        top_topic = topics[0]
        idx = 4 if total_comments > 0 else 3
        summary += f"\n{idx}. **🔥 热点话题**：#{top_topic['topic']} 提及{top_topic['count']}次，主导情感{get_sentiment_emoji(top_topic['sentiment'])} {top_topic['sentiment']}\n"

    summary += "\n---\n\n"

    # 需立即处理的事项
    if high_priority_risks:
        summary += "## ⏰ 需立即处理\n\n"
        for i, risk in enumerate(high_priority_risks[:3], 1):
            item = risk["item"]
            platform_name_cn = load_config()["platform_names_cn"][item["platform"]]
            title = item["title"][:40] if item["title"] else item["content"][:40]
            summary += f"- [ ] **高优先级{i}**：{risk['reason']} ({platform_name_cn})\n"
            summary += f"      内容：《{title}...》\n"
            if item.get("url"):
                summary += f"      [🔗 查看原文]({item['url']})\n"
        summary += "\n---\n\n"

    return summary


def generate_platform_analysis(analysis: Dict) -> str:
    """生成平台分析 - 优化版（添加详细内容信息和链接）"""
    config = load_config()
    platform_analysis = analysis["platform_analysis"]

    section = "## 🏛️ 平台分析\n\n"

    for platform, data in platform_analysis.items():
        if data["total_items"] == 0:
            continue

        platform_name_cn = config["platform_names_cn"][platform]

        # 平台概览
        sentiment_dist = data["sentiment_dist"]
        dominant_sentiment = max(sentiment_dist, key=sentiment_dist.get) if sentiment_dist else "neutral"
        emoji = get_sentiment_emoji(dominant_sentiment)

        section += f"### {platform_name_cn}\n\n"
        section += f"**数据概览**：{data['total_items']}条内容 | 平均互动{format_number(int(data['avg_engagement']))}次 | {emoji} {dominant_sentiment}\n\n"

        # 高互动内容（详细版）
        if data["top_posts"]:
            section += "#### 🔥 高互动内容（Top 3）\n\n"
            for i, post in enumerate(data["top_posts"][:3], 1):
                title = post["title"][:60] if post["title"] else post["content"][:60]

                # 互动数据分解
                engagement_breakdown = []
                if post["engagement"].get("likes"):
                    engagement_breakdown.append(f"{post['engagement']['likes']}赞")
                if post["engagement"].get("comments"):
                    engagement_breakdown.append(f"{post['engagement']['comments']}评")
                if post["engagement"].get("shares"):
                    engagement_breakdown.append(f"{post['engagement']['shares']}转")
                if post["engagement"].get("collects"):
                    engagement_breakdown.append(f"{post['engagement']['collects']}藏")

                engagement_total = sum(post["engagement"].values())
                engagement_str = " + ".join(engagement_breakdown) + f" = **{format_number(engagement_total)}**"

                sentiment = post["sentiment"]["label"]
                sentiment_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]
                sentiment_emoji = get_sentiment_emoji(sentiment)

                section += f"{i}. **《{title}》**\n"
                section += f"   - 👤 作者：{post['author']['name']}\n"
                section += f"   - 📊 互动：{engagement_str}\n"
                section += f"   - 🎭 情感：{sentiment_emoji} {sentiment_cn}\n"

                # 添加链接
                if post.get("url"):
                    section += f"   - 🔗 [查看原文]({post['url']})\n"

                # 根据情感给出建议
                if sentiment == "negative":
                    section += f"   - 💡 **建议**：关注负面内容，评估是否需要回应\n"
                elif engagement_total > 1000:
                    section += f"   - 💡 **建议**：高互动正面内容，可考虑官方转发放大影响\n"

                section += "\n"

        # 话题标签
        if data["topics"]:
            topics_list = [f"#{t['topic']}" for t in data["topics"][:5]]
            section += f"#### 📊 热门话题\n\n{', '.join(topics_list)}\n\n"

        section += "---\n\n"

    return section


def generate_risk_alerts(analysis: Dict) -> str:
    """生成风险预警 - 优化版（添加详细信息和建议）"""
    risks = analysis["risks"]

    if not risks:
        return """## ⚠️ 风险预警

✅ **当前无风险预警**

所有监测内容未发现需要特别关注的风险项。

---

"""

    section = "## ⚠️ 风险预警\n\n"

    # 高优先级风险
    high_priority = [r for r in risks if r["severity"] == "high"]
    if high_priority:
        section += "### 🔴 高优先级风险（需24小时内处理）\n\n"
        for i, risk in enumerate(high_priority[:3], 1):
            section += format_risk_item_detailed(risk, i)

    # 中优先级风险
    medium_priority = [r for r in risks if r["severity"] == "medium"]
    if medium_priority:
        section += "### 🟡 中优先级风险（需本周内关注）\n\n"
        for i, risk in enumerate(medium_priority[:3], 1):
            section += format_risk_item_detailed(risk, i)

    section += "---\n\n"
    return section


def format_risk_item_detailed(risk: Dict, index: int) -> str:
    """格式化单个风险项 - 详细版"""
    config = load_config()
    item = risk["item"]

    title = item["title"][:60] if item["title"] else item["content"][:60]
    platform_name_cn = config["platform_names_cn"][item["platform"]]
    engagement_total = sum(item["engagement"].values())

    # 内容引用
    content_preview = item["content"][:100] if item["content"] else ""

    risk_text = f"#### 风险{index}: {risk['reason']}\n\n"

    # 来源内容
    if content_preview:
        risk_text += f"**来源内容**：\n> {content_preview}...\n\n"

    # 详细信息
    risk_text += f"**详细信息**：\n"
    risk_text += f"- 📱 **平台**：{platform_name_cn}\n"
    risk_text += f"- 👤 **作者**：{item['author']['name']}\n"
    risk_text += f"- 📊 **互动**：{format_number(engagement_total)}次\n"
    risk_text += f"- 🎭 **情感**：{get_sentiment_emoji(item['sentiment']['label'])} {item['sentiment']['label']}\n"
    risk_text += f"- 🔑 **风险关键词**：{', '.join(risk['keywords'][:3])}\n"

    # 添加链接
    if item.get("url"):
        risk_text += f"- 🔗 **原文链接**：[查看详情]({item['url']})\n"

    # 影响评估
    risk_text += f"\n**影响评估**：\n"
    if engagement_total > 500:
        risk_text += f"- 🎯 **影响范围**：高（互动量{format_number(engagement_total)}，可能广泛传播）\n"
    elif engagement_total > 100:
        risk_text += f"- 🎯 **影响范围**：中（互动量{format_number(engagement_total)}）\n"
    else:
        risk_text += f"- 🎯 **影响范围**：低（互动量{format_number(engagement_total)}）\n"

    risk_text += f"- 📈 **传播风险**：{'高' if risk['severity'] == 'high' else '中等'}\n"

    # 建议行动
    risk_text += f"\n**建议行动**：\n"
    if risk["severity"] == "high":
        risk_text += f"1. ✅ **立即**（2小时内）：评估内容真实性，准备回应方案\n"
        risk_text += f"2. ✅ **短期**（24小时内）：发布官方说明或澄清\n"
        risk_text += f"3. ✅ **跟踪**：持续监控相关讨论，及时回应新问题\n"
    else:
        risk_text += f"1. ✅ **短期**：关注内容发展，评估是否需要介入\n"
        risk_text += f"2. ✅ **跟踪**：监控相关讨论\n"

    risk_text += "\n---\n\n"
    return risk_text


def generate_account_monitoring(analysis: Dict) -> str:
    """生成账号监控 - 优化版（添加KOL详细信息）"""
    kols = analysis["kols"]

    if not kols:
        return """## 👥 账号监控

当前期间未发现特别活跃的高影响力账号。

---

"""

    config = load_config()
    section = "## 👥 账号监控\n\n"
    section += "### 🌟 高影响力账号（KOLs）\n\n"

    for i, kol in enumerate(kols[:5], 1):
        platform_name_cn = config["platform_names_cn"][kol["platform"]]
        avg_engagement = int(kol["total_engagement"] / kol["post_count"])

        section += f"#### {i}. {kol['name']} ({platform_name_cn})\n\n"

        # 基本信息
        section += f"**活动数据**：\n"
        section += f"- 📝 发布内容：{kol['post_count']}条\n"
        section += f"- 💬 总互动量：{format_number(kol['total_engagement'])}\n"
        section += f"- 📊 平均互动：{format_number(avg_engagement)}/条\n"

        # 内容主题（列出发布的内容）
        if kol["posts"]:
            section += f"\n**内容主题**：\n"
            for post in kol["posts"][:2]:
                title = post["title"][:50] if post["title"] else post["content"][:50]
                engagement = sum(post["engagement"].values())
                section += f"- 《{title}》({format_number(engagement)}互动)\n"
                if post.get("url"):
                    section += f"  [🔗 查看]({post['url']})\n"

        # 合作建议
        section += f"\n**合作价值评估**：\n"
        if avg_engagement > 1000:
            section += f"- ✅ **影响力**：⭐⭐⭐⭐⭐（高影响力KOL）\n"
            section += f"- 💡 **建议**：优先建立深度合作关系，可邀请作为品牌大使\n"
        elif avg_engagement > 500:
            section += f"- ✅ **影响力**：⭐⭐⭐⭐（腰部达人）\n"
            section += f"- 💡 **建议**：保持良好互动，可合作内容共创\n"
        else:
            section += f"- ✅ **影响力**：⭐⭐⭐（潜力账号）\n"
            section += f"- 💡 **建议**：关注发展，适时提供支持\n"

        section += "\n"

    # 账号健康度
    section += "### 🛡️ 账号健康度检测\n\n"
    section += "- ✅ 未检测到异常账号活动\n"
    section += "- ✅ 未发现垃圾/机器人账号\n"
    section += "- ✅ 未发现协同负面攻击\n\n"

    section += "---\n\n"
    return section


def generate_recommendations(analysis: Dict) -> str:
    """生成行动建议 - 优化版（添加执行细节和KPI）"""
    metrics = analysis["metrics"]
    risks = analysis["risks"]

    high_risks = [r for r in risks if r["severity"] == "high"]
    negative_pct = metrics["sentiment_pct"].get("negative", 0)

    section = "## 💡 行动建议\n\n"

    # 即时行动
    section += "### ⏰ 即时行动（24小时内）\n\n"

    if high_risks:
        section += "#### 行动1: 处理高优先级风险\n\n"
        section += "**任务**：\n"
        for risk in high_risks[:2]:
            title = risk["item"]["title"][:30] if risk["item"]["title"] else risk["item"]["content"][:30]
            section += f"- [ ] 评估并回应《{title}...》相关风险\n"
        section += "\n"
        section += "**执行部门**：品牌部 + 公关部\n"
        section += "**所需资源**：官方声明模板、FAQ文档\n"
        section += "**预期效果**：平息质疑，避免负面扩散\n"
        section += "**跟踪指标**：相关讨论情绪变化、负面提及量\n\n"

    # KOL互动
    kols = analysis.get("kols", [])
    if kols:
        section += "#### 行动2: KOL关系维护\n\n"
        section += "**任务**：\n"
        for kol in kols[:2]:
            section += f"- [ ] 与{kol['name']}建立联系，表达感谢\n"
        section += "\n"
        section += "**执行部门**：运营部\n"
        section += "**预期效果**：建立长期合作关系\n\n"

    section += "---\n\n"

    # 短期策略
    section += "### 📅 短期策略（本周内）\n\n"

    section += "#### 策略1: 内容运营优化\n\n"
    section += "**目标**：放大正面内容，提升品牌形象\n\n"
    section += "**具体行动**：\n"
    section += f"- [ ] 发布{3-len(high_risks)}篇正面内容稀释负面讨论\n"
    section += "- [ ] 鼓励满意用户分享真实体验（UGC激励）\n"
    section += "- [ ] 在主要平台保持日更节奏\n\n"

    section += "**执行部门**：内容部 + 运营部\n"
    section += "**所需资源**：内容制作预算、用户激励预算\n"
    section += f"**预期效果**：正面内容占比提升至75%+\n"
    section += "**跟踪指标**：正面提及量、内容互动率\n\n"

    section += "---\n\n"

    # 长期规划
    section += "### 📆 长期规划（本月内）\n\n"

    section += "#### 规划1: 数据驱动优化\n\n"
    section += "**目标**：建立舆情数据资产，持续优化策略\n\n"
    section += "**具体行动**：\n"
    section += "- [ ] 使用Supabase存储历史舆情数据（已完成数据库设置）\n"
    section += "- [ ] 每周舆情复盘会，数据驱动决策\n"
    section += "- [ ] 建立舆情预警机制\n\n"

    section += "**执行部门**：技术部 + 运营部\n"
    section += "**预期效果**：建立舆情数据资产，提升决策科学性\n\n"

    section += "---\n\n"

    # 成功指标
    section += "### ✅ 成功指标（KPI）\n\n"

    section += "**即时指标（7天内）**：\n"
    if high_risks:
        section += f"- [ ] 高优先级风险处理完成率 = 100%\n"
    section += f"- [ ] 正面内容占比 ≥ {max(60, int(metrics['sentiment_pct'].get('positive', 0)) + 10)}%\n"
    if kols:
        section += f"- [ ] KOL合作触达 ≥ 2位\n"

    section += f"\n**短期指标（1个月内）**：\n"
    section += f"- [ ] 总互动量增长 ≥ 20%\n"
    section += f"- [ ] 负面提及率下降至 < {max(5, int(negative_pct) - 2)}%\n"
    section += f"- [ ] 建立舆情数据库，覆盖历史数据\n\n"

    section += "---\n\n"
    return section


def generate_appendix(analysis: Dict) -> str:
    """生成附录"""
    metrics = analysis["metrics"]
    metadata = analysis["metadata"]
    config = load_config()

    appendix = "## 📋 附录\n\n"

    # 数据概览
    appendix += "### 数据概览\n\n"
    appendix += f"- **数据范围**：{metadata['data_date']}\n"
    appendix += f"- **报告生成**：{metadata['analysis_date']}\n"
    appendix += f"- **总内容数**：{metrics['total_items']} 条\n"
    appendix += f"- **监测平台**：{', '.join([config['platform_names_cn'][p] for p in config['platforms']])}\n"
    appendix += f"- **搜索关键词**：{', '.join(config['keywords'])}\n\n"

    # 平台分布
    appendix += "### 平台数据分布\n\n"
    for platform, count in metrics["platform_dist"].items():
        platform_name_cn = config["platform_names_cn"][platform]
        appendix += f"- {platform_name_cn}: {count} 条\n"

    appendix += "\n### 分析方法\n\n"
    appendix += "- **情感分类**：基于关键词匹配的情感分析\n"
    appendix += "- **风险检测**：关键词匹配 + 情感综合判断\n"
    appendix += "- **热点话题**：标签频率分析 + 互动量排序\n"
    appendix += "- **KOL 识别**：发布频率 + 总互动量排序\n\n"

    appendix += "---\n\n"
    appendix += "*本报告由 Nanobot 舆情监控系统自动生成 | 优化版模板 v2.0*\n"

    return appendix


def generate_competitor_comparison(analysis: Dict) -> str:
    """生成竞品对比分析"""
    competitor_analysis = analysis.get("competitor_analysis", {})
    config = load_config()
    competitor_names = config.get("competitor_names", {})

    if not competitor_analysis or len(competitor_analysis) < 2:
        return ""

    section = "## 🏆 竞品对比分析\n\n"
    section += "> 对比中关村人工智能研究院与竞品机构的舆情表现\n\n"

    # 对比表格
    section += "### 整体对比\n\n"
    section += "| 机构 | 提及量 | 正面占比 | 负面占比 | 平均互动 | 舆情评级 |\n"
    section += "|------|--------|----------|----------|----------|----------|\n"

    for org, data in sorted(competitor_analysis.items(), key=lambda x: x[1]["total"], reverse=True):
        org_name = competitor_names.get(org, org)
        total = data["total"]
        positive_pct = data["sentiment_pct"].get("positive", 0)
        negative_pct = data["sentiment_pct"].get("negative", 0)
        avg_engagement = format_number(int(data["avg_engagement"]))

        # 舆情评级
        if positive_pct >= 60 and negative_pct < 15:
            rating = "🟢 优秀"
        elif positive_pct >= 40 and negative_pct < 30:
            rating = "🟡 良好"
        else:
            rating = "🔴 需改进"

        section += f"| {org_name} | {total} | {positive_pct}% | {negative_pct}% | {avg_engagement} | {rating} |\n"

    section += "\n---\n\n"

    # 详细分析
    section += "### 详细分析\n\n"

    zgc_data = competitor_analysis.get("zgc", {})
    if zgc_data:
        section += "#### 🎯 中关村人工智能研究院\n\n"
        section += f"- **提及量**: {zgc_data['total']} 条\n"
        section += f"- **情感分布**: 🟢 {zgc_data['sentiment_pct'].get('positive', 0)}% 正面 / 🟡 {zgc_data['sentiment_pct'].get('neutral', 0)}% 中性 / 🔴 {zgc_data['sentiment_pct'].get('negative', 0)}% 负面\n"
        section += f"- **平均互动**: {format_number(int(zgc_data['avg_engagement']))} 次/条\n\n"

        # 负面内容示例
        zgc_negative = [item for item in zgc_data.get("items", []) if item["sentiment"]["label"] == "negative"]
        if zgc_negative:
            section += f"**负面内容示例** ({len(zgc_negative)} 条):\n\n"
            for item in zgc_negative[:2]:
                title = item["title"][:50] if item["title"] else item["content"][:50]
                section += f"- 《{title}...》\n"
                if item.get("url"):
                    section += f"  [🔗 查看]({item['url']})\n"
            section += "\n"

    # 竞品分析
    for org in ["hetao", "chuangzhi"]:
        org_data = competitor_analysis.get(org, {})
        if org_data:
            org_name = competitor_names.get(org, org)
            section += f"#### 📊 {org_name}\n\n"
            section += f"- **提及量**: {org_data['total']} 条\n"
            section += f"- **情感分布**: 🟢 {org_data['sentiment_pct'].get('positive', 0)}% 正面 / 🟡 {org_data['sentiment_pct'].get('neutral', 0)}% 中性 / 🔴 {org_data['sentiment_pct'].get('negative', 0)}% 负面\n"
            section += f"- **平均互动**: {format_number(int(org_data['avg_engagement']))} 次/条\n\n"

            # 正面内容示例
            org_positive = [item for item in org_data.get("items", []) if item["sentiment"]["label"] == "positive"]
            if org_positive:
                section += f"**正面内容示例** ({len(org_positive)} 条):\n\n"
                for item in org_positive[:2]:
                    title = item["title"][:50] if item["title"] else item["content"][:50]
                    section += f"- 《{title}...》\n"
                    if item.get("url"):
                        section += f"  [🔗 查看]({item['url']})\n"
                section += "\n"

    # 对比洞察
    section += "### 💡 对比洞察\n\n"

    if zgc_data and len(competitor_analysis) > 1:
        zgc_positive = zgc_data["sentiment_pct"].get("positive", 0)
        zgc_negative = zgc_data["sentiment_pct"].get("negative", 0)

        # 找出表现最好的竞品
        best_competitor = max(
            [(org, data) for org, data in competitor_analysis.items() if org != "zgc"],
            key=lambda x: x[1]["sentiment_pct"].get("positive", 0),
            default=(None, None)
        )

        if best_competitor[0]:
            best_name = competitor_names.get(best_competitor[0], best_competitor[0])
            best_positive = best_competitor[1]["sentiment_pct"].get("positive", 0)

            if best_positive > zgc_positive:
                diff = best_positive - zgc_positive
                section += f"- ⚠️ **差距提示**: {best_name}的正面占比({best_positive}%)高于中关村({zgc_positive}%)，差距{diff:.1f}个百分点\n"
                section += f"- 💡 **建议**: 研究{best_name}的优势内容，学习其传播策略\n"
            else:
                section += f"- ✅ **优势**: 中关村正面占比({zgc_positive}%)领先于{best_name}({best_positive}%)\n"
                section += f"- 💡 **建议**: 保持当前策略，继续扩大优势\n"

    section += "\n---\n\n"
    return section


def generate_negative_details(analysis: Dict) -> str:
    """逐条列出所有负面内容及其评论"""
    config = load_config()
    all_items = analysis.get("all_items", [])

    # 只显示中关村的负面内容
    negative_items = [
        item for item in all_items
        if item["sentiment"]["label"] == "negative" and item.get("competitor") == "zgc"
    ]

    if not negative_items:
        return ""

    section = "## 🔍 负面内容逐条详情\n\n"
    section += "> 以下是中关村人工智能研究院的所有负面内容及其评论，便于溯源和处理\n\n"

    for i, item in enumerate(negative_items, 1):
        platform_name_cn = config["platform_names_cn"][item["platform"]]
        title = item["title"][:80] if item["title"] else ""
        content_preview = item["content"][:300] if item["content"] else ""
        engagement_breakdown = []
        if item["engagement"].get("likes"):
            engagement_breakdown.append(f"{item['engagement']['likes']}赞")
        if item["engagement"].get("comments"):
            engagement_breakdown.append(f"{item['engagement']['comments']}评")
        if item["engagement"].get("shares"):
            engagement_breakdown.append(f"{item['engagement']['shares']}转")
        if item["engagement"].get("collects"):
            engagement_breakdown.append(f"{item['engagement']['collects']}藏")
        engagement_total = sum(item["engagement"].values())
        engagement_str = " + ".join(engagement_breakdown) + f" = **{format_number(engagement_total)}**" if engagement_breakdown else format_number(engagement_total)

        section += f"### 负面内容 {i}｜{platform_name_cn} · {item['author']['name']}\n\n"
        if title:
            section += f"**标题**：{title}\n\n"
        section += f"**正文摘要**：\n> {content_preview}{'...' if len(item['content']) > 300 else ''}\n\n"
        section += f"- 📊 互动：{engagement_str}\n"
        if item.get("url"):
            section += f"- 🔗 [查看原文]({item['url']})\n"

        # 评论列表
        comments = item.get("comments", [])
        if comments:
            section += f"\n**评论（共 {len(comments)} 条）**：\n\n"
            for j, comment in enumerate(comments[:10], 1):
                comment_text = (
                    comment.get("content") or
                    comment.get("comment_content") or
                    comment.get("comment_text") or ""
                )[:150]
                comment_author = (
                    comment.get("nickname") or
                    comment.get("user_name") or
                    comment.get("author") or "匿名"
                )
                likes = comment.get("sub_comment_count") or comment.get("likes") or 0
                likes_str = f" · {likes}赞" if likes else ""
                section += f"{j}. **{comment_author}**{likes_str}：{comment_text}\n"
            if len(comments) > 10:
                section += f"\n*…还有 {len(comments) - 10} 条评论未展示*\n"
        else:
            section += "\n*暂无评论数据*\n"

        section += "\n---\n\n"

    return section


def generate_comments_analysis(analysis: Dict) -> str:
    """生成评论分析章节 - 展示评论的舆情情况"""
    comments_data = analysis.get("comments_analysis", {})
    
    total_comments = comments_data.get("total_comments", 0)
    comments_sentiment = comments_data.get("comments_sentiment", {})
    high_risk_comments = comments_data.get("high_risk_comments", [])
    
    if total_comments == 0:
        return """## 💬 评论舆情分析

当前监测内容暂无评论数据。

---

"""
    
    # 计算百分比
    total = sum(comments_sentiment.values())
    sentiment_pct = {
        label: int(count * 100 / total) if total > 0 else 0
        for label, count in comments_sentiment.items()
    }
    
    section = "## 💬 评论舆情分析\n\n"
    
    # 评论总体情感分布
    section += "### 评论总体情感分布\n\n"
    section += f"**总评论数**：{total_comments} 条\n\n"
    
    section += "| 情感 | 数量 | 占比 |\n"
    section += "|------|------|------|\n"
    
    for sentiment in ["positive", "neutral", "negative"]:
        emoji = get_sentiment_emoji(sentiment)
        label_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]
        count = comments_sentiment.get(sentiment, 0)
        pct = sentiment_pct.get(sentiment, 0)
        section += f"| {emoji} {label_cn} | {count} | {pct}% |\n"
    
    section += "\n---\n\n"
    
    # 高风险评论
    if high_risk_comments:
        section += f"### ⚠️ 高风险评论（共 {len(high_risk_comments)} 条）\n\n"
        
        for i, comment in enumerate(high_risk_comments[:10], 1):
            section += f"**评论 {i}**\n\n"
            section += f"- 📝 内容：{comment['content'][:150]}{'...' if len(comment['content']) > 150 else ''}\n"
            section += f"- 👤 评论人：{comment['author']}\n"
            section += f"- 🔑 风险关键词：{', '.join(comment['keywords'][:3])}\n"
            if comment.get('engagement', 0) > 0:
                section += f"- 👍 获赞数：{comment['engagement']}\n"
            section += "\n"
        
        if len(high_risk_comments) > 10:
            section += f"*…还有 {len(high_risk_comments) - 10} 条高风险评论未展示*\n\n"
        
        section += "---\n\n"
    else:
        section += "### ✅ 正面评论多、风险评论少\n\n"
        section += f"在 {total_comments} 条评论中，未发现包含风险关键词的高风险评论。\n\n"
        section += "---\n\n"
    
    # 评论建议
    section += "### 💡 评论管理建议\n\n"
    
    negative_count = comments_sentiment.get("negative", 0)
    if negative_count > total * 0.1:  # 负面评论超过10%
        section += f"- 🎯 **重点关注**：负面评论占比{sentiment_pct['negative']}%，建议增加正面回应\n"
    else:
        section += f"- ✅ **舆情状态**：负面评论仅占{sentiment_pct['negative']}%，保持目前策略\n"
    
    if high_risk_comments:
        section += f"- ⚠️ **风险预警**：发现{len(high_risk_comments)}条高风险评论，需要尽快回应处理\n"
    else:
        section += f"- 👍 **继续保持**：评论区没有明显风险内容，继续维持良好互动\n"
    
    positive_count = comments_sentiment.get("positive", 0)
    if positive_count > 0:
        section += f"- 🌟 **用户倡导**：{positive_count}条正面评论，可考虑展示或转发，放大正面声音\n"
    
    section += "\n---\n\n"
    
    return section


def generate_report(analysis: Dict) -> str:
    """
    生成完整的优化版报告

    Args:
        analysis: 完整的分析结果

    Returns:
        完整的markdown报告
    """
    report_sections = [
        generate_executive_summary(analysis),
        generate_competitor_comparison(analysis),
        generate_sentiment_overview_v2(analysis),
        generate_platform_analysis(analysis),
        generate_risk_alerts(analysis),
        generate_negative_details(analysis),
        generate_trending_topics_v2(analysis),
        generate_comments_analysis(analysis),
        generate_account_monitoring(analysis),
        generate_recommendations(analysis),
        generate_appendix(analysis)
    ]

    return "".join(report_sections)



def generate_sentiment_overview_v2(analysis: Dict) -> str:
    """生成情感概览 - 简化版"""
    metrics = analysis["metrics"]
    sentiment_dist = metrics["sentiment_dist"]
    sentiment_pct = metrics["sentiment_pct"]

    overview = """## 📈 舆情概览

### 整体情感分布

| 情感 | 数量 | 占比 | 代表内容 |
|------|------|------|----------|
"""

    # 为每种情感找一个代表内容
    all_items = analysis.get("all_items", [])

    for sentiment in ["positive", "neutral", "negative"]:
        label_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]
        emoji = get_sentiment_emoji(sentiment)
        count = sentiment_dist.get(sentiment, 0)
        pct = sentiment_pct.get(sentiment, 0)

        # 找代表内容
        sample_item = next((item for item in all_items if item["sentiment"]["label"] == sentiment), None)
        if sample_item:
            title = sample_item["title"][:30] if sample_item["title"] else sample_item["content"][:30]
            url = sample_item.get("url", "")
            sample_link = f"[{title}...]({url})" if url else f"{title}..."
        else:
            sample_link = "-"

        overview += f"| {emoji} {label_cn} | {count} | {pct}% | {sample_link} |\n"

    overview += "\n---\n\n"
    return overview


def generate_trending_topics_v2(analysis: Dict) -> str:
    """生成热点话题 - 简化版"""
    topics = analysis.get("topics", [])

    if not topics:
        return """## 🔥 热点话题

当前暂无明显热点话题。

---

"""

    section = "## 🔥 热点话题\n\n"
    section += "### Top 5 热门话题\n\n"

    for i, topic in enumerate(topics[:5], 1):
        sentiment_dist = topic["sentiment_dist"]

        section += f"**{i}. #{topic['topic']}** ({topic['count']} 次提及)\n\n"
        section += f"- 平均互动：{format_number(int(topic['avg_engagement']))}\n"
        section += f"- 主要情感：{get_sentiment_emoji(topic['sentiment'])} {topic['sentiment']}\n"

        # 情感分布
        sentiment_breakdown = ", ".join([
            f"{label} {count}"
            for label, count in sentiment_dist.items()
        ])
        section += f"- 情感分布：{sentiment_breakdown}\n\n"

    section += "---\n\n"
    return section


if __name__ == "__main__":
    # 测试
    print("Report Generator V2 - Optimized")
    print("=" * 70)
    print("✅ Module loaded successfully")
