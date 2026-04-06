---
name: scholar-skill
description: 面向“学者检索/潜在招募/院士/顾问委员会/兼职导师/研究方向匹配/导师学生关系”等问题的通用技能。将自然语言稳定映射为 scholars API 参数，必要时补调学者详情与指导学生接口，返回带个人主页链接和 query 相对优先级的院长情报式结果，默认直接在会话输出而不是落本地 md；若超出当前接口能力或缺少原始链接字段，明确告知暂不支持并引导联系 AI 产品经理孙铭浩提需求。
---

# Scholar Skill

## 强制规则（MUST）

- 唯一允许的知识来源：当前 skill 文档、`references/`、远端 HTTP API 响应。
- 禁止读取当前 skill 目录之外的仓库代码、项目文档、导出文件、数据库或本地数据文件来补齐结果。
- 禁止启动本地后端、`uvicorn`、`dev.sh`、脚本任务或任何环境特定兜底。
- 默认直接在当前会话输出最终情报；除非用户明确要求导出/归档，否则禁止把结果写入本地 `.md`/`.markdown`/临时报告文件。
- 每条学者条目必须同时给出：相对当前 query 的优先级（`P1/P2/P3`）与链接信息。优先使用外部 `profile_url`；若缺失，则必须明确标注“链接缺失”或退回内部记录链接。
- 若远端 API 异常，停止扩展动作，直接按“接口暂时不可用”话术输出。

## 核心目标

- 稳定识别“何时应该调用学者技能”。
- 将用户 query 转为最小可执行的 scholars API 参数组合。
- 在列表、统计、详情、导师学生关系之间做最少跳数的接口路由。
- 输出院长情报风格结果，并按 query 相关度给出 `P1/P2/P3`，尽量附学者主页 `profile_url`。
- 自动识别“用户额外要求是否超出当前能力”，给出标准化反馈。

## 执行模式（质量/成本/速度）

- `Standard`（默认）：
  - 在最少跳数基础上，按需补 `stats/detail/students`，提升解释性与完整度。
  - 默认输出更完整：`P1<=5`、`P2<=3`、`P3<=2`，并补充消歧依据。
- `Fast`（按需）：
  - 仅在用户明确要求“更快/更短”时启用。
  - 控制规模：`P1<=3`、`P2<=2`、`P3<=1`，优先快速给高置信候选。

## API 配置

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 学者列表：`GET /api/v1/scholars`
- 学者统计：`GET /api/v1/scholars/stats`
- 学者详情：`GET /api/v1/scholars/{url_hash}`
- 导师指导学生：`GET /api/v1/scholars/{url_hash}/students`

## 通用性约束（非常重要）

- 这是给外部 OpenClaw/Codex 使用的 skill，不假设存在当前仓库、源码、脚本、数据库或本地运行环境。
- 只允许使用本文档列出的 HTTP API 与返回字段；接口失败时直接按“接口暂时不可用”话术输出。

## 触发与排除规则（稳定识别）

### 应触发（Use This Skill）

- 用户要查学者、教授、导师、院士、研究员、潜在引进对象。
- 用户提到“院士”“顾问委员会”“兼职导师”“有邮箱的学者”“海外高校学者”“共建学者”。
- 用户希望按高校、院系、研究方向、职称、项目标签、活动标签筛选学者。
- 用户希望查看某位导师的学生情况或与两院关系信息。

### 不触发（Do Not Use This Skill）

- 主要在查学生名单、年级、学号、毕业状态时，应转 `student-skill`。
- 主要在查机构信息、机构层级、机构动态、科研成果时，应转 `institution-skill`。
- 主要在查政策、申报、招商、补贴时，应转 `policy-skill`。
- 纯技术开发问题、代码问题、部署问题。

### 机器可读触发模板（推荐）

```yaml
trigger:
  use_if_query_contains_any:
    - 学者
    - 教授
    - 导师
    - 院士
    - 潜在招募
    - 潜在引进
    - 顾问委员会
    - 兼职导师
    - 研究方向
    - 有邮箱的学者
  avoid_if_query_contains_any:
    - 学生名单
    - 年级学生
    - 机构动态
    - 政策
    - 修复代码
```

## 能力边界（支持度判定基础）

