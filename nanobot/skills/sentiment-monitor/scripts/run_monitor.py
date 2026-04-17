#!/usr/bin/env python3
"""
Sentiment Monitoring Script - Dual Dimension

加载官方账号数据 + 关键词搜索数据，分别分析后生成双维度报告：
  维度一：官方账号运营分析
  维度二：全网舆情洞察
"""

import json
import os
import sys
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# 加载 .env 文件（从项目根目录向上查找）
try:
    from dotenv import load_dotenv
    _here = Path(__file__).resolve()
    for _parent in [_here.parent, _here.parent.parent, _here.parent.parent.parent,
                    _here.parent.parent.parent.parent, _here.parent.parent.parent.parent.parent]:
        _env = _parent / ".env"
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass  # dotenv 不可用时静默跳过，依赖已设置的环境变量

from analyze_sentiment import analyze_all_data, analyze_account_data
try:
    from generate_report_v2 import generate_report
    print("✅ Using dual-dimension report generator v3.0")
except ImportError:
    from generate_report import generate_report
    print("⚠️  Using legacy report generator")

from validate_intel_report import validate_report_text


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json, expanding ${VAR} placeholders."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    expanded = os.path.expandvars(raw)
    return json.loads(expanded)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dual-dimension sentiment monitoring")
    parser.add_argument(
        "--mode",
        default="standard",
        choices=["standard", "fast"],
        help="Report generation mode. Default: standard",
    )
    parser.add_argument(
        "--date",
        dest="target_date",
        default=None,
        help="Optional target date in YYYY-MM-DD. If omitted, use all available data.",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip report quality-gate validation.",
    )
    return parser.parse_args()


def parse_target_date(date_text: Optional[str]) -> Optional[date]:
    if not date_text:
        return None
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid --date value: {date_text}, expected YYYY-MM-DD") from exc


def _extract_publish_date(item: Dict[str, Any]) -> Optional[date]:
    publish_time = item.get("publish_time")
    if publish_time is None:
        return None

    try:
        ts = float(publish_time)
    except (TypeError, ValueError):
        return None

    # Support second-level and millisecond-level timestamps.
    if ts > 10_000_000_000:
        ts /= 1000

    try:
        return datetime.fromtimestamp(ts).date()
    except (OverflowError, OSError, ValueError):
        return None


def _filter_items_by_date(items: List[Dict[str, Any]], target_date: Optional[date], label: str) -> List[Dict[str, Any]]:
    if target_date is None:
        return items

    filtered = [item for item in items if _extract_publish_date(item) == target_date]
    print(f"✅ Date filter ({target_date}) applied to {label}: {len(filtered)}/{len(items)} kept")
    return filtered


def load_official_data(config: Dict, target_date: Optional[date] = None) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
    """
    加载官方账号数据（source_keyword LIKE '@%'）及其评论。

    Returns:
        (account_items_raw, comments_by_id)
    """
    from supabase_client import SentimentSupabaseClient

    print(f"\n📊 Loading official account data...")
    supabase_client = SentimentSupabaseClient(config)

    account_items = supabase_client.get_official_account_contents()
    account_items = _filter_items_by_date(account_items, target_date, "official account posts")
    print(f"✅ Loaded {len(account_items)} official account posts")

    if not account_items:
        return [], {}

    content_ids = [item["content_id"] for item in account_items if item.get("content_id")]
    comments_data = supabase_client.get_comments_by_content_ids(content_ids)
    total_comments = sum(len(v) for v in comments_data.values())
    print(f"✅ Loaded {total_comments} comments for official account posts")

    return account_items, comments_data


