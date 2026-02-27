#!/usr/bin/env python3
"""
Sentiment Analysis Engine for Social Media Monitoring

This module provides comprehensive sentiment analysis capabilities for
multi-platform social media data, including sentiment classification,
risk detection, trending topic extraction, and KOL identification.
"""

import json
import os
from typing import Dict, List, Any, Tuple
from collections import Counter
from datetime import datetime, date

# Import Supabase client
try:
    from supabase_client import SentimentSupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️  Supabase client not available, will use local data only")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_platform_data(raw_data: List[Dict], platform: str) -> List[Dict]:
    """
    Normalize platform-specific data into unified format.

    Args:
        raw_data: Raw data from platform JSON
        platform: Platform identifier (xhs, douyin, bili, wb)

    Returns:
        List of normalized content items
    """
    normalized = []

    for item in raw_data:
        try:
            if platform == "xhs":
                normalized_item = {
                    "id": item.get("note_id", ""),
                    "platform": "xhs",
                    "type": item.get("type", "note"),
                    "title": item.get("title", ""),
                    "content": f"{item.get('title', '')} {item.get('desc', '')}".strip(),
                    "url": item.get("note_url", ""),
                    "created_at": item.get("time", 0),
                    "author": {
                        "id": item.get("user_id", ""),
                        "name": item.get("nickname", ""),
                        "avatar": item.get("avatar", "")
                    },
                    "engagement": {
                        "likes": int(item.get("liked_count", "0") or "0"),
                        "comments": int(item.get("comment_count", "0") or "0"),
                        "shares": int(item.get("share_count", "0") or "0"),
                        "collects": int(item.get("collected_count", "0") or "0")
                    },
                    "tags": [tag.strip() for tag in item.get("tag_list", "").split(",") if tag.strip()],
                    "raw": item
                }

            elif platform == "dy" or platform == "douyin":
                normalized_item = {
                    "id": item.get("aweme_id", ""),
                    "platform": "dy",
                    "type": "video" if item.get("aweme_type") == "0" else "image",
                    "title": item.get("title", ""),
                    "content": f"{item.get('title', '')} {item.get('desc', '')}".strip(),
                    "url": item.get("aweme_url", ""),
                    "created_at": item.get("create_time", 0),
                    "author": {
                        "id": item.get("user_id", ""),
                        "name": item.get("nickname", ""),
                        "avatar": item.get("avatar", "")
                    },
                    "engagement": {
                        "likes": int(item.get("liked_count", "0") or "0"),
                        "comments": int(item.get("comment_count", "0") or "0"),
                        "shares": int(item.get("share_count", "0") or "0"),
                        "collects": int(item.get("collected_count", "0") or "0")
                    },
                    "tags": [],
                    "raw": item
                }

            elif platform == "bili":
                normalized_item = {
                    "id": str(item.get("video_id", "")),
                    "platform": "bili",
                    "type": item.get("video_type", "video"),
                    "title": item.get("title", ""),
                    "content": f"{item.get('title', '')} {item.get('desc', '')}".strip(),
                    "url": item.get("video_url", ""),
                    "created_at": item.get("create_time", 0),
                    "author": {
                        "id": str(item.get("user_id", "")),
                        "name": item.get("nickname", ""),
                        "avatar": ""
                    },
                    "engagement": {
                        "likes": int(item.get("liked_count", "0") or "0"),
                        "views": int(item.get("video_play_count", "0") or "0"),
                        "favorites": int(item.get("video_favorite_count", "0") or "0"),
                        "shares": int(item.get("video_share_count", "0") or "0"),
                        "comments": int(item.get("video_comment", "0") or "0")
                    },
                    "tags": [],
                    "raw": item
                }

            elif platform == "wb":
                normalized_item = {
                    "id": item.get("mblog_id", ""),
                    "platform": "wb",
                    "type": "post",
                    "title": "",
                    "content": item.get("mblog_text", ""),
                    "url": item.get("mblog_url", ""),
                    "created_at": item.get("mblog_created_at", 0),
                    "author": {
                        "id": str(item.get("user_id", "")),
                        "name": item.get("nickname", ""),
                        "avatar": item.get("avatar", "")
                    },
                    "engagement": {
                        "likes": int(item.get("attitudes_count", "0") or "0"),
                        "comments": int(item.get("comments_count", "0") or "0"),
                        "shares": int(item.get("reposts_count", "0") or "0")
                    },
                    "tags": [],
                    "raw": item
                }

            else:
                continue

            # Skip items without content
            if not normalized_item["content"]:
                continue

            normalized.append(normalized_item)

        except Exception as e:
            print(f"Error normalizing {platform} item: {e}")
            continue

    return normalized


