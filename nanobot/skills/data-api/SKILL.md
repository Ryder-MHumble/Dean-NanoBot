---
name: zkygyzlyj-data-api
description: Use when users ask for data about Chinese AI policy, government personnel changes, university news, social media sentiment (Xiaohongshu/Douyin/Bilibili/Weibo), or faculty/scholar information from the institute's intelligence system. First queries available sources via API, then identifies matching data, and generates executable Python scripts to fetch and display results.
---

# 中关村人工智能研究院智能数据 API

## 概述

本 Skill 帮助你理解研究院后端数据系统的能力，并根据用户需求生成可直接运行的 Python 数据脚本。

**后端地址：** `http://43.98.254.243:8001`

---

## 六大核心 API 速查

| 用户常见问法 | API | 路径 |
|------------|-----|------|
| 有哪些数据来源？当前支持哪些信源？ | 信源列表 | `GET /api/v1/sources/` |
| 最近出了什么政策、申报通知、政策机会 | 政策动态 Feed | `GET /api/v1/intel/policy/feed` |
| 谁被任命/免职、领导调动、人事变动 | 人事动态 Feed | `GET /api/v1/intel/personnel/feed` |
| 高校动态、大学新闻、AI 研究机构公告 | 高校动态 Feed | `GET /api/v1/intel/university/feed` |
| 小红书/抖音/B站/微博上的舆情、社媒评论 | 社媒内容信息流 | `GET /api/v1/sentiment/feed` |
| 高校师资、学者信息、查某个教授/研究员 | 师资列表 | `GET /api/v1/faculty/` |

---

## 交互协议（必须遵守）

**第一步：查询可用信源（当用户询问特定机构或来源时）**

调用信源列表 API 确认支持情况：
```
GET /api/v1/sources/?dimension=<维度>
```
向用户说明当前支持的信源范围，询问是否符合需求。

**第二步：确认需求，提取过滤参数**

从用户描述中提取：
- 目标机构/平台（→ `source_name` 或 `platform`）
- 关键词（→ `keyword`）
- 时间范围（→ `date_from` / `date_to`）
- 数量要求（→ `limit` / `page_size`）

**第三步：生成脚本**

1. 读 `references/api-catalog.md` → 确认端点参数
2. 读 `references/script-guide.md` → 按规范生成展示脚本
3. 输出完整可运行 Python 脚本（参数已按用户需求填好）

---

## 信源过滤参数（Policy / Personnel / University / Faculty 通用）

| 参数 | 匹配方式 | 示例 |
|------|---------|------|
| `source_id` | 精确单个 | `source_id=moe_policy` |
| `source_ids` | 精确多个，逗号分隔 | `source_ids=moe_policy,most_policy` |
| `source_name` | 模糊单个 | `source_name=教育部` |
| `source_names` | 模糊多个，逗号分隔 | `source_names=教育部,科技部` |

---

## 何时读取哪个 reference 文件

- API 参数详情、响应字段 → `references/api-catalog.md`
- 已知信源 ID 和名称 → `references/sources.md`
- 脚本生成、结构化展示代码 → `references/script-guide.md`
- 完整可运行示例 → `scripts/fetch_template.py`
