# Query -> API 参数映射（Scholar）

## 1) 基础路由

- 学者列表：`GET /api/v1/scholars`
- 学者统计：`GET /api/v1/scholars/stats`
- 学者详情：`GET /api/v1/scholars/{url_hash}`
- 导师学生关系：`GET /api/v1/scholars/{url_hash}/students`

## 2) 常见意图到参数

| 用户表达 | 映射参数 |
| --- | --- |
| 清华大学 / 北大 / 海外高校 | `university=<机构名>` 或 `region=国际` |
| 计算机学院 / 人工智能研究院 | `department=<院系名>` |
| 教授 / 副教授 / 研究员 | `position=<职称>` |
| 院士 | `is_academician=true` |
| 潜在招募 / 潜在引进 | `is_potential_recruit=true` |
| 顾问委员会成员 | `is_advisor_committee=true` |
| 兼职导师 | `is_adjunct_supervisor=true` |
| 有邮箱 / 能联系上 | `has_email=true` |
| 海外 / 国际 | `region=国际` |
| 高校 / 企业 / 研究机构 | `affiliation_type=<机构类型>` |
| 做具身智能 / NLP / 机器人 / AI | `keyword=<主题词>` |
| AAAI / NeurIPS 等社群 | `community_name=<社群名>`，必要时补 `community_type` |
| 教育培养 / 科研学术等项目标签 | `project_category` / `project_subcategory` |
| 学术报告 / 论坛 / 讲坛 | `event_types=<活动类型>` |
| 共建高校 / 兄弟院校 / 海外高校 | `institution_group=<分组>` |
| 京内高校 / 京外C9 / 综合强校等 | `institution_category=<分类>` |

## 3) 具体学者识别与消歧策略（关键）

用于“想看某位老师”场景。

1. 先调列表接口：
- `keyword=<姓名>`
- 若用户提供了学校/院系/职称，同时带上 `university/department/position`
- `page=1&page_size=10`

2. 在返回结果中按以下优先级重排：
- `name` 精确命中
- `university` 命中
- `department` 命中
- `position` 命中
- `has_email=true`
- `is_potential_recruit=true`

3. 决策规则：
- 若唯一高置信候选，补调 `/{url_hash}`。
- 若存在多位同名且无法消歧，只返回候选列表，不强行补调 detail。

## 4) 复杂主题二次重排策略

用于“做 X 且满足 Y”的复合筛选。

1. 首轮优先用结构化参数缩小范围：
- 如 `region=国际`、`has_email=true`、`is_potential_recruit=true`

2. 再对命中结果在调用方内存中二次重排：
- 重点字段：`research_areas`、`keywords`、`bio`、`academic_titles`
- 标签字段：`project_tags`、`event_tags`
- 用户维护字段：`custom_fields`

3. 适用场景：
- `帮我找有邮箱的海外高校AI学者`
- `看一下清华大学做具身智能的潜在招募学者`
- `有没有北大计算机学院的院士和顾问委员会成员`

## 5) 示例映射

### 示例 A：清华具身智能潜在招募学者

用户 query：`帮我看一下清华大学做具身智能的潜在招募学者`

参数：
- `GET /api/v1/scholars?university=清华大学&keyword=具身智能&is_potential_recruit=true&page=1&page_size=20`

### 示例 B：北大计算机学院的院士和顾问委员会成员

用户 query：`有没有北大计算机学院的院士和顾问委员会成员`

参数：
- `GET /api/v1/scholars?university=北京大学&department=计算机学院&is_academician=true&is_advisor_committee=true&page=1&page_size=20`

### 示例 C：海外高校有邮箱的 AI 学者

用户 query：`帮我找有邮箱的海外高校AI学者`

参数：
- `GET /api/v1/scholars?region=国际&has_email=true&keyword=AI&page=1&page_size=30`

## 6) 额外需求识别（支持度判定）

### 完全支持（supported）

- 高校、院系、职称、地区、机构类型筛选
- 院士/潜在招募/顾问委员会/兼职导师/有邮箱筛选
- 项目标签、活动标签、社群筛选
- 学者详情与导师学生关系补调

### 部分支持（partially_supported）

- 同名学者精确识别：需要依赖用户补充学校/院系信息
- “最适合引进/最值得关注”的综合排序：只能近似重排
- 原始主页链接：依赖 `profile_url` 是否存在

### 暂不支持（unsupported）

- 当前接口不存在的结构化筛选字段
- 外部论文库、专利库、引用库联查
- 用户要求必须返回每位学者的外部原始主页，但目标记录本身没有链接字段

## 7) 结果优先级重排（必须）

- `P1`：精确命中姓名/高校/院系/职称等核心约束，且与用户主目标直接相关。
- `P2`：与 query 强相关，但主要作为补充候选或字段命中不完整。
- `P3`：背景参考或待消歧候选。默认少量保留。
