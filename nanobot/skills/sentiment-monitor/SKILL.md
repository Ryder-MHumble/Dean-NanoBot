---
name: sentiment-monitor
description: Daily sentiment monitoring / 每日舆情监控. Analyzes social media data from Supabase (Xiaohongshu, Douyin, Bilibili, Weibo) about the research institute, generates professional sentiment reports with risk alerts, trending topics, and account monitoring. Use when (1) setting up daily monitoring (2) generating sentiment report (3) analyzing social media data (4) running sentiment monitoring
metadata: {"nanobot":{"emoji":"📊","requires":{"bins":["python3"]}}}
---

# Sentiment Monitor

Automated daily sentiment monitoring for research institute leadership.

## Overview

This skill enables automated analysis of social media content across multiple Chinese platforms (Xiaohongshu, Douyin, Bilibili, Weibo) using data stored in Supabase, followed by AI-powered sentiment analysis and professional report generation.

**Key Features**:
- Multi-platform data collection (4 major Chinese social platforms)
- Automated sentiment classification (positive/neutral/negative)
- Risk detection and alerts
- Trending topic extraction
- KOL (Key Opinion Leader) identification
- **Competitor comparison analysis** (vs 深圳河套研究院, 上海创智研究院)
- **Negative content traceability** (detailed source links and comments)
- Professional reports for leadership decision-making

## When to Use

Use this skill when the user asks:
- "设置每日舆情监控" / "Set up daily sentiment monitoring"
- "生成舆情报告" / "Generate sentiment report"
- "分析今天的舆情" / "Analyze today's sentiment"
- "运行舆情监控" / "Run sentiment monitoring"
- "查看社交媒体数据" / "Check social media data"

## Quick Start

### Set up daily monitoring (run at 9 AM every day):
```bash
cron(action="add", message="Run sentiment monitoring: analyze social media data and send daily report", cron_expr="0 9 * * *")
```

### Generate report manually for today:
```bash
cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts && python3 run_monitor.py
```

### Generate report for specific date:
```bash
cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts && python3 run_monitor.py --date 2026-02-12
```

## Workflow

When executing sentiment monitoring, follow these steps:

### 1. Run Monitoring Script
Execute the monitoring script to load data from Supabase and generate report:
```bash
cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts && python3 run_monitor.py
```

The script will:
- Load all data from Supabase (posts and comments)
- Perform sentiment analysis
- Generate professional report
- Output report to stdout

### 2. Send Report
Use the message tool to send the generated report to the user:
```python
message(content=report_content, channel="dingtalk", chat_id=chat_id)
```

## Data Sources

All data is loaded from Supabase database:

- **Xiaohongshu (小红书)**: Notes, images, lifestyle content
- **Douyin (抖音)**: Short videos, viral content
- **Bilibili (B站)**: Long-form videos, technical content
- **Weibo (微博)**: News, public discourse

**Search Keywords**: "中关村人工智能研究院", "北京中关村学院", "中关村两院"

**Competitor Keywords**:
- 中关村人工智能研究院
- 深圳河套研究院
- 上海创智研究院

## Scripts

### run_monitor.py
Main script that loads data from Supabase and generates report.

**Usage**:
```bash
python3 run_monitor.py
```

**What it does**:
1. Load all posts and comments from Supabase
2. Call analyze_sentiment.py for analysis
3. Call generate_report_v2.py to format report
4. Output complete markdown report

### analyze_sentiment.py
Core sentiment analysis engine (imported by run_monitor.py).

**Capabilities**:
- Normalize data from different platforms into unified format
- Sentiment classification using keyword matching
- Risk detection (negative keywords, complaints)
- Trending topic extraction (hashtags, high engagement)
- KOL identification (high-follower accounts)
- Engagement metrics aggregation

### generate_report.py
Report formatting module (imported by run_monitor.py).

**Generates 7 key sections**:
1. Executive Summary
2. Sentiment Overview
3. Platform Analysis
4. Risk Alerts
5. Trending Topics
6. Account Monitoring
7. Recommendations

## Report Structure

The generated report includes these sections:

### 1. Executive Summary
- Overall sentiment (positive/neutral/negative percentages)
- Total mentions across platforms
- Key findings
- Urgent action items

### 2. Competitor Comparison Analysis
- Side-by-side comparison with 深圳河套研究院 and 上海创智研究院
- Sentiment distribution comparison
- Engagement metrics comparison
- Competitive insights and recommendations

### 3. Sentiment Overview
- Sentiment distribution table
- Trend comparison (vs previous day)
- Text-based charts

