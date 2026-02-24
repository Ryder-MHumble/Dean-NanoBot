# Sentiment Monitor Skill - 舆情监控技能

## 概述

sentiment-monitor 是为 nanobot 创建的每日舆情监控 skill，用于自动化收集和分析社交媒体数据，生成专业的舆情报告。

## 功能特点

✅ **多平台数据收集**: 支持小红书、抖音、B站、微博四大平台
✅ **智能情感分析**: 基于关键词的情感分类（正面/中性/负面）
✅ **风险预警系统**: 自动识别和分级风险项
✅ **热点话题提取**: 识别trending topics和标签
✅ **KOL识别**: 发现高影响力账号
✅ **专业报告生成**: 7个核心部分的完整报告
✅ **自动化执行**: 支持cron定时任务

## 文件结构

```
nanobot/skills/sentiment-monitor/
├── SKILL.md                          # Skill 定义和使用指南
├── README.md                         # 本文件
├── scripts/
│   ├── run_monitor.py               # 主编排脚本
│   ├── analyze_sentiment.py         # 舆情分析引擎
│   ├── generate_report.py           # 报告生成器
│   └── config.json                  # 配置文件
└── references/
    ├── report-template.md           # 报告模板示例
    └── sentiment-guidelines.md      # 分析指导原则
```

## 快速开始

### 1. 设置每日定时监控

**方式A: 通过nanobot创建（推荐）**

在 nanobot 中请求：
```
"设置每天早上9点的舆情监控定时任务"
```
或更明确的：
```
"创建cron任务，每天9点执行，消息是：生成舆情报告"
```

Agent 会调用 cron tool 创建定时任务。当cron触发时，agent会自动识别并执行sentiment-monitor skill。

**方式B: 系统cron（备选）**

如果需要更可靠的执行，可以使用系统cron：
```bash
crontab -e
# 添加以下行：
0 9 * * * /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts/cron_wrapper.sh
```

### 2. 手动生成报告

在 nanobot 中请求：
```
"生成今天的舆情报告"
```

或直接运行脚本：
```bash
cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts
python3 run_monitor.py
```

### 3. 分析特定日期

```bash
python3 run_monitor.py --date 2026-02-12
```

### 4. 跳过爬虫（使用现有数据）

```bash
python3 run_monitor.py --skip-crawler
```

## 工作流程

```
[Cron触发] 或 [手动请求]
    ↓
[Agent识别sentiment-monitor skill]
    ↓
[执行MediaCrawler爬取数据] (5-15分钟)
    ↓
[加载4个平台的JSON数据]
    ↓
[情感分析 + 风险检测 + 热点提取]
    ↓
[生成专业markdown报告]
    ↓
[通过MessageTool发送报告]
```

## 报告结构

生成的报告包含7个核心部分：

1. **Executive Summary** - 总体舆情、关键发现、紧急行动项
2. **Sentiment Overview** - 情感分布、趋势对比
3. **Platform Analysis** - 各平台详细分析
4. **Risk Alerts** - 高/中优先级风险预警
5. **Trending Topics** - 热门话题和标签
6. **Account Monitoring** - KOL识别和账号健康度
7. **Recommendations** - 即时行动、短期策略、长期规划

## 配置

编辑 `scripts/config.json` 来自定义：

- **mediacrawler_path**: MediaCrawler项目路径
- **keywords**: 监控关键词
- **platforms**: 要监控的平台
- **sentiment_keywords**: 情感分类关键词
- **thresholds**: 各种阈值设置

## 测试

### 测试情感分析引擎
```bash
cd scripts
python3 analyze_sentiment.py
```

### 测试报告生成器
```bash
python3 generate_report.py
```

### 测试完整流程（dry run）
```bash
python3 run_monitor.py --date 2026-02-12 --dry-run
```

## 数据源

MediaCrawler 爬取的数据位于：
- `/Users/sunminghao/Desktop/MediaCrawler/data/xhs/json/search_contents_YYYY-MM-DD.json`
- `/Users/sunminghao/Desktop/MediaCrawler/data/douyin/json/search_contents_YYYY-MM-DD.json`
- `/Users/sunminghao/Desktop/MediaCrawler/data/bili/json/search_contents_YYYY-MM-DD.json`
- `/Users/sunminghao/Desktop/MediaCrawler/data/weibo/json/search_contents_YYYY-MM-DD.json`

## 常见问题

**Q: MediaCrawler执行失败怎么办？**
A: 检查 `/tmp/mediacrawler.log` 日志，确认网络连接和登录状态。

**Q: 数据文件不存在？**
A: 确保 MediaCrawler 已经成功运行，或使用 `--skip-crawler` 测试现有数据。

**Q: 如何修改监控关键词？**
A: 编辑 `scripts/config.json` 中的 `keywords` 字段。

**Q: 如何调整情感分类的准确性？**
A: 在 `config.json` 中添加更多的正面/负面关键词。

**Q: 如何设置不同的定时任务？**
A: 修改 cron 表达式，例如：
- 每天 9AM: `0 9 * * *`
- 每天 9AM 和 6PM: `0 9,18 * * *`
- 工作日 9AM: `0 9 * * 1-5`

## 参考文档

- [SKILL.md](SKILL.md) - 完整的skill定义和使用指南
- [report-template.md](references/report-template.md) - 报告模板详细说明
- [sentiment-guidelines.md](references/sentiment-guidelines.md) - 情感分析最佳实践

## 技术架构

- **语言**: Python 3
- **依赖**: 标准库（json, os, subprocess, argparse, datetime）
- **外部依赖**: MediaCrawler项目（用于数据采集）
- **分析方法**: 关键词匹配（快速、零成本）

## 未来改进

- [ ] 历史趋势分析（存储每日数据）
- [ ] 使用LLM进行更深度的情感分析
- [ ] 生成可视化图表
- [ ] 支持更频繁的监控（每小时）
- [ ] 多关键词组合分析
- [ ] 自动回复建议生成

## License

本skill是nanobot项目的一部分，遵循项目的开源协议。

---

创建日期: 2026-02-12
作者: Claude Code
