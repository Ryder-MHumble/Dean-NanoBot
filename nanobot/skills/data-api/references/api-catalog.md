# API 参数完整文档

后端地址：`http://43.98.254.243:8001`

---

## 1. 信源列表 API

**GET** `/api/v1/sources/`

用途：查询当前系统支持的所有信源，可按维度筛选。**当用户询问「有哪些来源」时，优先调用此接口**。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `dimension` | string | 按维度筛选：`national_policy` / `beijing_policy` / `technology` / `personnel` / `industry` / `talent` / `events` / `universities` / `university_faculty` |

### 响应结构（每条信源）

```json
{
  "id": "moe_policy",
  "name": "教育部-政策法规",
  "url": "https://...",
  "dimension": "national_policy",
  "crawl_method": "static",
  "schedule": "daily",
  "is_enabled": true,
  "priority": 2,
  "last_crawl_at": "2026-03-01T08:00:00",
  "last_success_at": "2026-03-01T08:01:00",
  "consecutive_failures": 0
}
```

---

## 2. 政策动态 Feed

**GET** `/api/v1/intel/policy/feed`

### 请求参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `category` | string | 分类 | `国家政策` / `北京政策` / `领导讲话` / `政策机会` |
| `importance` | string | 重要性 | `紧急` / `重要` / `关注` / `一般` |
| `keyword` | string | 关键词（标题/摘要/标签） | `人工智能` |
| `source_id` | string | 精确单个信源 ID | `moe_policy` |
| `source_ids` | string | 精确多个，逗号分隔 | `moe_policy,most_policy` |
| `source_name` | string | 模糊单个名称 | `教育部` |
| `source_names` | string | 模糊多个，逗号分隔 | `教育部,科技部` |
| `limit` | int | 最多返回条数（默认50，最大200） | `20` |
| `offset` | int | 分页偏移（默认0） | `0` |

### 关键响应字段

```json
{
  "item_count": 25,
  "items": [{
    "title": "关于印发《...》的通知",
    "summary": "摘要文本",
    "category": "国家政策",
    "importance": "重要",
    "date": "2026-01-15",
    "source": "教育部",
    "funding": "5000万元",
    "daysLeft": 15,
    "sourceUrl": "https://..."
  }]
}
```

**展示字段：** `date` / `title` / `source` / `importance` / `summary` / `funding`（有则显示）/ `daysLeft`（有则显示）/ `sourceUrl`

---

## 3. 人事动态 Feed

**GET** `/api/v1/intel/personnel/feed`

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `importance` | string | `紧急` / `重要` / `关注` / `一般` |
| `keyword` | string | 关键词（姓名/职位/部门） |
| `source_id / source_ids / source_name / source_names` | string | 信源过滤（同政策） |
| `limit` | int | 默认50，最大200 |
| `offset` | int | 默认0 |

### 关键响应字段

```json
{
  "item_count": 12,
  "items": [{
    "title": "科技部发布最新人事任免通知",
    "date": "2026-01-15",
    "source": "中国政府网",
    "importance": "重要",
    "changes": [
      {
        "name": "张某某",
        "action": "任命",
        "position": "人工智能研究中心主任",
        "department": "科技部",
        "date": "2026-01-15"
      }
    ],
    "sourceUrl": "https://..."
  }]
}
```

**展示字段：** `date` / `title` / `source` / `importance` + `changes[]`（姓名/动作/职位/部门）/ `sourceUrl`

---

## 4. 高校动态 Feed

**GET** `/api/v1/intel/university/feed`

### 请求参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `group` | string | 按分组筛选 | `university_news` / `ai_institutes` / `awards` / `provincial` / `aggregators` |
| `keyword` | string | 标题关键词 | `人工智能` |
| `date_from` | date | 开始日期 YYYY-MM-DD | `2026-01-01` |
| `date_to` | date | 结束日期 YYYY-MM-DD | `2026-03-01` |
| `source_id / source_ids / source_name / source_names` | string | 信源过滤 | `source_name=清华大学` |
| `page` | int | 页码（默认1） | `1` |
| `page_size` | int | 每页条数（默认20，最大200） | `20` |