### 4. Platform Analysis
For each platform (Xiaohongshu, Douyin, Bilibili, Weibo):
- Total posts/videos
- Average engagement
- Top content (high engagement items)
- Key topics

### 5. Risk Alerts
Prioritized list of risks requiring attention:
- **High Priority**: Issues needing immediate action
- **Medium Priority**: Issues to monitor

Each alert includes:
- Source content
- Sentiment analysis
- Issue description
- Recommended action

### 6. Negative Content Details
- **Complete list of all negative posts** about 中关村人工智能研究院
- Full content preview with source links
- All comments under each negative post
- Easy traceability for response and handling

### 7. Trending Topics
- Top 5 topics by frequency and engagement
- Associated hashtags
- Content themes
- Sentiment by topic

### 8. Comments Analysis
- Overall comment sentiment distribution
- High-risk comments detection
- Comment management recommendations

### 9. Account Monitoring
- KOL identification (high-influence accounts)
- Active creators
- Account health metrics
- No spam/bot detection

### 10. Recommendations
- Immediate actions (this week)
- Short-term strategy (this month)
- Long-term initiatives (this quarter)

## Configuration

Edit `scripts/config.json` to customize:

```json
{
  "mediacrawler_path": "/Users/sunminghao/Desktop/MediaCrawler",
  "data_path": "/Users/sunminghao/Desktop/MediaCrawler/data",
  "keywords": ["中关村两院", "中关村人工智能研究院", "北京中关村学院"],
  "competitor_keywords": {
    "zgc": ["中关村人工智能研究院", "中关村两院", "北京中关村学院"],
    "hetao": ["深圳河套研究院", "河套研究院"],
    "chuangzhi": ["上海创智研究院", "创智研究院"]
  },
  "competitor_names": {
    "zgc": "中关村人工智能研究院",
    "hetao": "深圳河套研究院",
    "chuangzhi": "上海创智研究院"
  },
  "platforms": ["xhs", "douyin", "bili", "wb"],
  "sentiment_keywords": {
    "positive": ["优秀", "很好", "专业", "领先", "创新"],
    "negative": ["问题", "担心", "失望", "不满", "投诉"]
  },
  "thresholds": {
    "high_engagement_likes": 500,
    "high_engagement_comments": 50,
    "kol_min_followers": 10000
  }
}
```

## Cron Integration

This skill is designed to work with nanobot's cron system for automated daily monitoring.

### Set up daily monitoring at 9 AM:
When user requests to set up daily monitoring, use the cron tool:
```python
cron(
    action="add",
    message="Run sentiment monitoring: analyze social media data and send daily report",
    cron_expr="0 9 * * *"
)
```

### When cron triggers:
The agent will receive the message "Run sentiment monitoring: analyze social media data and send daily report" and should:
1. Read this SKILL.md file
2. Follow the workflow above
3. Run run_monitor.py
4. Send report via message tool

### Common cron expressions:
- Daily at 9 AM: `0 9 * * *`
- Twice daily (9 AM, 6 PM): `0 9,18 * * *`
- Every weekday at 9 AM: `0 9 * * 1-5`

## Error Handling

**Common issues**:

1. **Supabase connection fails**:
   - Check network connectivity
   - Verify Supabase credentials in config.json

2. **No data found**:
   - Verify data exists in Supabase tables
   - Check if keywords match any content

3. **Empty results**:
   - Report will show "No mentions found"
   - This is normal if keywords have no recent activity

## Examples

### Example 1: Manual report generation
User: "生成今天的舆情报告"

Agent:
1. Execute: `cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts && python3 run_monitor.py`
2. Capture output (markdown report)
3. Send via message tool

### Example 2: Set up automated monitoring
User: "设置每天早上9点的舆情监控定时任务"

Agent:
1. Call cron tool with action="add"
2. Use cron_expr="0 9 * * *"
3. Set message="Run sentiment monitoring: analyze social media data and send daily report"
4. Confirm job created

### Example 3: Generate report
User: "分析最近的舆情数据"

Agent:
1. Execute: `cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts && python3 run_monitor.py`
2. Capture report
3. Send via message tool

## Advanced Topics

### Historical Analysis
To compare trends over time, run reports for multiple dates and analyze differences in sentiment distribution, engagement, and topics.

### Custom Keywords
Modify `config.json` to add more keywords or focus on specific topics.

### Platform Filtering
Edit `config.json` platforms array to exclude platforms or focus on specific ones.

### Threshold Tuning
Adjust thresholds in `config.json` based on your platform's typical engagement levels.

## References

For detailed information, see:
- `references/report-template.md` - Complete report template with examples
- `references/sentiment-guidelines.md` - Sentiment analysis best practices
