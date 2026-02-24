#!/usr/bin/env python3
"""
Sentiment Monitoring Orchestration Script

This script coordinates the entire sentiment monitoring workflow:
1. Execute MediaCrawler to collect data
2. Load data from all platforms
3. Perform sentiment analysis
4. Generate professional report
5. Output report to stdout
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import analysis modules
try:
    from analyze_sentiment import analyze_all_data
    from generate_report import generate_report
except ImportError:
    # Try relative import if running as script
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from analyze_sentiment import analyze_all_data
    from generate_report import generate_report


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def execute_crawler(config: Dict) -> bool:
    """
    Execute MediaCrawler to collect latest data.

    Args:
        config: Configuration dict

    Returns:
        True if successful, False otherwise
    """
    mediacrawler_path = config["mediacrawler_path"]

    if not os.path.exists(mediacrawler_path):
        print(f"❌ Error: MediaCrawler path not found: {mediacrawler_path}", file=sys.stderr)
        return False

    print("🔄 Executing MediaCrawler to collect data...")
    print(f"   Path: {mediacrawler_path}")
    print(f"   This may take 5-15 minutes...")

    try:
        # Execute crawler
        cmd = [
            "python", "run.py", "--crawl-only"
        ]

        # Change to MediaCrawler directory and run
        result = subprocess.run(
            cmd,
            cwd=mediacrawler_path,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode != 0:
            print(f"❌ MediaCrawler execution failed with code {result.returncode}", file=sys.stderr)
            print(f"   stderr: {result.stderr[:500]}", file=sys.stderr)
            return False

        print("✅ MediaCrawler execution completed successfully")
        return True

    except subprocess.TimeoutExpired:
        print("❌ MediaCrawler execution timed out (30 minutes)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error executing MediaCrawler: {e}", file=sys.stderr)
        return False


def load_platform_data(
    platform: str,
    date: str,
    config: Dict
) -> List[Dict]:
    """
    Load data for a specific platform and date.

    Args:
        platform: Platform identifier (xhs, douyin, bili, wb)
        date: Date string in YYYY-MM-DD format
        config: Configuration dict

    Returns:
        List of content items from the platform
    """
    data_path = config["data_path"]

    # Map platform to directory name
    platform_dirs = {
        "xhs": "xhs",
        "douyin": "douyin",
        "bili": "bili",
        "wb": "weibo"
    }

    platform_dir = platform_dirs.get(platform, platform)
    json_path = os.path.join(
        data_path,
        platform_dir,
        "json",
        f"search_contents_{date}.json"
    )

    if not os.path.exists(json_path):
        print(f"⚠️  Warning: Data file not found for {platform}: {json_path}", file=sys.stderr)
        return []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"⚠️  Warning: Unexpected data format for {platform}", file=sys.stderr)
            return []

        print(f"✅ Loaded {len(data)} items from {platform}")
        return data

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON for {platform}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"❌ Error loading data for {platform}: {e}", file=sys.stderr)
        return []


def load_all_data(date: str, config: Dict) -> Dict[str, List[Dict]]:
    """
    Load data from all configured platforms.

    Args:
        date: Date string in YYYY-MM-DD format
        config: Configuration dict

    Returns:
        Dict mapping platform to data lists
    """
    all_data = {}

    print(f"\n📊 Loading data for {date}...")

    for platform in config["platforms"]:
        data = load_platform_data(platform, date, config)
        all_data[platform] = data

    total_items = sum(len(data) for data in all_data.values())
    print(f"\n✅ Total items loaded: {total_items}")

    return all_data


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Sentiment Monitoring Orchestration Script"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to analyze (YYYY-MM-DD), defaults to today"
    )
    parser.add_argument(
        "--skip-crawler",
        action="store_true",
        help="Skip MediaCrawler execution, use existing data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run: only load data and show stats, don't analyze"
    )

    args = parser.parse_args()

    # Load configuration
    print("=" * 70)
    print("🤖 Sentiment Monitoring System")
    print("=" * 70)

    try:
        config = load_config()
        print(f"✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine date
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Analysis date: {date_str}")
    print(f"🔍 Keywords: {', '.join(config['keywords'])}")
    print(f"📱 Platforms: {', '.join(config['platforms'])}")

    # Step 1: Execute MediaCrawler (unless skipped)
    if not args.skip_crawler:
        print("\n" + "=" * 70)
        print("Step 1: Data Collection")
        print("=" * 70)

        success = execute_crawler(config)

        if not success:
            print("\n⚠️  Warning: MediaCrawler execution failed")
            print("   Will attempt to use existing data...")
    else:
        print("\n⏭️  Skipping MediaCrawler execution (--skip-crawler)")

    # Step 2: Load data from all platforms
    print("\n" + "=" * 70)
    print("Step 2: Data Loading")
    print("=" * 70)

    all_data = load_all_data(date_str, config)

    # Check if we have any data
    total_items = sum(len(data) for data in all_data.values())

    if total_items == 0:
        print("\n❌ Error: No data found for the specified date", file=sys.stderr)
        print("   Possible reasons:")
        print("   1. MediaCrawler hasn't run yet")
        print("   2. No results found for the keywords")
        print("   3. Data files don't exist for this date")
        sys.exit(1)

    # If dry run, stop here
    if args.dry_run:
        print("\n✅ Dry run completed - data loaded successfully")
        sys.exit(0)

    # Step 3: Perform sentiment analysis
    print("\n" + "=" * 70)
    print("Step 3: Sentiment Analysis")
    print("=" * 70)

    try:
        print("🔄 Analyzing sentiment, detecting risks, extracting topics...")
        analysis = analyze_all_data(all_data)
        print("✅ Analysis completed")

        # Print summary
        metrics = analysis["metrics"]
        print(f"\n📊 Analysis Summary:")
        print(f"   Total items: {metrics['total_items']}")
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

    # Step 4: Generate report
    print("\n" + "=" * 70)
    print("Step 4: Report Generation")
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

    # Step 5: Output report
    print("\n" + "=" * 70)
    print("Step 5: Report Output")
    print("=" * 70)

    # Output the complete report to stdout
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
