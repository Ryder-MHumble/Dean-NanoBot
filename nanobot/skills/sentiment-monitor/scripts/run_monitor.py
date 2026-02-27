#!/usr/bin/env python3
"""
Sentiment Monitoring Script - Supabase Only

Loads data from Supabase, performs sentiment analysis, and generates report.
No local crawler execution needed.
"""

import json
import os
import sys
from typing import Dict, List, Any

from analyze_sentiment import analyze_all_data
try:
    from generate_report_v2 import generate_report
    print("✅ Using optimized report generator v2.0")
except ImportError:
    from generate_report import generate_report
    print("⚠️  Using legacy report generator")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_all_data(config: Dict) -> tuple[Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    """Load all available data from Supabase."""
    from supabase_client import SentimentSupabaseClient

    print(f"\n📊 Loading data from Supabase...")
    supabase_client = SentimentSupabaseClient(config)

    all_data = {}
    for platform in config["platforms"]:
        items = supabase_client.get_all_contents(platform)
        converted_items = supabase_client.convert_to_legacy_format(items, platform)
        all_data[platform] = converted_items

    total_items = sum(len(data) for data in all_data.values())
    print(f"✅ Loaded {total_items} posts")

    # Load comments
    print(f"\n📊 Loading comments...")
    content_ids = set()
    for platform_data in all_data.values():
        for item in platform_data:
            if isinstance(item, dict):
                for id_field in ['note_id', 'aweme_id', 'video_id', 'mblog_id']:
                    if id_field in item and item[id_field]:
                        content_ids.add(item[id_field])
                        break

    comments_data = supabase_client.get_comments_by_content_ids(list(content_ids))
    print(f"✅ Loaded {sum(len(v) for v in comments_data.values())} comments")

    return all_data, comments_data


def main():
    """Main execution function."""
    print("=" * 70)
    print("🤖 Sentiment Monitoring System")
    print("=" * 70)

    try:
        config = load_config()
        print(f"✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Keywords: {', '.join(config['keywords'])}")
    print(f"📱 Platforms: {', '.join(config['platforms'])}")

    # Load data from Supabase
    print("\n" + "=" * 70)
    print("Step 1: Loading Data from Supabase")
    print("=" * 70)

    all_data, comments_data = load_all_data(config)
    total_items = sum(len(data) for data in all_data.values())

    if total_items == 0:
        print("\n❌ Error: No data found in Supabase", file=sys.stderr)
        sys.exit(1)

    # Perform sentiment analysis
    print("\n" + "=" * 70)
    print("Step 2: Sentiment Analysis")
    print("=" * 70)

    try:
        print("🔄 Analyzing sentiment, detecting risks, extracting topics...")
        analysis = analyze_all_data(all_data, config=config, comments_data=comments_data)
        print("✅ Analysis completed")

        metrics = analysis["metrics"]
        comments_stats = analysis.get("comments_analysis", {})
        print(f"\n📊 Analysis Summary:")
        print(f"   Total items: {metrics['total_items']}")
        print(f"   Total comments: {comments_stats.get('total_comments', 0)}")
        print(f"   Positive: {metrics['sentiment_pct'].get('positive', 0)}%")
        print(f"   Neutral: {metrics['sentiment_pct'].get('neutral', 0)}%")
        print(f"   Negative: {metrics['sentiment_pct'].get('negative', 0)}%")
        print(f"   Risks detected: {len(analysis['risks'])}")
        print(f"   Topics found: {len(analysis['topics'])}")
        print(f"   KOLs identified: {len(analysis['kols'])}")

    except Exception as e:
        print(f"❌ Error during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Generate report
    print("\n" + "=" * 70)
    print("Step 3: Report Generation")
    print("=" * 70)

    try:
        print("🔄 Generating professional report...")
        report = generate_report(analysis)
        print("✅ Report generated successfully")

    except Exception as e:
        print(f"❌ Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Output report
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