### 关键响应字段

```json
{
  "total": 1200,
  "page": 1,
  "page_size": 20,
  "total_pages": 60,
  "items": [{
    "title": "文章标题",
    "url": "https://...",
    "published_at": "2026-01-15T10:00:00",
    "source_name": "清华大学新闻网",
    "group": "university_news"
  }]
}
```

**展示字段：** `published_at`（取日期部分）/ `title` / `source_name` / `url`

---

## 5. 社媒内容信息流

**GET** `/api/v1/sentiment/feed`

### 请求参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `platform` | string | 平台筛选 | `xhs`（小红书）/ `dy`（抖音）/ `bilibili` / `weibo`（微博） |
| `keyword` | string | 关键词（标题/正文/作者） | `中关村` |
| `sort_by` | string | 排序字段（默认 `publish_time`） | `publish_time` / `liked_count` / `comment_count` / `share_count` |
| `sort_order` | string | 排序方向（默认 `desc`） | `asc` / `desc` |
| `page` | int | 页码（默认1） | `1` |
| `page_size` | int | 每页条数（默认20，最大100） | `20` |

### 关键响应字段

```json
{
  "total": 342,
  "page": 1,
  "page_size": 20,
  "total_pages": 18,
  "items": [{
    "platform": "xhs",
    "content_type": "normal",
    "title": "内容标题",
    "description": "正文内容",
    "content_url": "https://...",
    "cover_url": "https://...",
    "nickname": "作者昵称",
    "ip_location": "北京",
    "liked_count": 1024,
    "comment_count": 86,
    "share_count": 43,
    "collected_count": 210,
    "source_keyword": "中关村人工智能",
    "publish_time": 1705296000000
  }]
}
```

**平台代码：** `xhs`=小红书，`dy`=抖音，`bilibili`=哔哩哔哩，`weibo`=微博

**注意：** `publish_time` 为时间戳（xhs 单位毫秒，dy 单位秒），展示时需转换为可读日期。

**展示字段：** `platform` / `nickname` / `ip_location` / `title` / `description`（截断）/ 互动数（点赞/评论/分享/收藏）/ `source_keyword` / `content_url`

---

## 6. 师资列表

**GET** `/api/v1/faculty/`

### 请求参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `university` | string | 高校名（模糊匹配） | `清华` / `北京大学` |
| `department` | string | 院系名（模糊匹配） | `计算机` |
| `group` | string | 信源分组（精确） | `sjtu` / `pku` / `cas` |
| `position` | string | 职称（精确） | `教授` / `副教授` / `研究员` / `助理教授` |
| `is_academician` | bool | 仅显示院士 | `true` |
| `is_potential_recruit` | bool | 仅显示潜在引进人才 | `true` |
| `has_email` | bool | 仅显示有邮箱的 | `true` |
| `min_completeness` | int | 最低数据完整度 0-100 | `60` |
| `keyword` | string | 关键词（姓名/简介/研究方向） | `自然语言处理` |
| `source_id / source_ids / source_name / source_names` | string | 信源过滤 |  |
| `page` | int | 页码（默认1） | `1` |
| `page_size` | int | 每页条数（默认20，最大200） | `20` |

### 关键响应字段

```json
{
  "total": 856,
  "page": 1,
  "page_size": 20,
  "total_pages": 43,
  "items": [{
    "url_hash": "abc123",
    "name": "张三",
    "name_en": "Zhang San",
    "university": "清华大学",
    "department": "计算机科学与技术系",
    "position": "教授",
    "academic_titles": ["长江学者"],
    "is_academician": false,
    "research_areas": ["自然语言处理", "机器学习"],
    "email": "zhangsan@tsinghua.edu.cn",
    "profile_url": "https://...",
    "data_completeness": 85,
    "is_potential_recruit": false
  }]
}
```

**展示字段：** `name` / `university` / `department` / `position` / `academic_titles` / `is_academician` / `research_areas`（前3个）/ `email`（有则显示）/ `profile_url`