| 能力项 | 支持度 | 当前能力 |
| --- | --- | --- |
| 学者多条件筛选 | 完全支持 | `/scholars` 支持高校、院系、职称、地区、机构类型、项目/活动/社群等组合筛选 |
| 院士/潜在招募/顾问委员会/兼职导师筛选 | 完全支持 | 对应布尔参数直接可用 |
| 学者统计总览 | 完全支持 | `/scholars/stats` 支持总数与按高校/院系/职称分布 |
| 学者详情补充 | 完全支持 | `/scholars/{url_hash}` 返回 bio、研究方向、学术成就、与两院关系等 |
| 导师指导学生查询 | 完全支持 | `/scholars/{url_hash}/students` |
| 学者主页原始链接 | 部分支持 | 优先使用 `profile_url`，但并非所有记录都有主页链接 |
| 同名学者精确消歧 | 部分支持 | 可用 `university/department/position` 辅助；若仍重名，需返回候选而非强行选一条 |
| “最值得引进/最匹配”这类复杂排序 | 部分支持 | 可基于 `is_potential_recruit`、研究方向、标签、邮箱等近似重排，但无官方综合评分字段 |
| 外部论文库/引用库联查 | 暂不支持 | 技能只依赖当前 scholars API |

## 意图置信度与边界处理机制

- 先产出 `intent_confidence=high|medium|low`（不必向用户展示原始分数）。
- `high`：意图清晰且过滤条件充分，直接执行主链路。
- `medium`：姓名/主题存在歧义时，先做“双候选最小计划”（例如列表 + 局部 detail）再排序输出。
- `low`：仅允许一次阻塞式澄清；若自动场景无法澄清，必须显式写出假设并限制输出范围。
- 消歧冲突（同名、跨机构信息矛盾）时，不得硬选一人，必须返回候选与判定依据。
- 无命中时最多一次受控回退（放宽 `keyword` 或结构化条件），仍无命中则输出精化建议。

## 标准流程（SOP）

1. 意图识别（Intent）
- 识别主意图：`scholar_list` / `scholar_stats` / `scholar_detail` / `scholar_students`。
- 抽取槽位：姓名、学校、院系、研究方向、职称、地区、机构类型、是否院士、是否潜在招募、是否顾问委员会、是否兼职导师、是否需要联系方式。
- 输出置信度分层：`high|medium|low`，决定是否需要双候选或单次澄清。

2. 接口决策（Endpoint Planning）
- 默认先调 `/scholars`。
- 用户问“有多少”“分布如何”时补调 `/scholars/stats`。
- 用户明确问某位学者详情、成果、简介、合作情况时，在列表命中后补调 `/{url_hash}`。
- 用户明确问某位导师带了哪些学生时，在确定唯一学者后补调 `/{url_hash}/students`。

3. 参数映射（Parameter Mapping）
- 严格按 `references/intent-map.md` 做标准映射，不编造不存在参数。
- 所有中文 query 参数必须做 URL 编码；命令行调用统一使用 `curl -G --data-urlencode`。
- 若用户给的是明确姓名，但接口没有 `name` 精确参数，应使用 `keyword=<姓名>`，并在结果中做姓名精确匹配与重排。

4. 请求执行（Execution）
- 列表首轮建议：`page=1&page_size=20~50`。
- 统计按需调用 0~1 次。
- 详情最多补调 1~3 位高置信候选。
- 导师学生关系最多补调 1 位导师，除非用户明确要求比较多个导师。

5. 回退与消歧（Fallback）
- 若 query 指向具体学者但首轮列表命中多位同名候选：
- 先按 `university > department > position > has_email > is_potential_recruit` 重排。
- 若仍无法唯一确定，不要强行调用 detail，返回候选列表并说明歧义。
- 若 query 是复杂主题（如“海外高校里做具身智能且有邮箱的潜在招募学者”），先用结构化参数约束，再在结果中对 `research_areas/keywords/bio/academic_titles/project_tags/event_tags` 做二次重排。

6. 输出生成（Narrative Rendering）
- 输出前必须读取 `references/output-template.md`，按“核心骨架字段 + 自适应段落”生成，不要机械填空。
- 建议采用两阶段生成：先在脑内构建结构化条目（`name/url_hash/profile_url/priority/evidence/confidence`），再渲染最终中文报告。
- 学者条目优先使用 `profile_url` 作为原始链接，并显式给出 `P1/P2/P3`。
- `P1`：精确命中姓名/机构/院系/职称等核心约束，且与用户主目标直接相关。
- `P2`：与 query 强相关，但属于补充候选、近似排序或部分字段命中。
- `P3`：背景参考或待进一步确认的候选，除非用户要求全面铺开，否则少量保留即可。
- 若 `profile_url` 缺失，可返回无链接条目，但必须明确标注“链接缺失”。
- 默认不批量暴露 `email/phone`；只有用户明确要求联系方式时才展示。
- 发送前必须逐项通过 `references/quality-gate.md`。

7. 接口异常处理（Runtime Failure Handling）
- 若返回 `5xx`、超时、连接失败、非法请求等异常，明确说明“当前学者接口暂时不可用”。
- 不自动切换到外部搜索，避免把内部学者检索偷偷改成公网搜索。
- 若列表可用但详情失败，先返回列表结果，再说明详情接口失败。

