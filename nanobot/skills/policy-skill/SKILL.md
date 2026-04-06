---
name: policy-skill
description: 面向“政策检索/申报机会/招商项目/人才转化”等问题的通用技能。将自然语言稳定映射为 policy API 参数，返回带原始信源链接和 query 相对优先级的院长早报风格情报，默认直接在会话输出而不是落本地 md；若超出当前信源能力，明确告知暂不支持并引导联系 AI 产品经理孙铭浩提需求。
---

# Policy Skill

## 强制规则（MUST）

- 唯一允许的知识来源：当前 skill 文档、`references/`、远端 HTTP API 响应。
- 禁止读取当前 skill 目录之外的仓库代码、项目文档、导出文件、数据库或本地数据文件来补齐结果。
- 禁止启动本地后端、`uvicorn`、`dev.sh`、脚本任务或任何环境特定兜底。
- 默认直接在当前会话输出最终情报；除非用户明确要求导出/归档，否则禁止把结果写入本地 `.md`/`.markdown`/临时报告文件。
- 每条政策/机会条目必须同时给出：相对当前 query 的优先级（`P1/P2/P3`）与原始 `sourceUrl`；若链接缺失，必须明确标注“原始链接缺失”。
- 若远端 API 异常，停止扩展动作，直接按“接口暂时不可用”话术输出。

## 核心目标

- 稳定识别“何时应该调用政策技能”。
- 将用户 query 转为最小可执行的 API 参数组合。
- 以尽量少的请求次数拿到可追溯、可阅读的政策情报结果。
- 输出院长早报风格叙事，并按 query 相关度给出 `P1/P2/P3` 优先级，在正文中附原始 `sourceUrl`。
- 自动识别“额外需求是否超出当前信源能力”，并给出标准化反馈。

## 执行模式（质量/成本/速度）

- `Standard`（默认）：
  - 在最小请求路径基础上，允许一次必要回退（命中不足时扩大范围或补查）。
  - 默认输出更完整：`P1<=5`、`P2<=5`、`P3<=2`，并补充背景与行动含义。
- `Fast`（按需）：
  - 仅在用户明确要求“更快/更短”时启用。
  - 控制规模：`P1<=3`、`P2<=3`、`P3<=1`，优先快速给结论。

## API 配置

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 政策动态：`GET /api/v1/intel/policy/feed`
- 政策机会：`GET /api/v1/intel/policy/opportunities`
- 统计信息：`GET /api/v1/intel/policy/stats`

## 通用性约束（非常重要）

- 这是给外部 OpenClaw/Codex 使用的 skill，不假设存在当前仓库、源码、脚本、数据库或本地运行环境。
- 只允许使用本文档列出的 HTTP API 与返回字段；接口失败时直接按“接口暂时不可用”话术输出。

## 触发与排除规则（稳定识别）

### 应触发（Use This Skill）

- 用户要查政策信息、政策动向、政策机会、申报项目、招商项目、资金补贴。
- 用户提到“人才政策、成果转化、成功转化、项目落地、高匹配政策、重点政策”。
- 用户希望按来源/地区/匹配度/重要性做政策筛选。
- 用户希望结果带原始出处链接并可直接追溯。

### 不触发（Do Not Use This Skill）

- 纯技术开发问题（代码、部署、报错排查）。
- 明确要求外部新闻综述且不依赖内部政策数据。
- 与政策数据无关的通用问答。

### 机器可读触发模板（推荐）

```yaml
trigger:
  use_if_query_contains_any:
    - 政策
    - 申报
    - 招商
    - 补贴
    - 资金支持
    - 人才政策
    - 成果转化
    - 成功转化
    - 项目落地
    - 高匹配政策
  avoid_if_query_contains_any:
    - 修复代码
    - 部署
    - 单元测试
    - 数据库迁移
```

## 能力边界（支持度判定基础）

