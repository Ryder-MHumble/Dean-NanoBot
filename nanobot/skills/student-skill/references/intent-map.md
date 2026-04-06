# Query -> API 参数映射（Student）

## 1) 基础路由

- 学生列表：`GET /api/v1/students`
- 学生筛选项：`GET /api/v1/students/options`
- 学生详情：`GET /api/v1/students/{student_id}`

## 2) 常见意图到参数

| 用户表达 | 映射参数 |
| --- | --- |
| 清华大学学生 / 北大学生 | `institution=<高校名>` |
| 2024 级 / 2025 级 | `enrollment_year=<年份>` |
| 导师叫张三 | `mentor_name=张三` |
| 学号 240207001 | `student_no=240207001` |
| 学生叫李四 | `name=李四` |
| 毕业 / 在读 | `status=毕业|在读` |
| 某个关键词 | `keyword=<关键词>` |
| 查邮箱 | `email=<邮箱片段>` |
| 想先看有哪些年级/学校/导师 | `/students/options` |

## 3) 精准查询策略

用于“用户只说一句自然话，但实际想快速拿到一批学生”场景。

1. 若用户明确给了学校和年级：
- 直接查 `/students?institution=...&enrollment_year=...`

2. 若用户只说“看一下某导师的学生”：
- 直接查 `/students?mentor_name=...`

3. 若用户只说“看某个学生详情”：
- 先查 `/students?name=...` 或 `/students?student_no=...`
- 唯一命中后再补 `GET /api/v1/students/{student_id}`

4. 若用户问“有哪些导师/学校/年级可以选”：
- 直接查 `/students/options`

## 4) 示例映射

### 示例 A：2024 级清华学生

用户 query：`看一下 2024 级清华的学生信息`

参数：
- `GET /api/v1/students?institution=清华大学&enrollment_year=2024&page=1&page_size=20`

### 示例 B：某导师的学生

用户 query：`帮我找导师叫张三的学生`

参数：
- `GET /api/v1/students?mentor_name=张三&page=1&page_size=20`

### 示例 C：毕业状态学生

用户 query：`我想看毕业状态的学生名单`

参数：
- `GET /api/v1/students?status=毕业&page=1&page_size=20`

## 5) 额外需求识别（支持度判定）

### 完全支持（supported）

- 学校、年级、导师、姓名、学号、状态筛选
- 当前筛选下的总数
- 单个学生详情
- 年级/学校/导师可选项查询

### 部分支持（partially_supported）

- 统计分析：可返回本次筛选总数，但没有专门多维统计接口
- 模糊描述的导师/学校：可借助 `/options` 辅助，但不是语义理解型检索

### 暂不支持（unsupported）

- 外部原始信源链接
- 趋势分析、同比环比、多维交叉统计
- 跨系统联查或外部学籍系统对接

## 6) 结果优先级重排（必须）

- `P1`：精确命中学号/姓名，或同时命中学校+年级+导师等核心约束。
- `P2`：与 query 强相关，但字段命中不完整，主要作为补充样本。
- `P3`：背景参考或宽检索结果。默认少量保留，不要挤占主结果。
