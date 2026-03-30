---
name: fetch-data
description: Use when users need OpenClaw backend data retrieval through /api/v1 endpoints, including source discovery, policy/personnel feeds, scholar and student directories, and leadership data. Route intent to correct endpoint and execute one-shot API calls directly without writing local script files unless the user explicitly asks to save a script.
---
# OpenClaw Fetch Data Skill

## 目标

根据用户自然语言需求，选择正确 API、映射参数、直接执行查询，并返回结构化结果。

后端基址：`http://10.1.132.21:8001`

## 默认执行模式（强约束）

- 默认使用一次性执行，不落盘脚本文件。
- 推荐命令形态：`./.venv/bin/python - <<'PY' ... PY`（或可用解释器）/ 直接 `curl`。
- 只有用户明确要求“保存脚本/生成文件”时，才使用 `scripts/fetch_template.py`。

## 路由决策

1. 用户问“有哪些信源/某类信源是否覆盖/按维度筛选”：
- 优先 `GET /api/v1/sources/catalog`
- 需要筛选面板值时加调 `GET /api/v1/sources/facets`

2. 用户问“政策/人事动态”：
- `GET /api/v1/intel/policy/feed`
- `GET /api/v1/intel/personnel/feed`

3. 用户问“学者/导师/院士/共建导师”：
- `GET /api/v1/scholars`

4. 用户问“学生/导师名下学生/年级状态”：
- `GET /api/v1/students`

5. 用户问“高校领导模块数据”：
- `GET /api/v1/leadership`

## 执行流程

1. 读取 `references/intent-map.md` 做意图到接口映射。
2. 读取 `references/api-catalog.md` 确认参数、分页、关键返回字段。
3. 按 `references/script-guide.md` 使用“一次性执行模板”直接请求。
4. 结果展示优先返回摘要表 + 总量 + 下一页建议，不输出冗长原始 JSON。

## 参数抽取规则

- 关键词：`keyword`
- 信源限定：`source_id/source_ids/source_name/source_names`
- 信源目录过滤：`dimension(s)`, `group(s)`, `tag(s)`, `is_enabled`, `health_status(es)`
- Feed 分页：`limit/offset`
- 列表分页：`page/page_size`

## 参考文件入口

- 接口与字段：`references/api-catalog.md`
- 意图映射：`references/intent-map.md`
- 一次性执行规范：`references/script-guide.md`
- 信源专项：`references/sources.md`
