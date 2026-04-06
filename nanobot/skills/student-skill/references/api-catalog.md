# Student API Catalog（通用版）

- 服务基址（由服务方提供）：`http://10.1.132.21:8001`
- 所有接口均为 `GET` 请求，参数走 query string。
- 含中文的参数值必须做 URL 编码；命令行建议统一使用 `curl -G --data-urlencode`。

## 1) 学生列表

### `GET /api/v1/students`

用途：学生主检索接口。

参数：
- `institution`: 机构/共建高校（模糊匹配）
- `grade`: 兼容参数，建议优先使用 `enrollment_year`
- `enrollment_year`: 入学年级
- `home_university`: 兼容参数，建议优先使用 `institution`
- `mentor_name`: 导师姓名
- `name`: 学生姓名
- `email`: 邮箱片段
- `student_no`: 学号片段
- `status`: 在读状态，如 `在读` / `毕业`
- `keyword`: 姓名/学号/学校/导师/邮箱
- `page`, `page_size`

关键返回字段：
- `total`, `page`, `page_size`, `total_pages`
- `items[]`:
  - `id`, `scholar_id`
  - `student_no`, `name`
  - `home_university`, `enrollment_year`
  - `status`, `major`
  - `email`, `phone`
  - `mentor_name`

## 2) 学生筛选项

### `GET /api/v1/students/options`

用途：返回当前在库可用的筛选项。

参数：
- `enrollment_year`：可选，按某个年级限制高校/导师选项

关键返回字段：
- `grades[]`
- `universities[]`
- `mentors[]`

## 3) 学生详情

### `GET /api/v1/students/{student_id}`

用途：拉取单个学生完整记录。

关键返回字段：
- `id`, `student_no`, `name`
- `home_university`, `major`
- `enrollment_year`, `status`
- `email`, `phone`
- `mentor_name`, `degree_type`
- `expected_graduation_year`
- `added_by`, `created_at`, `updated_at`

## 4) 调用顺序建议

1. 默认先查 `/students`。
2. 用户问“有哪些学校/导师/年级可选”时，优先 `/students/options`。
3. 需要具体学生完整记录时，再补 `/students/{student_id}`。

## 5) 能力边界提示（对外说明）

- 当前学生接口不提供外部 `sourceUrl` 字段。
- 若需要可点击追溯，可使用内部记录链接 `/api/v1/students/{student_id}`，但必须说明这不是外部原始信源。
- 若接口返回 `5xx`、超时或非法请求错误，应明确说明“当前接口暂时不可用”，不要伪造成“未命中”。