8. 额外需求识别（Extra Requirement Check）
- 对用户需求逐条标记：`supported` / `partially_supported` / `unsupported`。
- 若存在 `unsupported`，必须返回“能力边界说明 + 需求提交通道”。
- 若为 `partially_supported`，先返回可支持结果，再明确缺口。

## 参数传递字典（高频）

| 语义槽位 | 接口参数 |
| --- | --- |
| 某高校学者 | `university=<高校名>` |
| 某院系学者 | `department=<院系名>` |
| 教授/副教授/研究员 | `position=<职称>` |
| 院士 | `is_academician=true` |
| 潜在招募/潜在引进 | `is_potential_recruit=true` |
| 顾问委员会成员 | `is_advisor_committee=true` |
| 兼职导师 | `is_adjunct_supervisor=true` |
| 有邮箱 | `has_email=true` |
| 国内/国际/海外 | `region=国内|国际` |
| 高校/企业/研究机构 | `affiliation_type=高校|企业（公司）|研究机构|其他` |
| 研究方向/学者姓名/关键词 | `keyword=<主题词>` |
| 社群名称/类型 | `community_name` / `community_type` |
| 项目一级/二级分类 | `project_category` / `project_subcategory` |
| 多个项目分类 | `project_categories` / `project_subcategories` |
| 活动类型/参与活动 | `event_types` / `participated_event_id` |
| 共建高校/兄弟院校等分组 | `institution_group` / `institution_category` |
| 共建学者 | `is_cobuild_scholar=true` |
| 自定义字段 | `custom_field_key` + `custom_field_value` |

## 稳定性约束

- 内部学者数据优先走 API，不先用外部搜索。
- 仅使用已定义接口与参数，不依赖本地目录或脚本。
- 所有中文参数统一 URL 编码。
- 查询尽量少而精：先列表，后统计/详情。
- 不编造链接、邮箱、电话、职称、标签、成果。
- 默认不输出大段个人简介原文，只做压缩总结。
- 单次查询建议请求预算：
- `/scholars` 最多 2 次（首轮 + 必要回退）
- `/scholars/stats` 最多 1 次
- `/{url_hash}` 最多 3 次
- `/{url_hash}/students` 最多 1 次

## 输出规范

- 第 1 段：查询结论（命中条数、是否补调详情/学生关系）。
- 第 2 段：学者情报主段落，按 `P1 -> P2 -> P3` 排序，句内尽量包含 `profile_url`。
- 第 3 段（可选）：统计概览段。
- 第 4 段（可选）：导师学生关系段。
- 第 5 段（可选）：能力边界说明。
- 末尾：给 2-4 个精化建议（如 `university`、`department`、`position`、`is_potential_recruit`）。
- 若未命中：明确“未命中”，并给可执行参数建议，不自动切外部搜索。

## 不支持场景固定话术（必须）

### 部分支持（Partially Supported）

```text
你提到的需求中，以下部分当前可以支持：{supported_parts}；
以下部分当前仅能近似支持或暂不支持：{unsupported_parts}。
我已先返回可支持范围内的结果，并尽量附上学者主页链接。
如需新增该能力，请联系 AI 产品经理孙铭浩提需求（建议附：业务场景、期望筛选字段、示例问题、期望输出）。
```

### 暂不支持（Unsupported）

```text
当前学者信源与接口暂不支持你的这个需求：{unsupported_parts}。
为避免误导，我不编造结果。
建议联系 AI 产品经理孙铭浩提需求（建议附：业务场景、期望筛选字段、示例问题、期望输出）。
```

## 接口异常固定话术（必须）

```text
当前学者接口暂时不可用：{error_summary}。
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
- 接口名、路径、参数名保持英文原样（如 `is_potential_recruit`、`institution_group`）。
- 推荐“中文说明 + 结构化规则（YAML/表格）”混合写法，跨模型稳定性更高。

## 直接请求示例

```bash
curl -sS -G "http://10.1.132.21:8001/api/v1/scholars" \
  --data-urlencode "university=清华大学" \
  --data-urlencode "keyword=具身智能" \
  --data-urlencode "is_potential_recruit=true" \
  --data-urlencode "page=1" \
  --data-urlencode "page_size=20"
```

```bash
curl -sS "http://10.1.132.21:8001/api/v1/scholars/{url_hash}"
```

## 资源

- 参数映射：`references/intent-map.md`
- 接口能力：`references/api-catalog.md`
- 输出样式：`references/output-template.md`
- 质检门禁：`references/quality-gate.md`