| 能力项 | 支持度 | 当前能力 |
| --- | --- | --- |
| 政策动态检索 | 完全支持 | `feed` 按分类、重要性、匹配度、关键词、信源筛选 |
| 申报/招商/资金机会检索 | 完全支持 | `opportunities` 按状态、匹配度筛选 |
| 原始信源回溯 | 完全支持 | 依赖 `sourceUrl` 字段 |
| 正文级二次过滤 | 完全支持 | 可对 `title/summary/content/detail/aiInsight/signals/tags` 重排 |
| 超细粒度地区筛选（如区县、园区） | 部分支持 | 通过 `keyword`/`source_name` 近似，暂无专属结构化字段 |
| 自定义复杂统计口径（同比/环比/多维交叉） | 暂不支持 | 当前仅有 `stats` 基础计数 |
| 外部数据库联查/跨系统聚合 | 暂不支持 | 技能只依赖当前 policy API |

## 意图置信度与边界处理机制

- 先产出 `intent_confidence=high|medium|low`（不必向用户展示原始分数）。
- `high`：主意图单一且槽位充分，直接执行目标接口。
- `medium`：主意图可能有两种以上解释时，先做“双候选计划”（例如 `feed` 与 `opportunities` 各跑一条最小请求），再合并结果并标注假设。
- `low`：仅允许一次阻塞式澄清；若场景不便澄清（如定时任务），必须显式写出假设并仅返回保守结果。
- 约束冲突（如“只看北京政策”同时“只看国家政策”）时，不得硬猜，必须先指出冲突并给可执行拆分方案。
- 无命中时按“受控扩检”处理：最多一次放宽参数，仍无结果就输出“未命中 + 下一步精化建议”，不编造。

## 标准流程（SOP）

1. 意图识别（Intent）
- 识别主意图：`policy_feed` / `policy_opportunities` / `policy_stats`。
- 抽取槽位：主题词、地区层级、重要性、匹配度、来源约束、是否机会类。
- 输出置信度分层：`high|medium|low`，作为后续请求策略开关。

2. 接口决策（Endpoint Planning）
- 默认先调 `feed`。
- 命中“机会/申报/资金/招商/重大项目”时并行或补调 `opportunities`。
- 仅需总量时可调 `stats`。

3. 参数映射（Parameter Mapping）
- 按 `references/intent-map.md` 做标准映射，不编造不存在参数。
- 参数优先级：明确用户约束 > 映射规则默认值。
- 所有中文 query 参数必须做 URL 编码；命令行调用统一使用 `curl -G --data-urlencode`。

4. 请求执行（Execution）
- 首轮：`feed` 用精准参数请求，建议 `limit=50~80`、`offset=0`。
- 机会类：`opportunities` 建议 `limit=30~50`。
- 失败或命中不足时仅扩大必要参数，避免无界请求。

5. 回退策略（Fallback）
- 当首轮命中不足（建议 `<3`）且 query 有明确主题词时：
- 去掉 `keyword`，`limit` 提升至 `120~200` 重查 `feed`。
- 在调用方内存中对 `title/summary/content/detail/aiInsight/signals/tags` 做正文级过滤与重排。

6. 输出生成（Narrative Rendering）
- 输出前必须读取 `references/output-template.md`，按“核心骨架字段 + 自适应段落”生成，不要机械填空。
- 建议采用两阶段生成：先在脑内构建结构化条目（`title/sourceUrl/priority/evidence`），再渲染最终中文报告，减少格式漂移。
- 每条情报句必须内嵌原始 `sourceUrl`，并显式给出 `P1/P2/P3`。
- `P1`：直接命中用户核心主题/地区/时间约束，且 `importance`/`matchScore`/行动紧迫性高。
- `P2`：与 query 强相关，但更偏补充背景、近似命中或优先级次一级。
- `P3`：仅作为背景参考，除非用户要求全面铺开，否则少量保留即可。
- 若链接缺失，明确标注“链接缺失”。
- 发送前必须逐项通过 `references/quality-gate.md`。

7. 接口异常处理（Runtime Failure Handling）
- 若返回 `5xx`、超时、连接失败、`Invalid HTTP request received.` 等异常，明确说明“当前政策接口暂时不可用”。
- 不自动切换到外部 `web_search`，避免把内部政策问答偷偷改成公网搜索。
- 若部分接口仍可用，先返回可用部分结果，再说明失败范围。

8. 额外需求识别（Extra Requirement Check）
- 对用户需求逐条标记：`supported` / `partially_supported` / `unsupported`。
- 若存在 `unsupported`，必须返回“能力边界说明 + 需求提交通道”。
- 若为 `partially_supported`，先返回可支持结果，再明确缺口。

