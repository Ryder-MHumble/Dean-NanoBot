# Query -> API 参数映射（Institution）

## 1) 基础路由

- 机构搜索：`GET /api/v1/institutions/search`
- 机构建议匹配：`GET /api/v1/institutions/suggest`
- 机构列表：`GET /api/v1/institutions`
- 机构分类体系：`GET /api/v1/institutions/taxonomy`
- 机构详情：`GET /api/v1/institutions/{institution_id}`
- 高校动态：`GET /api/v1/intel/university/feed`
- 单篇文章详情：`GET /api/v1/intel/university/article/{url_hash}`
- 高校科研成果：`GET /api/v1/intel/university/research`

## 2) 常见意图到参数

| 用户表达 | 映射参数 |
| --- | --- |
| 机构列表 / 机构分类 | `/api/v1/institutions` |
| 机构层级 / 一级机构下看二级机构 | `view=hierarchy` |
| 扁平机构页 | `view=flat` |
| 国内 / 国际 | `region=国内|国际` |
| 高校 / 企业 / 研究机构 / 行业学会 | `org_type=<类型>` |
| 共建高校 / 兄弟院校 / 海外高校 / 其他高校 | `classification=<分类>` |
| 二级分类 | `sub_classification=<分类>` |
| 查某机构详情 | 先 `/search` 或 `/suggest`，再 `/{institution_id}` |
| 高校新闻 | `group=university_news` |
| AI研究机构动态 | `group=ai_institutes` |
| 最近一周 / 最近一个月 | `date_from=<日期>&date_to=<日期>` |
| 某个机构的动态 | `keyword=<机构名>`，必要时补 `source_name` |
| 论文 / 专利 / 获奖 | `type=论文|专利|获奖` |
| 高影响力 | `influence=高` |

## 3) 机构名解析策略（关键）

用于“用户给的是机构名，不是机构 ID”场景。

1. 优先调用：
- `GET /api/v1/institutions/suggest?institution_name=<机构名>`

2. 若 `matched` 存在：
- 直接取 `matched.id` 调 `/api/v1/institutions/{institution_id}`

3. 若只有 `suggestions`：
- 返回前 3 个候选，不强行猜 ID

4. 若搜索/建议接口不可用：
- 明确说明“静态机构接口暂时不可用”
- 不编造机构 ID

## 4) 动态与科研成果近似过滤策略

### A. 某机构最近动态

问题：`/intel/university/feed` 没有 `institution_id` 参数。

建议流程：
1. 首轮：`keyword=<机构名>`
2. 若能推断官方信源，再补 `source_name=<信源名>`
3. 若仍只能近似命中，输出时必须标注“部分支持”

### B. 某机构科研成果

问题：`/intel/university/research` 没有 `institution` 查询参数。

建议流程：
1. 先按 `type/influence/page/page_size` 拉取结果
2. 在调用方内存中对 `institution/title/detail/content/aiAnalysis/authors/field` 做二次过滤
3. 输出时明确说明这是近似方案，不是服务端精确筛选

## 5) 示例映射

### 示例 A：机构信息和合作方向

用户 query：`看一下清华大学的机构信息和重点合作方向`

参数：
1. `GET /api/v1/institutions/suggest?institution_name=清华大学`
2. `GET /api/v1/institutions/{institution_id}`

### 示例 B：最近高校动态里和中关村相关的机构新闻

用户 query：`帮我看最近高校动态里和中关村相关的机构新闻`

参数：
- `GET /api/v1/intel/university/feed?keyword=中关村&page=1&page_size=20`

### 示例 C：最近一周 AI 研究机构高影响力论文

用户 query：`看一下 AI 研究机构分组最近一周的高影响力论文`

参数：
- `GET /api/v1/intel/university/research?type=论文&influence=高&page=1&page_size=20`
- 若用户明确要求动态新闻，则改为：
  - `GET /api/v1/intel/university/feed?group=ai_institutes&date_from=<7天前>&date_to=<今天>&page=1&page_size=20`

## 6) 额外需求识别（支持度判定）

### 完全支持（supported）

- 机构列表、层级、分类、详情
- 高校动态、AI研究机构动态
- 科研成果按类型/影响力筛选
- 动态/科研成果原始链接返回

### 部分支持（partially_supported）

- 某机构最近动态：通常需要 `keyword/source_name` 近似
- 某机构科研成果：通常需要客户端二次过滤
- 静态机构外部官网链接：接口不保证提供统一官网

### 暂不支持（unsupported）

- 当前接口不存在的结构化筛选字段
- 趋势分析、同比环比、多维统计看板
- 跨系统联查或外部数据库聚合

## 7) 结果优先级重排（必须）

- `P1`：精确命中目标机构，或精确命中用户要求的主题/时间范围，且 `priority`/`influence`/相关度高。
- `P2`：与 query 强相关，但来自近似过滤、补充动态或次一级成果。
- `P3`：背景参考。默认少量保留，不要用 `P3` 替代主答案。
