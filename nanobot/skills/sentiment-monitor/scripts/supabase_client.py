#!/usr/bin/env python3
"""
Supabase Client for Sentiment Monitoring
提供与Supabase数据库交互的所有方法
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from supabase import create_client, Client


class SentimentSupabaseClient:
    """舆情监控Supabase客户端"""

    def __init__(self, config: Dict[str, Any]):
        """初始化Supabase客户端"""
        supabase_config = config.get("supabase", {})
        url = supabase_config.get("url") or os.getenv("SUPABASE_URL")
        key = supabase_config.get("key") or os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("Supabase URL and key are required")

        self.client: Client = create_client(url, key)
        print(f"✅ Supabase client initialized: {url}")

    # ==================== 内容数据操作 ====================

    def get_all_contents(self, platform: Optional[str] = None) -> List[Dict]:
        """
        获取所有内容（不限日期）

        Args:
            platform: 平台过滤 (xhs, douyin, bili, wb)，None 表示全平台

        Returns:
            内容列表
        """
        query = self.client.table("contents").select("*")

        if platform:
            query = query.eq("platform", platform)

        try:
            response = query.execute()
            print(f"   Loaded {len(response.data)} items from {platform or 'all platforms'}")
            return response.data
        except Exception as e:
            print(f"❌ Error loading all contents: {e}")
            return []

    def get_contents_by_date(
        self,
        target_date: date,
        platform: Optional[str] = None
    ) -> List[Dict]:
        """
        查询指定日期的内容数据

        Args:
            target_date: 目标日期
            platform: 平台过滤 (xhs, douyin, bili, wb)

        Returns:
            内容列表
        """
        # 由于publish_time字段可能是秒级或毫秒级时间戳，我们需要查询所有数据然后手动过滤
        query = self.client.table("contents").select("*")

        if platform:
            query = query.eq("platform", platform)

        try:
            response = query.execute()

            # 手动过滤日期
            filtered_data = []
            for item in response.data:
                pub_time = item.get("publish_time")
                if pub_time:
                    # 处理两种时间戳格式
                    ts = pub_time if pub_time < 10000000000 else pub_time / 1000
                    try:
                        dt = datetime.fromtimestamp(ts)
                        if dt.date() == target_date:
                            filtered_data.append(item)
                    except:
                        pass

            print(f"   Loaded {len(filtered_data)} items from {platform or 'all platforms'}")
            return filtered_data

        except Exception as e:
            print(f"❌ Error loading contents: {e}")
            return []

    def get_contents_by_date_range(
        self,
        start_date: date,
        end_date: date,
        platform: Optional[str] = None
    ) -> List[Dict]:
        """查询日期范围的内容"""
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())

        query = self.client.table("contents")\
            .select("*")\
            .gte("publish_time", start_ts)\
            .lte("publish_time", end_ts)

        if platform:
            query = query.eq("platform", platform)

        try:
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"❌ Error loading contents: {e}")
            return []

    def get_contents_by_keyword(
        self,
        keyword: str,
        start_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict]:
        """查询包含特定关键词的内容"""
        query = self.client.table("contents")\
            .select("*")\
            .eq("source_keyword", keyword)\
            .order("publish_time", desc=True)\
            .limit(limit)

        if start_date:
            start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            query = query.gte("publish_time", start_ts)

        try:
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"❌ Error loading by keyword: {e}")
            return []

    # ==================== 评论数据操作 ====================

    def get_comments_by_content_ids(
        self,
        content_ids: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        获取指定内容的评论

        Returns:
            {content_id: [comment1, comment2, ...]}
        """
        if not content_ids:
            return {}

        try:
            response = self.client.table("comments")\
                .select("*")\
                .in_("content_id", content_ids)\
                .execute()

            # 按content_id分组
            comments_by_content = {}
            for comment in response.data:
                content_id = comment.get("content_id")
                if content_id not in comments_by_content:
                    comments_by_content[content_id] = []
                comments_by_content[content_id].append(comment)

            return comments_by_content
        except Exception as e:
            print(f"❌ Error loading comments: {e}")
            return {}

    # ==================== 数据转换 ====================

    def convert_to_legacy_format(self, items: List[Dict], platform: str) -> List[Dict]:
        """
        将Supabase数据转换为原有格式（向后兼容）

        Args:
            items: Supabase数据
            platform: 平台标识

        Returns:
            兼容旧格式的数据列表
        """
        converted = []

        for item in items:
            if platform == "xhs":
                converted_item = {
                    "note_id": item.get("content_id"),
                    "type": item.get("content_type", "normal"),
                    "title": item.get("title", ""),
                    "desc": item.get("description", ""),
                    "note_url": item.get("content_url", ""),
                    "time": item.get("publish_time", 0) * 1000,  # 转换为毫秒
                    "user_id": item.get("user_id", ""),
                    "nickname": item.get("nickname", ""),
                    "avatar": item.get("avatar", ""),
                    "liked_count": str(item.get("liked_count", 0)),
                    "comment_count": str(item.get("comment_count", 0)),
                    "share_count": str(item.get("share_count", 0)),
                    "collected_count": str(item.get("collected_count", 0)),
                    "tag_list": "",  # 从platform_data提取
                    "ip_location": item.get("ip_location", ""),
                    "source_keyword": item.get("source_keyword", ""),
                }

            elif platform == "dy" or platform == "douyin":
                converted_item = {
                    "aweme_id": item.get("content_id"),
                    "aweme_type": "0" if item.get("content_type") == "video" else "1",
                    "title": item.get("title", ""),
                    "desc": item.get("description", ""),
                    "aweme_url": item.get("content_url", ""),
                    "create_time": item.get("publish_time", 0),
                    "user_id": item.get("user_id", ""),
                    "nickname": item.get("nickname", ""),
                    "avatar": item.get("avatar", ""),
                    "liked_count": str(item.get("liked_count", 0)),
                    "comment_count": str(item.get("comment_count", 0)),
                    "share_count": str(item.get("share_count", 0)),
                    "collected_count": str(item.get("collected_count", 0)),
                }

            elif platform == "bili":
                converted_item = {
                    "video_id": item.get("content_id"),
                    "video_type": item.get("content_type", "video"),
                    "title": item.get("title", ""),
                    "desc": item.get("description", ""),
                    "video_url": item.get("content_url", ""),
                    "create_time": item.get("publish_time", 0),
                    "user_id": item.get("user_id", ""),
                    "nickname": item.get("nickname", ""),
                    "liked_count": str(item.get("liked_count", 0)),
                    "video_comment": str(item.get("comment_count", 0)),
                    "video_share_count": str(item.get("share_count", 0)),
                    "video_favorite_count": str(item.get("collected_count", 0)),
                    "video_play_count": str(item.get("platform_data", {}).get("video_play_count", 0)),
                }

            elif platform == "wb":
                converted_item = {
                    "mblog_id": item.get("content_id"),
                    "mblog_text": item.get("description", ""),
                    "mblog_url": item.get("content_url", ""),
                    "mblog_created_at": item.get("publish_time", 0),
                    "user_id": item.get("user_id", ""),
                    "nickname": item.get("nickname", ""),
                    "avatar": item.get("avatar", ""),
                    "attitudes_count": str(item.get("liked_count", 0)),
                    "comments_count": str(item.get("comment_count", 0)),
                    "reposts_count": str(item.get("share_count", 0)),
                }

            else:
                continue

            converted.append(converted_item)

        return converted

    # ==================== 统计查询 ====================

    def get_platform_stats(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, int]:
        """获取平台分布统计"""
        contents = self.get_contents_by_date_range(start_date, end_date)

        stats = {}
        for item in contents:
            platform = item.get("platform", "unknown")
            stats[platform] = stats.get(platform, 0) + 1

        return stats

    def get_top_contents(
        self,
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[Dict]:
        """获取高互动内容"""
        contents = self.get_contents_by_date_range(start_date, end_date)

        # 计算总互动量
        for item in contents:
            item["total_engagement"] = (
                item.get("liked_count", 0) +
                item.get("comment_count", 0) +
                item.get("share_count", 0) +
                item.get("collected_count", 0)
            )

        # 排序并返回top N
        sorted_contents = sorted(
            contents,
            key=lambda x: x["total_engagement"],
            reverse=True
        )

        return sorted_contents[:limit]


if __name__ == "__main__":
    # 测试
    print("=" * 70)
    print("Testing Supabase Client")
    print("=" * 70)

    import os
    config = {
        "supabase": {
            "url": os.environ.get("SUPABASE_URL", "https://dfpijqpgsupvdmidztup.supabase.co"),
            "key": os.environ.get("SUPABASE_KEY", "")
        }
    }

    client = SentimentSupabaseClient(config)

    # 测试查询
    today = date.today()
    yesterday = today - timedelta(days=1)

    print(f"\n📊 Testing query for {yesterday}...")
    contents = client.get_contents_by_date(yesterday)
    print(f"   Found {len(contents)} items")

    if contents:
        print(f"\n📝 Sample item:")
        sample = contents[0]
        print(f"   Platform: {sample.get('platform')}")
        print(f"   Title: {sample.get('title', '')[:60]}...")
        print(f"   URL: {sample.get('content_url', '')[:60]}...")

    print("\n✅ Test complete!")
