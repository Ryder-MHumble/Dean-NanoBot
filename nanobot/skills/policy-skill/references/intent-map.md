# Query -> API 参数映射（Policy）

## 1) 基础路由

- 政策动态：`GET /api/v1/intel/policy/feed`
- 政策机会：`GET /api/v1/intel/policy/opportunities`
- 统计信息：`GET /api/v1/intel/policy/stats`

## 2) 常见意图到参数

| 用户表达 | 映射参数 |
| --- | --- |
| 国家政策 / 部委政策 | `category=国家政策` |
| 北京政策 / 海淀 / 中关村 | `category=北京政策` |
| 领导讲话 / 领导指示 | `category=领导讲话` |
| 紧急 / 立即跟进 | `importance=紧急`；机会类补 `status=urgent` |
| 重点 / 高优 / 核心 | `importance=重要` |
| 关注 / 跟踪 | `importance=关注`；机会类可补 `status=tracking` |
| 高相关 / 精准匹配 | `min_match_score=70` |
| 相关即可 / 宽一点 | `min_match_score=40~50` |
| 教育部 / 科技部 / 工信部 / 北京市科委 | `source_name=<机构名>` |
| 资金 / 补贴 / 申报 / 项目 | 同时查询 `feed + opportunities` |
| 招商 / 重大项目 / 项目落地 | 优先 `opportunities`，并保留 `feed` 佐证 |

## 3) 正文级检索策略（关键）

用于“标题没写，但正文提到了 X”场景。

1. 首轮：带 `keyword` 查 `feed`。
2. 若命中不足（通常 `<3`）：
- 取消 `keyword`，扩大 `limit`（建议 120~200）。
- 在调用方内存中对 `title/summary/content/detail/aiInsight/signals/tags` 二次过滤。
3. 过滤词建议优先级：
- 用户明确短语（`【...】`、引号内容）
- 业务词（如 `人才`、`成功转化`、`招商`、`重大项目`）

## 4) 示例映射

### 示例 A：人才成功转化（标题未出现）

用户 query：`看一下人才政策里提到人才成功转化的信息`

首轮参数：
- `GET /api/v1/intel/policy/feed?keyword=人才成功转化&limit=80`

若命中不足，二次过滤：
- `GET /api/v1/intel/policy/feed?limit=200`
- 二次过滤词：`人才`、`成功转化`、`成果转化`

### 示例 B：北京重大招商项目

用户 query：`看北京近期重大招商项目`

参数：
- `GET /api/v1/intel/policy/feed?category=北京政策&keyword=招商项目&limit=80`
- `GET /api/v1/intel/policy/opportunities?status=active&limit=50`

### 示例 C：国家层面高匹配政策

用户 query：`给我国家层面高匹配政策`

参数：
- `GET /api/v1/intel/policy/feed?category=国家政策&min_match_score=70&limit=50`

## 5) 额外需求识别（支持度判定）

### 完全支持（supported）

- 分类筛选：`category`
- 重要性：`importance`
- 匹配度：`min_match_score`
- 信源筛选：`source_id/source_ids/source_name/source_names`
- 机会状态：`status`

### 部分支持（partially_supported）

- 区县/园区等细粒度地域：可用 `keyword` + `source_name` 近似，不是结构化字段。
- 复杂主题组合（如“人才 + 成功转化 + 区县 + 行业”）：可做正文级过滤近似。

### 暂不支持（unsupported）

- API 未定义字段的筛选条件（如自定义统计口径、外部数据库联查、跨系统聚合）。
- 用户要求必须基于当前接口不存在的结构化维度输出。

### 决策规则

1. 若全部需求可映射到现有参数，正常执行并返回。
2. 若部分可映射，先返回可支持结果，再输出“能力边界说明”。
3. 若核心需求不可映射，直接明确“当前暂不支持”，并引导联系 AI 产品经理孙铭浩提需求。

## 6) 结果优先级重排（必须）

- `P1`：同时满足用户核心主题词、地区/来源/时间等主约束，且 `importance` 高、`matchScore` 高或需要优先行动。
- `P2`：满足主要主题词，但地区/来源/时间等约束不完全，或主要作为背景补充。
- `P3`：只提供弱相关背景参考。默认少量保留，不要用 `P3` 挤占主结果。
