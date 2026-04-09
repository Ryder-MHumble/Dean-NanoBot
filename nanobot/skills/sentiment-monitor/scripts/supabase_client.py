#!/usr/bin/env python3
"""
Compatibility client for sentiment monitoring data access.

Historical name kept as `SentimentSupabaseClient` to avoid changing existing
callers, but data now comes from DeanAgent-Backend HTTP APIs backed by local
PostgreSQL.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from urllib.parse import quote
from typing import Any, Dict, List, Optional

import requests


class SentimentSupabaseClient:
    """Sentiment monitoring client backed by DeanAgent-Backend APIs."""

    def __init__(self, config: Dict[str, Any]):
        backend_cfg = config.get("backend_api", {})

        env_base_url = (
            os.getenv("DEAN_BACKEND_API_BASE_URL")
            or os.getenv("BACKEND_API_BASE_URL")
            or os.getenv("NANOBOT_BACKEND_API_BASE_URL")
        )
        base_url = (env_base_url or backend_cfg.get("base_url") or "http://127.0.0.1:8001").strip()

        if not base_url.startswith(("http://", "https://")):
            raise ValueError("Invalid backend API base URL")

        self.base_url = base_url.rstrip("/")
        self.api_prefix = backend_cfg.get("api_prefix", "/api/v1").rstrip("/")
        self.timeout_seconds = int(backend_cfg.get("timeout_seconds", 15))
        self.page_size = max(1, min(100, int(backend_cfg.get("page_size", 100))))
        self.max_pages = max(1, int(backend_cfg.get("max_pages", 50)))
        self.max_detail_requests = max(1, int(backend_cfg.get("max_detail_requests", 200)))

        self.session = requests.Session()
        api_key = (backend_cfg.get("api_key") or os.getenv("BACKEND_API_KEY") or "").strip()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

        print(f"✅ Backend API client initialized: {self.base_url}{self.api_prefix}")

    # ==================== HTTP Helpers ====================

    def _url(self, path: str) -> str:
        return f"{self.base_url}{self.api_prefix}{path}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(
                self._url(path),
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            print(f"❌ API request failed: GET {path} params={params} err={exc}")
            return None

    @staticmethod
    def _normalize_platform(platform: Optional[str]) -> Optional[str]:
        if not platform:
            return None
        p = platform.strip().lower()
        mapping = {
            "douyin": "dy",
            "dy": "dy",
            "bilibili": "bili",
            "bili": "bili",
            "weibo": "wb",
            "wb": "wb",
            "xhs": "xhs",
            "zhihu": "zhihu",
        }
        return mapping.get(p, p)

    def _fetch_feed_all(
        self,
        platform: Optional[str] = None,
        sort_by: str = "publish_time",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        normalized_platform = self._normalize_platform(platform)

        items: List[Dict[str, Any]] = []
        total_pages: Optional[int] = None

        for page in range(1, self.max_pages + 1):
            params: Dict[str, Any] = {
                "page": page,
                "page_size": self.page_size,
                "sort_by": sort_by,
                "sort_order": sort_order,
            }
            if normalized_platform:
                params["platform"] = normalized_platform

            payload = self._get("/sentiment/feed", params=params)
            if payload is None:
                break

            page_items = payload.get("items", []) or []
            items.extend(page_items)

            if total_pages is None:
                raw_total_pages = payload.get("total_pages")
                total_pages = int(raw_total_pages) if raw_total_pages else 1

            if page >= total_pages:
                break

        if total_pages and total_pages > self.max_pages:
            print(
                "⚠️  Feed pages truncated by max_pages: "
                f"fetched={self.max_pages}, available={total_pages}"
            )

        return items

    @staticmethod
    def _publish_date(item: Dict[str, Any]) -> Optional[date]:
        raw_ts = item.get("publish_time")
        if raw_ts is None:
            return None

        try:
            ts = float(raw_ts)
        except (TypeError, ValueError):
            return None

        if ts > 10_000_000_000:
            ts /= 1000

        try:
            return datetime.fromtimestamp(ts).date()
        except (OverflowError, OSError, ValueError):
            return None

    @staticmethod
    def _is_official(item: Dict[str, Any]) -> bool:
        source_keyword = (item.get("source_keyword") or "").strip()
        return source_keyword.startswith("@")

    # ==================== Contents ====================

    def get_all_contents(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self._fetch_feed_all(platform=platform)
        print(f"   Loaded {len(items)} items from {platform or 'all platforms'}")
        return items

    def get_contents_by_date(self, target_date: date, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self._fetch_feed_all(platform=platform)
        filtered = [it for it in items if self._publish_date(it) == target_date]
        print(f"   Loaded {len(filtered)} items from {platform or 'all platforms'}")
        return filtered

    def get_contents_by_date_range(
        self,
        start_date: date,
        end_date: date,
        platform: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        items = self._fetch_feed_all(platform=platform)
        filtered: List[Dict[str, Any]] = []
        for item in items:
            item_date = self._publish_date(item)
            if item_date is None:
                continue
            if start_date <= item_date <= end_date:
                filtered.append(item)
        return filtered

    def get_contents_by_keyword(
        self,
        keyword: str,
        start_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        items = self._fetch_feed_all()
        filtered = [it for it in items if (it.get("source_keyword") or "").strip() == keyword]

        if start_date:
            filtered = [it for it in filtered if (self._publish_date(it) and self._publish_date(it) >= start_date)]

        return filtered[:limit]

    # ==================== Comments ====================

    def get_comments_by_content_ids(self, content_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        if not content_ids:
            return {}

        comments_by_content: Dict[str, List[Dict[str, Any]]] = {}
        unique_ids = list(dict.fromkeys(cid for cid in content_ids if cid))

        if len(unique_ids) > self.max_detail_requests:
            print(
                "⚠️  Content detail requests truncated by max_detail_requests: "
                f"fetched={self.max_detail_requests}, requested={len(unique_ids)}"
            )
            unique_ids = unique_ids[: self.max_detail_requests]

        for content_id in unique_ids:
            encoded_content_id = quote(str(content_id), safe="")
            payload = self._get(f"/sentiment/content/{encoded_content_id}")
            if payload is None:
                comments_by_content[content_id] = []
                continue

            comments = payload.get("comments")
            if comments is None and isinstance(payload.get("data"), dict):
                comments = payload["data"].get("comments")
            if comments is None:
                comments = []
            comments_by_content[content_id] = comments

        return comments_by_content

    # ==================== Data Conversion ====================

    def convert_to_legacy_format(self, items: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        converted: List[Dict[str, Any]] = []
        platform_norm = self._normalize_platform(platform)

        for item in items:
            p = self._normalize_platform(item.get("platform"))
            if platform_norm and p != platform_norm:
                continue

            publish_time = item.get("publish_time", 0) or 0
            # Keep legacy behavior: xhs expects ms, others mostly seconds.
            publish_time_seconds = int(publish_time / 1000) if publish_time > 10_000_000_000 else int(publish_time)

            if p == "xhs":
                converted_item = {
                    "note_id": item.get("content_id"),
                    "type": item.get("content_type", "normal"),
                    "title": item.get("title", "") or "",
                    "desc": item.get("description", "") or "",
                    "note_url": item.get("content_url", "") or "",
                    "time": publish_time if publish_time > 10_000_000_000 else publish_time * 1000,
                    "user_id": item.get("user_id", "") or "",
                    "nickname": item.get("nickname", "") or "",
                    "avatar": item.get("avatar", "") or "",
                    "liked_count": str(item.get("liked_count", 0) or 0),
                    "comment_count": str(item.get("comment_count", 0) or 0),
                    "share_count": str(item.get("share_count", 0) or 0),
                    "collected_count": str(item.get("collected_count", 0) or 0),
                    "tag_list": (item.get("platform_data") or {}).get("tag_list", ""),
                    "ip_location": item.get("ip_location", "") or "",
                    "source_keyword": item.get("source_keyword", "") or "",
                }
            elif p == "dy":
                converted_item = {
                    "aweme_id": item.get("content_id"),
                    "aweme_type": "0" if item.get("content_type") == "video" else "1",
                    "title": item.get("title", "") or "",
                    "desc": item.get("description", "") or "",
                    "aweme_url": item.get("content_url", "") or "",
                    "create_time": publish_time_seconds,
                    "user_id": item.get("user_id", "") or "",
                    "nickname": item.get("nickname", "") or "",
                    "avatar": item.get("avatar", "") or "",
                    "liked_count": str(item.get("liked_count", 0) or 0),
                    "comment_count": str(item.get("comment_count", 0) or 0),
                    "share_count": str(item.get("share_count", 0) or 0),
                    "collected_count": str(item.get("collected_count", 0) or 0),
                }
            elif p == "bili":
                converted_item = {
                    "video_id": item.get("content_id"),
                    "video_type": item.get("content_type", "video") or "video",
                    "title": item.get("title", "") or "",
                    "desc": item.get("description", "") or "",
                    "video_url": item.get("content_url", "") or "",
                    "create_time": publish_time_seconds,
                    "user_id": item.get("user_id", "") or "",
                    "nickname": item.get("nickname", "") or "",
                    "liked_count": str(item.get("liked_count", 0) or 0),
                    "video_comment": str(item.get("comment_count", 0) or 0),
                    "video_share_count": str(item.get("share_count", 0) or 0),
                    "video_favorite_count": str(item.get("collected_count", 0) or 0),
                    "video_play_count": str((item.get("platform_data") or {}).get("video_play_count", 0) or 0),
                }
            elif p in {"wb", "weibo"}:
                converted_item = {
                    "mblog_id": item.get("content_id"),
                    "mblog_text": item.get("description", "") or "",
                    "mblog_url": item.get("content_url", "") or "",
                    "mblog_created_at": publish_time_seconds,
                    "user_id": item.get("user_id", "") or "",
                    "nickname": item.get("nickname", "") or "",
                    "avatar": item.get("avatar", "") or "",
                    "attitudes_count": str(item.get("liked_count", 0) or 0),
                    "comments_count": str(item.get("comment_count", 0) or 0),
                    "reposts_count": str(item.get("share_count", 0) or 0),
                }
            else:
                continue

            converted.append(converted_item)

        return converted

    # ==================== Skill-specific data loaders ====================

    def get_official_account_contents(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._fetch_feed_all(platform=platform)
        official = [row for row in rows if self._is_official(row)]
        print(f"   Loaded {len(official)} official account items from {platform or 'all platforms'}")
        return official

    def get_keyword_search_contents(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._fetch_feed_all(platform=platform)
        keyword_rows = [row for row in rows if not self._is_official(row)]
        print(f"   Loaded {len(keyword_rows)} keyword search items from {platform or 'all platforms'}")
        return keyword_rows

    # ==================== Aggregate helpers ====================

    def get_platform_stats(self, start_date: date, end_date: date) -> Dict[str, int]:
        contents = self.get_contents_by_date_range(start_date, end_date)
        stats: Dict[str, int] = {}
        for item in contents:
            platform = item.get("platform", "unknown")
            stats[platform] = stats.get(platform, 0) + 1
        return stats

    def get_top_contents(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        contents = self.get_contents_by_date_range(start_date, end_date)
        for item in contents:
            item["total_engagement"] = (
                (item.get("liked_count") or 0)
                + (item.get("comment_count") or 0)
                + (item.get("share_count") or 0)
                + (item.get("collected_count") or 0)
            )

        sorted_contents = sorted(contents, key=lambda x: x["total_engagement"], reverse=True)
        return sorted_contents[:limit]


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Sentiment API Client")
    print("=" * 70)

    client = SentimentSupabaseClient({})
    today = date.today()

    print(f"\n📊 Testing query for {today}...")
    contents = client.get_contents_by_date(today)
    print(f"   Found {len(contents)} items")

    if contents:
        sample = contents[0]
        print(f"\n📝 Sample item platform: {sample.get('platform')}")
        print(f"   Title: {(sample.get('title') or '')[:60]}...")
        print(f"   URL: {(sample.get('content_url') or '')[:60]}...")

    print("\n✅ Test complete!")