def classify_sentiment(text: str, config: Dict) -> Tuple[str, float, float]:
    """
    Classify sentiment using keyword matching with context awareness.

    Returns:
        Tuple of (label, score, confidence)
    """
    positive_keywords = config["sentiment_keywords"]["positive"]
    negative_keywords = config["sentiment_keywords"]["negative"]
    override_keywords = config.get("positive_override_keywords", [])

    # If text contains positive-context override keywords (e.g. clarification, debunking),
    # negative keyword matches are describing OTHERS' content, not the institution itself.
    has_positive_override = any(kw in text for kw in override_keywords)

    positive_count = sum(1 for kw in positive_keywords if kw in text)
    negative_count = sum(1 for kw in negative_keywords if kw in text)

    # Suppress false-negative: override context neutralizes negative keyword hits
    if has_positive_override and negative_count > 0:
        negative_count = 0

    total_count = positive_count + negative_count

    if total_count == 0:
        return "neutral", 0.0, 0.3

    if positive_count > negative_count:
        label = "positive"
        score = min(1.0, positive_count / total_count)
        confidence = min(1.0, total_count / 5.0)
    elif negative_count > positive_count:
        label = "negative"
        score = -min(1.0, negative_count / total_count)
        confidence = min(1.0, total_count / 5.0)
    else:
        label = "neutral"
        score = 0.0
        confidence = 0.5

    return label, score, confidence


def detect_risks(items: List[Dict], config: Dict) -> List[Dict]:
    """
    Detect risk items that require attention.

    Args:
        items: List of normalized content items with sentiment
        config: Configuration dict

    Returns:
        List of risk items with severity and details
    """
    risks = []
    risk_keywords = config["risk_keywords"]
    high_priority_keywords = config["thresholds"]["risk_priority_high_keywords"]
    override_keywords = config.get("positive_override_keywords", [])

    for item in items:
        # Only flag negative or neutral items
        if item["sentiment"]["label"] not in ["negative", "neutral"]:
            continue

        content = item["content"]
        matched_keywords = [kw for kw in risk_keywords if kw in content]

        if not matched_keywords:
            continue

        # Skip if risk keyword appears in a positive/clarification context
        has_positive_override = any(kw in content for kw in override_keywords)
        if has_positive_override:
            continue

        # Determine severity
        has_high_priority = any(kw in content for kw in high_priority_keywords)
        severity = "high" if has_high_priority else "medium"

        # Calculate engagement level
        engagement_total = sum(item["engagement"].values())

        risks.append({
            "item": item,
            "severity": severity,
            "keywords": matched_keywords,
            "engagement": engagement_total,
            "reason": f"检测到风险关键词: {', '.join(matched_keywords[:3])}"
        })

    # Sort by severity (high first) then engagement (high first)
    risks.sort(key=lambda x: (0 if x["severity"] == "high" else 1, -x["engagement"]))

    return risks