## 参数传递字典（高频）

| 语义槽位 | 接口参数 |
| --- | --- |
| 国家层面 | `category=国家政策` |
| 北京层面（北京/海淀/中关村） | `category=北京政策` |
| 领导讲话 | `category=领导讲话` |
| 紧急/立即 | `importance=紧急`，机会类可补 `status=urgent` |
| 重点/高优 | `importance=重要` |
| 跟踪/关注 | `importance=关注`，机会类可补 `status=tracking` |
| 高相关/高匹配 | `min_match_score=70` |
| 宽检索 | `min_match_score=40~50` |
| 部委/机构定向 | `source_name` 或 `source_names` |
| 多信源定向 | `source_ids` |
| 分页 | `limit` + `offset` |

## 稳定性约束

- 内部政策数据优先走 API，不先用 `web_search`。
- 仅使用已定义接口与参数，不依赖本地目录或脚本。
- 所有中文参数统一 URL 编码，避免服务端把中文 query string 判成非法请求。
- 请求尽量少而精：先精确，再按需回退。
- 输出不编造字段；事实、数字、日期、来源均来自 API 响应。
- 单次查询建议请求预算：
- `feed` 最多 2 次（首轮 + 回退）
- `opportunities` 最多 1 次
- `stats` 按需 0~1 次

## 输出规范

- 第 1 段：查询结论（命中条数、是否启用正文级过滤）。
- 第 2 段：政策情报主段落，按 `P1 -> P2 -> P3` 排序，句内包含 `[标题](sourceUrl)` 与 `原始链接`。
- 第 3 段（可选）：政策机会段落，按 `P1 -> P2 -> P3` 排序，包含资金/截止日/状态与原始链接。
- 第 4 段（可选）：能力边界说明（当存在部分支持或不支持需求时必须出现）。
- 末尾：给 2-4 个可选精化参数建议（如 `category`、`importance`、`min_match_score`、`source_name`）。
- 若未命中：明确“未命中”，并给可执行参数建议，不自动跳外部搜索。

## 不支持场景固定话术（必须）

### 部分支持（Partially Supported）

```text
你提到的需求中，以下部分当前可以支持：{supported_parts}；
以下部分当前仅能近似支持或暂不支持：{unsupported_parts}。
我已先返回可支持范围内的结果，并标注了原始链接。
如需新增该能力，请联系 AI 产品经理孙铭浩提需求（建议附：业务场景、期望筛选字段、示例问题、期望输出）。
```

### 暂不支持（Unsupported）

```text
当前信源与接口暂不支持你的这个需求：{unsupported_parts}。
为避免误导，我不编造结果。
建议联系 AI 产品经理孙铭浩提需求（建议附：业务场景、期望筛选字段、示例问题、期望输出）。
```

## 接口异常固定话术（必须）

```text
当前政策接口暂时不可用：{error_summary}。
为避免误导，我不编造结果，也不自动切换到外部搜索。
如果只是一部分接口失败，我会先返回仍可支持的结果；如需补齐能力或持续排查，请联系 AI 产品经理孙铭浩。
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

- 用户提问可为中文自然语句；结果默认中文。
- 接口名、路径、参数名、状态枚举值保持英文原样（如 `min_match_score`、`status=active`）。
- 推荐“中文说明 + 结构化规则（YAML/表格）”混合写法，跨模型稳定性更高。

## 直接请求示例

```bash
curl -G "http://10.1.132.21:8001/api/v1/intel/policy/feed" \
  --data-urlencode "keyword=人才成功转化" \
  --data-urlencode "limit=80" \
  --data-urlencode "offset=0"
```

```bash
curl -G "http://10.1.132.21:8001/api/v1/intel/policy/opportunities" \
  --data-urlencode "status=active" \
  --data-urlencode "min_match_score=50" \
  --data-urlencode "limit=50" \
  --data-urlencode "offset=0"
```

## 资源

- 参数映射：`references/intent-map.md`
- 接口能力：`references/api-catalog.md`
- 输出样式：`references/output-template.md`
- 质检门禁：`references/quality-gate.md`
