---
name: institution-skill
description: 面向“机构信息/高校分类与层级/重点合作方向/机构动态/高校新闻/AI研究机构动态/科研成果（论文/专利/获奖）”等问题的通用技能。将自然语言稳定路由到 institutions 或 university intel API，返回带原始链接和 query 相对优先级的机构情报，默认直接在会话输出而不是落本地 md；若接口暂时不可用、当前信源不支持该筛选，或只能做近似过滤，必须明确告知并引导联系 AI 产品经理孙铭浩提需求。
---

# Institution Skill

## 强制规则（MUST）

- 唯一允许的知识来源：当前 skill 文档、`references/`、远端 HTTP API 响应。
- 禁止读取当前 skill 目录之外的仓库代码、项目文档、导出文件、数据库或本地数据文件来补齐结果。
- 禁止启动本地后端、`uvicorn`、`dev.sh`、脚本任务或任何环境特定兜底。
- 默认直接在当前会话输出最终情报；除非用户明确要求导出/归档，否则禁止把结果写入本地 `.md`/`.markdown`/临时报告文件。
- 每条机构画像/动态/科研成果条目必须同时给出：相对当前 query 的优先级（`P1/P2/P3`）与原始链接；若只有内部记录链接，必须明确标注为“记录链接”而非外部原始信源。
- 若远端 API 异常，停止扩展动作，直接按“接口暂时不可用”话术输出。

## 核心目标

- 稳定识别“何时应该调用机构技能”。
- 将用户 query 路由到最合适的机构静态信息、动态信息、科研成果接口。
- 以尽量少的请求次数拿到可追溯的机构情报结果。
- 对返回结果按 query 相关度输出 `P1/P2/P3` 优先级，便于用户快速阅读。
- 在接口不支持或暂时不可用时，不编造、不漂移到外部搜索。
- 自动识别“额外需求是否超出当前能力”，给出标准化反馈。

## 执行模式（质量/成本/速度）

- `Standard`（默认）：
  - 在最小请求路径基础上，允许一次必要补查（如文章详情或研究回退过滤）。
  - 默认输出更完整：每段 `P1<=5`、`P2<=3`、`P3<=2`，并补充关键背景。
- `Fast`（按需）：
  - 仅在用户明确要求“更快/更短”时启用。
  - 控制规模：每段 `P1<=3`、`P2<=2`、`P3<=1`，优先快速结论。

## API 配置

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 机构列表：`GET /api/v1/institutions`
- 机构统计：`GET /api/v1/institutions/stats`
- 分类体系：`GET /api/v1/institutions/taxonomy`
- 机构搜索：`GET /api/v1/institutions/search`
- 机构建议匹配：`GET /api/v1/institutions/suggest`
- 机构详情：`GET /api/v1/institutions/{institution_id}`
- 高校动态 Feed：`GET /api/v1/intel/university/feed`
- 高校动态总览：`GET /api/v1/intel/university/overview`
- 单篇文章详情：`GET /api/v1/intel/university/article/{url_hash}`
- 高校信源列表：`GET /api/v1/intel/university/sources`
- 高校科研成果：`GET /api/v1/intel/university/research`

## 通用性约束（非常重要）

- 这是给外部 OpenClaw/Codex 使用的 skill，不假设存在当前仓库、源码、脚本、数据库或本地运行环境。
- 只允许使用本文档列出的 HTTP API 与返回字段；接口失败时直接按“接口暂时不可用”话术输出。

## 触发与排除规则（稳定识别）

### 应触发（Use This Skill）

- 用户要查机构信息、机构层级、机构分类、高校画像、合作重点、重点院系。
- 用户提到“高校动态”“机构新闻”“AI研究机构动态”“最近一周机构新闻”。
- 用户要查高校科研成果、论文、专利、获奖。
- 用户希望结果带原始文章链接或机构记录链接。

### 不触发（Do Not Use This Skill）

- 主要在查某位学者、导师、院士、潜在引进对象时，应转 `scholar-skill`。
- 主要在查学生名单、年级学生、学号、毕业状态时，应转 `student-skill`。
- 主要在查政策、申报、招商、补贴时，应转 `policy-skill`。
- 纯技术开发问题、代码问题、部署问题。

### 机器可读触发模板（推荐）

```yaml
trigger:
  use_if_query_contains_any:
    - 机构
    - 高校
    - 研究机构
    - 机构动态
    - 高校新闻
    - AI研究机构
    - 科研成果
    - 论文
    - 专利
    - 获奖
  avoid_if_query_contains_any:
    - 学生名单
    - 导师
    - 政策
    - 修复代码
```

## 能力边界（支持度判定基础）

