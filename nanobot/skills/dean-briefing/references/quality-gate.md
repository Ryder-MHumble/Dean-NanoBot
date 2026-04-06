# Dean Briefing 质检门禁

在发送早报前，必须逐项检查并全部通过：

1. 内容来源正确：仅使用当日 API 返回段落，不重写段落事实。
2. 顺序正确：保持 API 原顺序，视作优先级顺序。
3. 链接完整：段落中的关键情报点保留原始链接。
4. 文案完整：标题、正文、收尾齐全，不丢段落。
5. 长度受控：默认总长度建议 `<= 6000` 中文字符。
6. 不落地文件：默认直接回复或发送消息，不创建本地 `.md` 报告文件。

可使用 `scripts/validate_intel_report.py` 做快速机器校验：

```bash
python3 scripts/validate_intel_report.py --require-priority false --max-chars 6000 --file - <<< "$report_content"
```
