# Sentiment Monitor Skill - 测试指南

本文档提供详细的测试步骤，帮助您验证sentiment-monitor skill是否正确配置并能够正常工作。

## 测试前准备

### 1. 确认MediaCrawler已运行

检查是否有数据文件：
```bash
ls -lh /Users/sunminghao/Desktop/MediaCrawler/data/*/json/*.json
```

如果没有数据，先运行MediaCrawler：
```bash
cd /Users/sunminghao/Desktop/MediaCrawler
python run.py --crawl-only
```

### 2. 确认Python环境

```bash
python3 --version  # 应该是Python 3.x
which python3
```

## 测试阶段

## 阶段1: 组件单独测试

### 测试1.1: 配置文件

```bash
cd /Users/sunminghao/Desktop/nanobot/nanobot/skills/sentiment-monitor/scripts
cat config.json | python3 -m json.tool
```

**预期结果**: JSON格式正确，无语法错误

### 测试1.2: 情感分析引擎

```bash
python3 analyze_sentiment.py
```

**预期结果**:
```
Sentiment Analysis Engine
==================================================
Loaded config: 4 platforms

Testing sentiment classification:
  '这个研究院很好...' -> positive (score: 1.00, confidence: 0.60)
  '有点失望...' -> neutral/negative (score: ..., confidence: ...)
  '今天去参观...' -> neutral (score: 0.00, confidence: 0.30)
```

### 测试1.3: 报告生成器

```bash
python3 generate_report.py | head -50
```

**预期结果**: 显示报告头部，包含标题、日期、Executive Summary等

### 测试1.4: 主脚本（dry run）

使用已有数据测试，不运行爬虫：
```bash
python3 run_monitor.py --date 2026-02-12 --skip-crawler --dry-run
```

**预期结果**:
```
======================================================================
🤖 Sentiment Monitoring System
======================================================================
✅ Configuration loaded
📅 Analysis date: 2026-02-12
...
✅ Dry run completed - data loaded successfully
```

## 阶段2: 完整流程测试（不含爬虫）

如果您已经有MediaCrawler的数据文件：

```bash
python3 run_monitor.py --date 2026-02-12 --skip-crawler
```

**预期结果**:
1. 加载数据成功
2. 分析完成
3. 生成完整报告
4. 在输出中看到markdown格式的报告

**检查要点**:
- [ ] 是否显示了所有4个平台的数据？
- [ ] 情感分布是否合理？
- [ ] 是否有风险预警？（如果数据中有负面内容）
- [ ] 是否识别了热门话题？
- [ ] 报告格式是否正确？

## 阶段3: 完整流程测试（含爬虫）

**注意**: 此测试会实际运行MediaCrawler，需要5-15分钟

```bash
python3 run_monitor.py
```

**监控进度**:
在另一个终端窗口：
```bash
tail -f /tmp/mediacrawler.log
```

**预期结果**:
1. MediaCrawler执行成功
2. 4个平台的数据都被爬取
3. 分析和报告生成成功

## 阶段4: Nanobot集成测试

### 测试4.1: Skill识别测试

启动nanobot，然后说：
```
"Run sentiment monitoring"
```
或
```
"生成舆情报告"
```

**预期结果**: Agent识别到sentiment-monitor skill并开始执行

**观察要点**:
- [ ] Agent是否提到"sentiment-monitor"或"舆情监控"？
- [ ] Agent是否读取了SKILL.md？
- [ ] Agent是否开始执行MediaCrawler或run_monitor.py？

### 测试4.2: Cron任务创建测试

在nanobot中说：
```
"设置每天早上9点的舆情监控定时任务"
```

**预期结果**: Agent创建cron任务

**验证**:
```
"列出所有cron任务"
```

应该看到类似的任务：
```
- Run sentiment monitoring: analyze social media data and send daily report (id: xxx, cron)
```

### 测试4.3: Cron触发测试（短期测试）

为了快速测试，创建一个2分钟后触发的任务：

在nanobot中说：
```
"创建一个测试任务，2分钟后执行一次，消息是：生成舆情报告"
```

**观察**: 2分钟后，检查agent是否自动执行

**如果没有自动执行**:
- 检查cron任务是否存在
- 查看nanobot日志
- 尝试使用更明确的触发词

## 阶段5: 报告接收测试

### 测试5.1: 手动发送报告

假设您已经生成了报告（保存在文件或变量中），测试通过message tool发送：

在nanobot中（如果agent支持）：
```python
message(
    content="[报告内容]",
    channel="dingtalk",
    chat_id="您的chat_id"
)
```

**预期结果**: 在钉钉/飞书收到报告消息

## 常见问题排查

### 问题1: "MediaCrawler execution failed"

**检查**:
```bash
cat /tmp/mediacrawler.log
```

**常见原因**:
- 网络连接问题
- MediaCrawler需要重新登录
- Python环境问题

**解决**:
```bash
cd /Users/sunminghao/Desktop/MediaCrawler
python run.py --login-only  # 重新登录
```

### 问题2: "Data file not found"

**检查**:
```bash
ls /Users/sunminghao/Desktop/MediaCrawler/data/*/json/
```

**原因**: MediaCrawler还没运行或运行失败

**解决**: 先手动运行MediaCrawler

### 问题3: "No data found"

**原因**: 关键词在当天没有新的提及

**解决**:
- 使用`--date`参数指定有数据的日期
- 或修改config.json中的关键词

### 问题4: Agent不能自动识别skill

**检查**:
1. SKILL.md的description是否包含触发关键词？
2. 消息文本是否与触发短语匹配？

**解决**:
- 使用更明确的触发词："生成舆情报告"
- 或使用方式B（系统cron）

### 问题5: 报告没有发送到钉钉/飞书

**检查**:
- message tool是否配置正确？
- channel和chat_id是否正确？

**临时解决**: 报告内容在run_monitor.py的输出中，可以手动复制

## 测试检查清单

完成所有测试后，请确认：

### 基础功能
- [ ] config.json格式正确
- [ ] analyze_sentiment.py可以运行
- [ ] generate_report.py可以运行
- [ ] run_monitor.py可以执行（dry run）

### 数据处理
- [ ] 可以加载MediaCrawler数据
- [ ] 可以正确识别不同平台的数据
- [ ] 情感分类工作正常
- [ ] 报告生成完整

### Nanobot集成
- [ ] Skill可以被nanobot识别
- [ ] 手动触发可以执行
- [ ] Cron任务可以创建
- [ ] Cron触发可以自动执行（可选）

### 完整流程
- [ ] 从爬虫到报告的完整流程工作正常
- [ ] 报告内容准确和完整
- [ ] 报告可以发送到目标渠道（可选）

## 性能基准

**正常执行时间**:
- MediaCrawler爬取: 5-15分钟（取决于数据量）
- 数据加载: 1-2秒
- 情感分析: 5-10秒（100条内容）
- 报告生成: 1-2秒
- **总计**: 约6-18分钟

**数据量基准**:
- 典型情况: 50-200条内容/天
- 高峰情况: 200-500条内容/天
- 低峰情况: 10-50条内容/天

## 下一步

测试完成后：

1. **如果所有测试通过**:
   - 设置正式的每日定时任务
   - 开始收集每日数据
   - 根据实际使用调整配置

2. **如果部分测试失败**:
   - 查看本文档的"常见问题排查"
   - 检查日志文件
   - 根据错误信息调整配置

3. **优化和调整**:
   - 根据实际数据调整情感关键词
   - 根据实际需求调整报告格式
   - 根据反馈改进分析逻辑

---

*祝测试顺利！如有问题，请参考README.md和SKILL.md*