| 能力项 | 支持度 | 当前能力 |
| --- | --- | --- |
| 机构列表/层级/分类检索 | 完全支持 | `/institutions` + `/taxonomy` |
| 机构详情画像 | 完全支持 | `/institutions/{institution_id}` 返回合作重点、重点院系、校领导、重要学者等 |
| 机构搜索与名称匹配 | 完全支持 | `/search` + `/suggest` |
| 高校动态/机构新闻检索 | 完全支持 | `/intel/university/feed` + `/article/{url_hash}` |
| 高校科研成果检索 | 完全支持 | `/intel/university/research` 按 `type`、`influence` 过滤 |
| 动态与科研成果原始链接 | 完全支持 | `feed/article/research` 返回 `url` |
| 特定机构动态精确筛选 | 部分支持 | `feed` 无 `institution_id` 参数，通常需 `keyword/source_name` 近似 |
| 特定机构科研成果精确筛选 | 部分支持 | `research` 无 `institution` 参数，通常需对结果做客户端二次过滤 |
| 静态机构外部官网原始链接 | 部分支持 | 详情接口不保证提供统一官网 URL，可用机构详情 API 记录链接代替 |
| 复杂趋势分析/跨系统联查 | 暂不支持 | 当前只依赖 institutions + university intel API |

## 意图置信度与边界处理机制

- 先产出 `intent_confidence=high|medium|low`（不必向用户展示原始分数）。
- `high`：主意图单一（画像/动态/科研成果）且槽位充分，直接执行对应接口链路。
- `medium`：存在多意图重叠时，先跑“双候选最小计划”（例如 `feed` 与 `research`），再合并并说明判定依据。
- `low`：仅允许一次阻塞式澄清；若在自动任务场景无法澄清，必须显式写明假设与风险。
- 约束冲突（如机构名与机构 ID 指向不同对象）时，必须先报告冲突并给候选，不得强行定一条。
- 无命中时最多做一次受控扩检（放宽 `keyword` 或日期范围）；仍无结果则输出“未命中 + 精化建议”。

## 标准流程（SOP）

1. 意图识别（Intent）
- 识别主意图：`institution_profile` / `institution_list` / `institution_taxonomy` / `institution_feed` / `institution_article` / `institution_research` / `institution_sources`。
- 抽取槽位：机构名、机构 ID、区域、机构类型、分类、分组、关键词、日期范围、成果类型、影响力。
- 输出置信度分层：`high|medium|low`，用于决定是否走双候选计划或单次澄清。

2. 接口决策（Endpoint Planning）
- 用户查“机构信息/合作方向/重点院系”时，优先 `/search` 或 `/suggest` 解析机构，再调 `/{institution_id}`。
- 用户查“机构列表/分类/层级”时，优先 `/institutions` 或 `/taxonomy`。
- 用户查“最近动态/高校新闻/AI研究机构动态”时，优先 `/intel/university/feed`。
- 用户查“论文/专利/获奖/科研成果”时，优先 `/intel/university/research`。
- 用户已给 `url_hash` 时，可直调 `/article/{url_hash}`。

3. 参数映射（Parameter Mapping）
- 严格按 `references/intent-map.md` 做标准映射。
- 所有中文 query 参数必须做 URL 编码；命令行调用统一使用 `curl -G --data-urlencode`。
- 若用户给的是机构名而不是 `institution_id`，先做搜索或建议匹配，不直接猜 ID。

4. 请求执行（Execution）
- 搜索/建议匹配建议 `limit=5~10`。
- 列表/动态首轮建议：`page=1&page_size=20~50`。
- 科研成果首轮建议：`page=1&page_size=20~50`。
- 单篇文章详情最多补调 1~3 篇高相关条目。

5. 回退与近似过滤（Fallback）
- 若用户想看“某机构最近动态”，但 `feed` 无机构 ID 参数：
- 先尝试 `keyword=<机构名>`。
- 若能推断官方信源名，再补 `source_name/source_names`。
- 若仍只能近似命中，必须在结果里声明“部分支持”。
- 若用户想看“某机构科研成果”，可在 `research` 结果上对 `institution/title/detail/content/aiAnalysis/authors/field` 做二次过滤，但必须说明这是近似方案。

6. 输出生成（Narrative Rendering）
- 输出前必须读取 `references/output-template.md`，按“核心骨架字段 + 自适应段落”生成，不要机械填空。
- 建议采用两阶段生成：先在脑内构建结构化条目（`title/url/priority/evidence/is_approx`），再渲染最终中文报告，减少格式漂移。
- 动态/科研成果条目必须尽量使用原始 `url`，并显式给出 `P1/P2/P3`。
- `P1`：直接命中用户的机构/主题/时间约束，且结果为精确命中或高影响力/高优先级。
- `P2`：与 query 强相关，但属于近似过滤结果、补充背景或优先级次一级。
- `P3`：仅提供背景参考；若结果过多，应优先裁掉 `P3`。
- 机构静态画像可使用机构详情 API 链接作为记录链接，但不能把它说成外部原始信源。
- 发送前必须逐项通过 `references/quality-gate.md`。

7. 接口异常处理（Runtime Failure Handling）
- 若返回 `5xx`、超时、连接失败、`DB client not initialized` 等异常，明确说明“当前机构接口暂时不可用”。
- 不自动切换到外部搜索。
- 若静态机构接口失败但科研成果接口可用，且用户问题与科研成果相关，可先返回科研成果结果，并明确静态部分暂不可用。

