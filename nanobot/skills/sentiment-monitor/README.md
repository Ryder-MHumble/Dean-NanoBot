# sentiment-monitor

`sentiment-monitor` 用于生成“官方账号运营分析 + 全网舆情洞察”的双维度报告。

当前推荐执行方式：**调用后端 API 取数并生成结果**，而不是依赖本地爬虫或本地中间文件。

## 目录结构

```text
nanobot/skills/sentiment-monitor/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── api-catalog.md
│   ├── quality-gate.md
│   ├── report-template.md
│   └── sentiment-guidelines.md
└── scripts/
    ├── run_monitor.py
    ├── analyze_sentiment.py
    ├── generate_report_v2.py
    ├── supabase_client.py
    └── validate_intel_report.py
```

## 快速使用

### 1) 在会话中触发

示例：
- “生成今天的舆情报告（标准版）”
- “给我一个更快更短的舆情快报（Fast）”
- “分析近7天舆情，重点看风险和可转发机会”

### 2) 直接调用后端 API（调试/核对）

```bash
# 概览
curl -sS "http://10.1.132.21:8001/api/v1/sentiment/overview"

# 最近7天报告（默认 markdown）
curl -sS -G "http://10.1.132.21:8001/api/v1/reports/sentiment/latest" \
  --data-urlencode "days=7" \
  --data-urlencode "output_format=markdown"

# 信息流
curl -sS -G "http://10.1.132.21:8001/api/v1/sentiment/feed" \
  --data-urlencode "keyword=中关村人工智能研究院" \
  --data-urlencode "sort_by=publish_time" \
  --data-urlencode "sort_order=desc" \
  --data-urlencode "page=1" \
  --data-urlencode "page_size=20"
```

更多参数见 `references/api-catalog.md`。

## 执行模式

- `Standard`（默认）：覆盖更完整，适合正式日报。
- `Fast`：仅在用户明确要求“更快/更短”时使用。

## 输出质量要求

发送前必须通过 `references/quality-gate.md`，重点检查：
- 双维度完整
- `P1/P2/P3` 完整
- 原始链接完整（缺失需显式标注）
- 行动清单可执行

## 关于 scripts（说明）

`scripts/` 目录保留用于历史兼容/本地调试，不是默认生产路径。

如果仅做脚本调试，当前 `run_monitor.py` 的有效参数是：

```bash
python3 nanobot/skills/sentiment-monitor/scripts/run_monitor.py --mode standard
python3 nanobot/skills/sentiment-monitor/scripts/run_monitor.py --date 2026-02-12 --mode fast
```

> 注意：`--skip-crawler`、`--dry-run` 不是当前脚本支持参数，文档中不再使用。

## 参考

- `SKILL.md`
- `references/api-catalog.md`
- `references/report-template.md`
- `references/quality-gate.md`
- `references/sentiment-guidelines.md`