def extract_trending_topics(items: List[Dict]) -> List[Dict]:
    """
    Extract trending topics from content.

    Args:
        items: List of normalized content items

    Returns:
        List of trending topics with stats
    """
    # Collect all tags
    tag_stats = Counter()
    tag_engagement = {}
    tag_sentiment = {}

    for item in items:
        tags = item.get("tags", [])
        engagement = sum(item["engagement"].values())
        sentiment = item["sentiment"]["label"]

        for tag in tags:
            if not tag:
                continue
            tag_stats[tag] += 1
            tag_engagement[tag] = tag_engagement.get(tag, 0) + engagement

            if tag not in tag_sentiment:
                tag_sentiment[tag] = {"positive": 0, "neutral": 0, "negative": 0}
            tag_sentiment[tag][sentiment] += 1

    # Create trending topics list
    topics = []
    for tag, count in tag_stats.most_common(10):
        avg_engagement = tag_engagement[tag] / count
        sentiment_dist = tag_sentiment[tag]

        # Determine dominant sentiment
        dominant_sentiment = max(sentiment_dist, key=sentiment_dist.get)

        topics.append({
            "topic": tag,
            "count": count,
            "avg_engagement": avg_engagement,
            "sentiment": dominant_sentiment,
            "sentiment_dist": sentiment_dist
        })

    return topics


def identify_kols(items: List[Dict], config: Dict) -> List[Dict]:
    """
    Identify Key Opinion Leaders (KOLs) from content creators.

    Args:
        items: List of normalized content items
        config: Configuration dict

    Returns:
        List of KOL accounts with stats
    """
    author_stats = {}

    for item in items:
        author_id = item["author"]["id"]
        author_name = item["author"]["name"]

        if not author_id or not author_name:
            continue

        if author_id not in author_stats:
            author_stats[author_id] = {
                "id": author_id,
                "name": author_name,
                "platform": item["platform"],
                "post_count": 0,
                "total_engagement": 0,
                "posts": []
            }

        author_stats[author_id]["post_count"] += 1
        author_stats[author_id]["total_engagement"] += sum(item["engagement"].values())
        author_stats[author_id]["posts"].append(item)

    # Filter and sort KOLs by engagement
    kols = [
        author for author in author_stats.values()
        if author["total_engagement"] > 100  # Minimum threshold
    ]

    kols.sort(key=lambda x: x["total_engagement"], reverse=True)

    return kols[:10]  # Top 10 KOLs