def load_keyword_data(config: Dict, target_date: Optional[date] = None) -> Tuple[Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    """
    加载关键词搜索数据（source_keyword NOT LIKE '@%'）及其评论。

    Returns:
        (all_data_by_platform, comments_by_id)
    """
    from supabase_client import SentimentSupabaseClient

    print(f"\n📊 Loading keyword search data...")
    supabase_client = SentimentSupabaseClient(config)

    all_data = {}
    for platform in config["platforms"]:
        raw_items = supabase_client.get_keyword_search_contents(platform)
        raw_items = _filter_items_by_date(raw_items, target_date, f"{platform} keyword posts")
        converted = supabase_client.convert_to_legacy_format(raw_items, platform)
        all_data[platform] = converted

    total_items = sum(len(d) for d in all_data.values())
    print(f"✅ Loaded {total_items} keyword search posts")

    if total_items == 0:
        return all_data, {}

    # 收集所有 content_id（保持稳定顺序）以便加载评论
    content_ids: List[str] = []
    seen_content_ids = set()
    for platform_data in all_data.values():
        for item in platform_data:
            for id_field in ['note_id', 'aweme_id', 'video_id', 'mblog_id']:
                if id_field in item and item[id_field]:
                    content_id = item[id_field]
                    if content_id not in seen_content_ids:
                        seen_content_ids.add(content_id)
                        content_ids.append(content_id)
                    break

    comments_data = supabase_client.get_comments_by_content_ids(content_ids)
    total_comments = sum(len(v) for v in comments_data.values())
    print(f"✅ Loaded {total_comments} comments for keyword search posts")

    return all_data, comments_data


def main():
    """Main execution function."""
    args = parse_args()
    try:
        target_date_obj = parse_target_date(args.target_date)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)

    print("=" * 70)
    print("🤖 Sentiment Monitoring System - Dual Dimension v3.0")
    print("=" * 70)

    try:
        config = load_config()
        print(f"✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Keywords: {', '.join(config['keywords'])}")
    print(f"📱 Platforms: {', '.join(config['platforms'])}")
    print(f"🧩 Report mode: {args.mode}")
    if target_date_obj:
        print(f"📅 Date filter: {target_date_obj}")
    else:
        print("📅 Date filter: all available data")

    account_analysis = None
    fullvolume_analysis = None

    # ── Dimension 1: Official Account Data ──────────────────────────────
    print("\n" + "=" * 70)
    print("Step 1: Loading Official Account Data")
    print("=" * 70)

    try:
        account_items_raw, account_comments = load_official_data(config, target_date_obj)
        if account_items_raw:
            print("\n🔄 Analyzing official account data...")
            account_analysis = analyze_account_data(account_items_raw, account_comments, config)
            print(f"✅ Account analysis complete: {account_analysis['total_posts']} posts, "
                  f"{account_analysis['total_comments']} comments")
        else:
            print("⚠️  No official account data found, skipping account dimension")
    except Exception as e:
        print(f"⚠️  Account data loading failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    # ── Dimension 2: Keyword Search Data ────────────────────────────────
    print("\n" + "=" * 70)
    print("Step 2: Loading Keyword Search Data")
    print("=" * 70)

    try:
        keyword_data, keyword_comments = load_keyword_data(config, target_date_obj)
        total_keyword_items = sum(len(d) for d in keyword_data.values())

        if total_keyword_items > 0:
            print("\n🔄 Analyzing keyword search data...")
            fullvolume_analysis = analyze_all_data(
                all_data=keyword_data,
                config=config,
                comments_data=keyword_comments
            )
            metrics = fullvolume_analysis["metrics"]
            print(f"✅ Full-volume analysis complete:")
            print(f"   Total items: {metrics['total_items']}")
            print(f"   Positive: {metrics['sentiment_pct'].get('positive', 0)}%")
            print(f"   Neutral:  {metrics['sentiment_pct'].get('neutral', 0)}%")
            print(f"   Negative: {metrics['sentiment_pct'].get('negative', 0)}%")
            print(f"   Risks detected: {len(fullvolume_analysis['risks'])}")
        else:
            print("⚠️  No keyword search data found, skipping full-volume dimension")
    except Exception as e:
        print(f"⚠️  Keyword data loading failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    if account_analysis is None and fullvolume_analysis is None:
        print("\n❌ Error: No data available for any dimension", file=sys.stderr)
        sys.exit(1)

    # ── Report Generation ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("Step 3: Report Generation")
    print("=" * 70)

    try:
        print("🔄 Generating focused sentiment action report...")
        combined_analysis = {
            "metadata": {
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_date": args.target_date or "全量数据",
                "mode": args.mode,
            }
        }
        if account_analysis is not None:
            combined_analysis["account_analysis"] = account_analysis
        if fullvolume_analysis is not None:
            combined_analysis["fullvolume_analysis"] = fullvolume_analysis
            if not args.target_date:
                combined_analysis["metadata"]["data_date"] = fullvolume_analysis.get(
                    "metadata", {}
                ).get("data_date", "全量数据")

        try:
            report = generate_report(combined_analysis, mode=args.mode)
        except TypeError:
            # Legacy generator compatibility
            report = generate_report(combined_analysis)
        print("✅ Report generated successfully")
    except Exception as e:
        print(f"❌ Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ── Validation ───────────────────────────────────────────────────────
    if not args.skip_validate:
        print("\n" + "=" * 70)
        print("Step 4: Quality Gate Validation")
        print("=" * 70)

        max_chars = 5500 if args.mode == "fast" else 8000
        require_action_checklist = fullvolume_analysis is not None
        require_priority = bool(
            fullvolume_analysis
            and (
                fullvolume_analysis.get("risks")
                or fullvolume_analysis.get("competitor_analysis")
            )
        )
        require_links = require_priority

        errors, metrics = validate_report_text(
            report,
            require_priority=require_priority,
            require_links=require_links,
            require_dual_dimensions=False,
            require_action_checklist=require_action_checklist,
            require_primary_monitoring=bool(fullvolume_analysis),
            require_benchmark_section=bool(
                fullvolume_analysis and fullvolume_analysis.get("competitor_analysis")
            ),
            require_relevance_reasons=bool(
                fullvolume_analysis and fullvolume_analysis.get("risks")
            ),
            max_chars=max_chars,
            allow_missing_links=0,
        )
        if errors:
            print("❌ Report validation failed:", file=sys.stderr)
            for err in errors:
                print(f"   - {err}", file=sys.stderr)
            sys.exit(1)

        print("✅ Report validation passed")
        print(
            "   metrics: "
            f"chars={metrics.get('char_count', 0)}, "
            f"priorities={metrics.get('priority_labels', 0)}, "
            f"urls={metrics.get('urls', 0)}, "
            f"missing_links={metrics.get('missing_link_marks', 0)}, "
            f"checklist_items={metrics.get('checklist_items', 0)}"
        )

    # ── Output ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("GENERATED REPORT")
    print("=" * 70 + "\n")
    print(report)

    print("\n" + "=" * 70)
    print("✅ Sentiment monitoring completed successfully")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
