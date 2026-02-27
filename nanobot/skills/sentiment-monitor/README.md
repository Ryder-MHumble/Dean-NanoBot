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

## Supabase 改造方案

### 改造动机

当前系统依赖本地JSON文件，存在以下限制：
- ❌ 无法远程访问数据
- ❌ 难以进行历史趋势分析
- ❌ 数据分散在多个文件中
- ❌ 无法灵活部署

### 改造后的优势

- ✅ 云端数据存储，支持远程访问
- ✅ 完整的历史数据查询能力
- ✅ 灵活的数据分析和聚合
- ✅ 支持多维度报告生成
- ✅ 可扩展到Web Dashboard

### 核心改动

#### 1. 数据库设计

**表结构**:
- `social_media_posts`: 存储所有平台的帖子数据
- `sentiment_analysis`: 存储情感分析结果
- `daily_reports`: 存储每日报告

**视图**:
- `v_posts_with_sentiment`: 帖子+情感分析联合视图
- `v_daily_stats`: 每日统计聚合视图

详细SQL脚本见skill文档末尾。

#### 2. 代码改造

**新增文件**:
- `scripts/supabase_client.py` - Supabase客户端封装
- `scripts/mediacrawler_sync.py` - 实时数据同步脚本
- `scripts/migrate_historical_data.py` - 历史数据迁移工具

**修改文件**:
- `scripts/config.json` - 添加Supabase配置
- `scripts/analyze_sentiment.py` - 支持从Supabase读取
- `scripts/run_monitor.py` - 集成同步逻辑

#### 3. 配置示例

```json
{
  "data_source": "supabase",
  "supabase": {
    "url": "https://your-project.supabase.co",
    "service_role_key": "your-key"
  }
}
```

#### 4. 向后兼容

设置 `"data_source": "local"` 可继续使用本地JSON模式，完全向后兼容。

### 迁移步骤

1. **创建Supabase项目** (10分钟)
   - 访问 supabase.com 创建项目
   - 执行SQL脚本创建表和视图

2. **安装依赖** (5分钟)
   ```bash
   pip install supabase-py watchdog
   ```

3. **配置环境** (5分钟)
   - 更新 config.json 添加Supabase凭证

4. **创建代码文件** (2小时)
   - 实现supabase_client.py
   - 实现数据同步逻辑

5. **测试系统** (30分钟)
   ```bash
   python3 run_monitor.py --date 2026-02-12 --skip-crawler
   ```

6. **迁移历史数据** (可选)
   ```bash
   python3 migrate_historical_data.py
   ```

### SQL脚本

**创建核心表**:

```sql
CREATE TABLE social_media_posts (
    id BIGSERIAL PRIMARY KEY,
    post_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    type VARCHAR(20),
    title TEXT,
    content TEXT,
    url TEXT,
    author_id VARCHAR(100),
    author_name VARCHAR(200),
    author_avatar TEXT,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    collects_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    tags TEXT[],
    ip_location VARCHAR(100),
    created_at TIMESTAMPTZ,
    crawled_at TIMESTAMPTZ DEFAULT NOW(),
    source_keyword VARCHAR(200),
    raw_data JSONB,
    UNIQUE(platform, post_id),
    CONSTRAINT check_platform CHECK (platform IN ('xhs', 'douyin', 'bili', 'wb'))
);

CREATE INDEX idx_posts_platform ON social_media_posts(platform);
CREATE INDEX idx_posts_created_at ON social_media_posts(created_at DESC);
CREATE INDEX idx_posts_crawled_at ON social_media_posts(crawled_at DESC);

CREATE TABLE sentiment_analysis (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES social_media_posts(id) ON DELETE CASCADE,
    sentiment_label VARCHAR(20) NOT NULL,
    sentiment_score DECIMAL(5, 4),
    confidence DECIMAL(5, 4),
    is_risk BOOLEAN DEFAULT false,
    risk_level VARCHAR(20),
    risk_keywords TEXT[],
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    analyzer_version VARCHAR(50),
    UNIQUE(post_id)
);

CREATE TABLE daily_reports (
    id BIGSERIAL PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    total_posts INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    platform_distribution JSONB,
    high_risk_count INTEGER DEFAULT 0,
    medium_risk_count INTEGER DEFAULT 0,
    report_content TEXT,
    report_metadata JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE VIEW v_posts_with_sentiment AS
SELECT
    p.*,
    (p.likes_count + p.comments_count + p.shares_count +
     COALESCE(p.collects_count, 0) + COALESCE(p.views_count, 0)) AS total_engagement,
    s.sentiment_label,
    s.sentiment_score,
    s.confidence AS sentiment_confidence,
    s.is_risk,
    s.risk_level,
    s.risk_keywords
FROM social_media_posts p
LEFT JOIN sentiment_analysis s ON p.id = s.post_id;
```

### 技术细节

**Python客户端示例**:

```python
from supabase import create_client

class SentimentSupabaseClient:
    def __init__(self, config):
        self.client = create_client(
            config["supabase"]["url"],
            config["supabase"]["service_role_key"]
        )

    def get_posts_by_date_range(self, start_date, end_date, platform=None):
        query = self.client.table("v_posts_with_sentiment")\
            .select("*")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())

        if platform:
            query = query.eq("platform", platform)

        return query.execute().data

    def upsert_posts(self, posts):
        return self.client.table("social_media_posts")\
            .upsert(posts, on_conflict="platform,post_id")\
            .execute()
```

### FAQ

**Q: 改造需要多长时间？**
A: 核心开发约8-10小时，测试和调试2-3小时。

**Q: Supabase免费版够用吗？**
A: 免费版支持500MB数据库，对于每日数百条数据可用1-2年。

**Q: 会丢失现有数据吗？**
A: 不会。本地JSON文件保留，Supabase是额外存储层。

**Q: 如何回退？**
A: 只需设置 `data_source: "local"` 即可回到原有模式。

### 实施建议

**阶段1**（2小时）：Supabase设置 + 基本客户端
**阶段2**（3小时）：修改现有代码支持Supabase
**阶段3**（3小时）：实时同步 + 历史迁移
**阶段4**（2小时）：全面测试 + 文档更新

---

## 未来改进

- [ ] ✅ Supabase云端存储（改造方案见上）
- [ ] 使用LLM进行更深度的情感分析
- [ ] 生成可视化图表
- [ ] 支持更频繁的监控（每小时）
- [ ] 多关键词组合分析
- [ ] 自动回复建议生成
- [ ] Web Dashboard（基于Supabase + Next.js）

## License

本skill是nanobot项目的一部分，遵循项目的开源协议。

---

## Supabase迁移完成（2026-02-26更新）

### ✅ 已完成的改动

#### 1. 数据源迁移
- ✅ 创建Supabase客户端 (`scripts/supabase_client.py`)
- ✅ 修改数据加载逻辑支持Supabase
- ✅ 保持向后兼容（可切换回本地模式）

#### 2. 报告优化
- ✅ 创建优化版报告生成器 (`scripts/generate_report_v2.py`)
- ✅ **可溯源**：每个内容都附带原文链接
- ✅ **详细分解**：互动数据（赞、评、转、藏）独立展示
- ✅ **KOL分析**：详细信息、内容主题、合作建议
- ✅ **行动导向**：执行部门、资源需求、KPI指标

### 🚀 快速开始（Supabase模式）

```bash
cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts

# 安装依赖（首次）
python3 -m venv .venv
source .venv/bin/activate
pip install supabase

# 生成报告
source .venv/bin/activate
python3 run_monitor.py --date 2025-09-08 --skip-crawler
```

### 📊 报告模板对比

**旧版**：
```markdown
1. "标题" - 172 互动, 中性
   - 作者: 小红薯F517277
```

**新版（优化）**：
```markdown
1. **《标题》**
   - 👤 作者：小红薯F517277
   - 📊 互动：123赞 + 46评 + 3转 = **172**
   - 🎭 情感：🟡 中性
   - 🔗 [查看原文](https://www.xiaohongshu.com/explore/...)
   - 💡 **建议**：关注负面内容，评估是否需要回应
```

### 🔧 配置说明

**Supabase模式** (config.json):
```json
{
  "data_source": "supabase",
  "supabase": {
    "url": "https://dfpijqpgsupvdmidztup.supabase.co",
    "key": "${SUPABASE_KEY}"
  }
}
```

**本地模式** (切换回本地JSON):
```json
{
  "data_source": "local"
}
```

### 📁 新增文件

- `scripts/supabase_client.py` - Supabase客户端封装
- `scripts/generate_report_v2.py` - 优化版报告生成器
- `scripts/.venv/` - Python虚拟环境（需安装）

### 🎯 主要优化点

| 模块 | 优化内容 |
|------|---------|
| **Executive Summary** | 核心指标表格、关键发现卡片、待办事项清单 |
| **Platform Analysis** | 互动数据分解、原文链接、建议行动 |
| **Risk Alerts** | 内容引用、影响评估、分级行动清单 |
| **Account Monitoring** | KOL详细信息、内容主题、合作建议 |
| **Recommendations** | 执行部门、资源需求、KPI指标 |

### 💡 使用建议

**测试连接**：
```bash
source .venv/bin/activate
python3 supabase_client.py
```

**查看可用日期**：
```python
from supabase_client import SentimentSupabaseClient
# 查询数据库中有哪些日期的数据
```

**生成完整报告**：
```bash
# 使用有数据的日期（如2025-09-08）
python3 run_monitor.py --date 2025-09-08 --skip-crawler
```

### 🔍 数据库信息

- **表名**：`contents`, `comments`
- **总数据**：63条内容 + 231条评论
- **日期范围**：2025-03-29 至 2026-02-09
- **平台**：小红书、B站、抖音、微博

---

创建日期: 2026-02-12
更新日期: 2026-02-26 (Supabase迁移完成 + 报告优化)
作者: Claude Code