def aggregate_metrics(items: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate overall metrics from all items.

    Args:
        items: List of normalized content items with sentiment

    Returns:
        Dict of aggregated metrics
    """
    total_items = len(items)

    if total_items == 0:
        return {
            "total_items": 0,
            "sentiment_dist": {"positive": 0, "neutral": 0, "negative": 0},
            "sentiment_pct": {"positive": 0, "neutral": 0, "negative": 0},
            "total_engagement": 0,
            "avg_engagement": 0,
            "platform_dist": {}
        }

    # Sentiment distribution
    sentiment_dist = Counter(item["sentiment"]["label"] for item in items)
    sentiment_pct = {
        label: round(count / total_items * 100, 1)
        for label, count in sentiment_dist.items()
    }

    # Engagement stats
    total_engagement = sum(sum(item["engagement"].values()) for item in items)
    avg_engagement = round(total_engagement / total_items, 1)

    # Platform distribution
    platform_dist = Counter(item["platform"] for item in items)

    return {
        "total_items": total_items,
        "sentiment_dist": dict(sentiment_dist),
        "sentiment_pct": sentiment_pct,
        "total_engagement": total_engagement,
        "avg_engagement": avg_engagement,
        "platform_dist": dict(platform_dist)
    }


def analyze_platform_data(platform_items: List[Dict], config: Dict) -> Dict[str, Any]:
    """
    Analyze data for a specific platform.

    Args:
        platform_items: List of items from one platform
        config: Configuration dict

    Returns:
        Platform analysis results
    """
    if not platform_items:
        return {
            "total_items": 0,
            "sentiment_dist": {},
            "avg_engagement": 0,
            "top_posts": [],
            "topics": []
        }

    platform = platform_items[0]["platform"]

    # Sentiment distribution
    sentiment_dist = Counter(item["sentiment"]["label"] for item in platform_items)

    # Average engagement
    total_engagement = sum(sum(item["engagement"].values()) for item in platform_items)
    avg_engagement = round(total_engagement / len(platform_items), 1)

    # Top posts by engagement
    sorted_items = sorted(
        platform_items,
        key=lambda x: sum(x["engagement"].values()),
        reverse=True
    )
    top_posts = sorted_items[:5]

    # Extract topics/tags
    topics = extract_trending_topics(platform_items)

    return {
        "platform": platform,
        "total_items": len(platform_items),
        "sentiment_dist": dict(sentiment_dist),
        "avg_engagement": avg_engagement,
        "top_posts": top_posts,
        "topics": topics[:5]
    }


def load_data_from_supabase(config: Dict, target_date: str) -> Dict[str, List[Dict]]:
    """
    从Supabase加载数据

    Args:
        config: 配置字典
        target_date: 目标日期 (YYYY-MM-DD)

    Returns:
        Dict mapping platform to raw data lists
    """
    if not SUPABASE_AVAILABLE:
        raise ImportError("Supabase client not available")

    # 创建Supabase客户端
    supabase_client = SentimentSupabaseClient(config)

    # 解析日期
    if isinstance(target_date, str):
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        target_date_obj = target_date

    print(f"\n📊 Loading data from Supabase for {target_date_obj}...")

    all_data = {}
    platforms = config.get("platforms", ["xhs", "douyin", "bili", "wb"])

    for platform in platforms:
        # 从Supabase读取数据
        items = supabase_client.get_contents_by_date(target_date_obj, platform)

        # 转换为旧格式（向后兼容）
        converted_items = supabase_client.convert_to_legacy_format(items, platform)

        all_data[platform] = converted_items
        print(f"   {platform}: {len(converted_items)} items")

    return all_data


def classify_competitor(text: str, config: Dict) -> str:
    """判断内容属于哪个机构"""
    competitor_keywords = config.get("competitor_keywords", {})
    for org, keywords in competitor_keywords.items():
        if any(kw in text for kw in keywords):
            return org
    return "unknown"


def analyze_all_data(
    all_data: Dict[str, List[Dict]] = None,
    config: Dict = None,
    target_date: str = None,
    comments_data: Dict[str, List[Dict]] = None
) -> Dict[str, Any]:
    """
    Perform complete sentiment analysis on all platform data.

    Args:
        all_data: Dict mapping platform to raw data lists (optional, for backward compatibility)
        config: Configuration dict (required if loading from Supabase)
        target_date: Target date string YYYY-MM-DD (required if loading from Supabase)
        comments_data: Dict mapping content_id to list of comment dicts

    Returns:
        Complete analysis results
    """
    if config is None:
        config = load_config()

    # 如果没有提供all_data，从Supabase加载
    if all_data is None:
        data_source = config.get("data_source", "local")

        if data_source == "supabase":
            if not target_date:
                raise ValueError("target_date is required when using Supabase data source")
            all_data = load_data_from_supabase(config, target_date)
        else:
            raise ValueError("all_data must be provided when data_source is not 'supabase'")

    # 如果没有提供comments_data，初始化为空
    if comments_data is None:
        comments_data = {}

    # Normalize all data
    all_items = []
    for platform, raw_items in all_data.items():
        normalized = normalize_platform_data(raw_items, platform)
        all_items.extend(normalized)

    # Classify sentiment and competitor for all items
    for item in all_items:
        label, score, confidence = classify_sentiment(item["content"], config)
        item["sentiment"] = {
            "label": label,
            "score": score,
            "confidence": confidence
        }
        item["competitor"] = classify_competitor(item["content"], config)

    # ==================== 关联和分析评论数据 ====================
    comments_analysis = {
        "total_comments": 0,
        "comments_sentiment": {"positive": 0, "neutral": 0, "negative": 0},
        "high_risk_comments": []
    }
    
    if comments_data:
        print(f"   Processing {sum(len(v) for v in comments_data.values())} comments...")
        for item in all_items:
            # 为每个item关联评论
            item_id = item.get("id", "")
            item_comments = comments_data.get(item_id, [])
            
            if item_comments:
                item["comments"] = item_comments
                item["comment_sentiment_dist"] = {"positive": 0, "neutral": 0, "negative": 0}
                
                # 分析每条评论的情感
                for comment in item_comments:
                    comment_text = comment.get("content", "")
                    if comment_text:
                        label, score, confidence = classify_sentiment(comment_text, config)
                        comment["sentiment"] = {"label": label, "score": score}
                        
                        # 更新统计
                        item["comment_sentiment_dist"][label] = item["comment_sentiment_dist"].get(label, 0) + 1
                        comments_analysis["comments_sentiment"][label] += 1
                        comments_analysis["total_comments"] += 1
                        
                        # 检测高风险评论
                        if label == "negative":
                            risk_keywords = config.get("risk_keywords", [])
                            matched_keywords = [kw for kw in risk_keywords if kw in comment_text]
                            if matched_keywords:
                                comments_analysis["high_risk_comments"].append({
                                    "content": comment_text,
                                    "keywords": matched_keywords,
                                    "parent_content_id": item_id,
                                    "author": comment.get("nickname", "Unknown"),
                                    "engagement": comment.get("like_count", 0)
                                })
            else:
                item["comments"] = []
                item["comment_sentiment_dist"] = {"positive": 0, "neutral": 0, "negative": 0}

    # Perform analysis
    metrics = aggregate_metrics(all_items)
    risks = detect_risks(all_items, config)
    topics = extract_trending_topics(all_items)
    kols = identify_kols(all_items, config)

    # Platform-specific analysis
    platform_analysis = {}
    for platform in config["platforms"]:
        platform_items = [item for item in all_items if item["platform"] == platform]
        platform_analysis[platform] = analyze_platform_data(platform_items, config)

    # 计算数据日期范围
    data_date_label = "全量数据"
    if all_items:
        timestamps = [
            item["created_at"] for item in all_items
            if item.get("created_at") and item["created_at"] > 0
        ]
        if timestamps:
            ts_min = min(t if t < 10000000000 else t / 1000 for t in timestamps)
            ts_max = max(t if t < 10000000000 else t / 1000 for t in timestamps)
            try:
                date_min = datetime.fromtimestamp(ts_min).strftime("%Y-%m-%d")
                date_max = datetime.fromtimestamp(ts_max).strftime("%Y-%m-%d")
                data_date_label = f"{date_min} ~ {date_max}" if date_min != date_max else date_min
            except Exception:
                pass

    # 竞品对比分析
    competitor_analysis = {}
    competitor_keywords = config.get("competitor_keywords", {})
    for org in competitor_keywords.keys():
        org_items = [item for item in all_items if item.get("competitor") == org]
        if org_items:
            org_sentiment = Counter(item["sentiment"]["label"] for item in org_items)
            org_total = len(org_items)
            competitor_analysis[org] = {
                "total": org_total,
                "sentiment_dist": dict(org_sentiment),
                "sentiment_pct": {k: round(v/org_total*100, 1) for k, v in org_sentiment.items()},
                "avg_engagement": round(sum(sum(item["engagement"].values()) for item in org_items) / org_total, 1) if org_total > 0 else 0,
                "items": org_items
            }

    return {
        "metadata": {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_platforms": len(all_data),
            "data_date": data_date_label
        },
        "metrics": metrics,
        "risks": risks,
        "topics": topics[:10],
        "kols": kols,
        "platform_analysis": platform_analysis,
        "all_items": all_items,
        "comments_analysis": comments_analysis,
        "competitor_analysis": competitor_analysis
    }


if __name__ == "__main__":
    # Test with sample data
    print("Sentiment Analysis Engine")
    print("=" * 50)

    # Load config
    config = load_config()
    print(f"Loaded config: {len(config['platforms'])} platforms")

    # Test sentiment classification
    test_texts = [
        "这个研究院很好，老师很专业，推荐！",
        "有点失望，感觉不太满意",
        "今天去参观了一下"
    ]

    print("\nTesting sentiment classification:")
    for text in test_texts:
        label, score, confidence = classify_sentiment(text, config)
        print(f"  '{text}' -> {label} (score: {score:.2f}, confidence: {confidence:.2f})")