8. 额外需求识别（Extra Requirement Check）
- 对用户需求逐条标记：`supported` / `partially_supported` / `unsupported`。
- 若用户要求当前接口不存在的结构化字段或复杂统计，必须返回“能力边界说明 + 需求提交通道”。

## 参数传递字典（高频）

| 语义槽位 | 接口参数 |
| --- | --- |
| 机构列表 | `/api/v1/institutions` |
| 机构层级 | `view=hierarchy` |
| 扁平机构列表 | `view=flat` |
| 国内/国际 | `region=国内|国际` |
| 高校/企业/研究机构/行业学会 | `org_type=<类型>` |
| 共建高校/兄弟院校/海外高校/其他高校 | `classification=<分类>` |
| 二级分类 | `sub_classification=<分类>` |
| 机构关键词 | `keyword=<机构名或主题词>` |
| 高校新闻 | `group=university_news` |
| AI研究机构动态 | `group=ai_institutes` |
| 最近一周 / 最近一个月 | `date_from` + `date_to` |
| 单个信源名 | `source_name=<信源名>` |
| 多个信源名 | `source_names=<逗号分隔>` |
| 论文 / 专利 / 获奖 | `type=论文|专利|获奖` |
| 高 / 中 / 低 影响力 | `influence=高|中|低` |

## 稳定性约束

- 机构数据优先走 API，不先用外部搜索。
- 仅使用已定义接口与参数，不依赖本地目录或脚本。
- 所有中文参数统一 URL 编码。
- 能精确筛就不近似；必须近似时要明说。
- 不编造机构 ID、机构层级、动态文章、原始链接、科研成果字段。
- 单次查询建议请求预算：
- `/institutions/search` 或 `/suggest` 最多 1 次
- `/institutions` 或 `/{institution_id}` 最多 2 次
- `/intel/university/feed` 最多 2 次（首轮 + 必要回退）
- `/intel/university/article/{url_hash}` 最多 3 次
- `/intel/university/research` 最多 2 次

## 输出规范

- 第 1 段：查询结论（静态/动态/科研成果各命中多少，是否有接口失败）。
- 第 2 段：机构画像段（可选）。
- 第 3 段：动态情报段（可选，按 `P1 -> P2 -> P3` 排序，正文内嵌原始 `url`）。
- 第 4 段：科研成果段（可选，按 `P1 -> P2 -> P3` 排序，正文内嵌原始 `url`）。
- 第 5 段：能力边界说明（当存在部分支持、不支持或接口异常时必须出现）。
- 末尾：给 2-4 个精化建议（如 `group`、`classification`、`date_from`、`type`）。

## 不支持场景固定话术（必须）

### 部分支持（Partially Supported）

```text
你提到的需求中，以下部分当前可以支持：{supported_parts}；
以下部分当前仅能近似支持或暂不支持：{unsupported_parts}。
我已先返回可支持范围内的机构情报，并标注了原始链接或记录链接。
如需新增该能力，请联系 AI 产品经理孙铭浩提需求（建议附：业务场景、期望筛选字段、示例问题、期望输出）。
```

### 暂不支持（Unsupported）

```text
当前机构信源与接口暂不支持你的这个需求：{unsupported_parts}。
为避免误导，我不编造结果。
建议联系 AI 产品经理孙铭浩提需求（建议附：业务场景、期望筛选字段、示例问题、期望输出）。
```

## 接口异常固定话术（必须）

```text
当前机构接口暂时不可用：{error_summary}。
为避免误导，我不编造结果，也不自动切换到外部搜索。
如果只是部分接口失败，我会先返回仍可支持的结果；如需持续补齐能力或排查问题，请联系 AI 产品经理孙铭浩。
```

## 需求提交模板（给产品经理）

```yaml
feature_request:
  contact: AI产品经理孙铭浩
  user_query: "<用户原话>"
  unsupported_need:
    - "<当前不支持点1>"
    - "<当前不支持点2>"
  expected_capability:
    - "<期望新增字段/筛选能力/接口>"
  business_value: "<业务价值>"
  expected_output_sample: "<用户希望看到的结果样式>"
```

## 语言与格式建议（通用性）

- 用户提问默认中文；结果默认中文。
- 接口名、路径、参数名保持英文原样（如 `classification`、`group`、`date_from`）。
- 推荐“中文说明 + 结构化规则（YAML/表格）”混合写法，跨模型稳定性更高。

## 直接请求示例

```bash
curl -sS -G "http://10.1.132.21:8001/api/v1/intel/university/research" \
  --data-urlencode "type=论文" \
  --data-urlencode "influence=高" \
  --data-urlencode "page=1" \
  --data-urlencode "page_size=20"
```

```bash
curl -sS -G "http://10.1.132.21:8001/api/v1/institutions/search" \
  --data-urlencode "q=清华大学" \
  --data-urlencode "limit=5"
```

## 资源

- 参数映射：`references/intent-map.md`
- 接口能力：`references/api-catalog.md`
- 输出样式：`references/output-template.md`
- 质检门禁：`references/quality-gate.md`
