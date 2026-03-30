# 信源查询（2026 实时版）

基址：`http://10.1.132.21:8001`

## 推荐接口

1. 首选：`GET /api/v1/sources/catalog`
- 用于全量检索、分页和分面统计。

2. 分面：`GET /api/v1/sources/facets`
- 用于拿维度/分组/标签候选值。

3. 兼容：`GET /api/v1/sources`
- 返回数组，适合简单列表场景。

## 常用调用

### 1) 全量信源目录 + 分面

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?include_facets=true&page_size=200"
```

### 2) 高校领导信源

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?tag=leadership"
```

### 3) 学者师资信源

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?dimension=scholars"
```

### 4) 只看异常信源

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?health_status=failing"
```

### 5) 看筛选候选值

```bash
curl "http://10.1.132.21:8001/api/v1/sources/facets"
```

## 与 policy/personnel 联动

当用户要“只看某来源政策/人事”时，先用 `sources/catalog` 找 `source_id` 或确认 `source_name`，再调用：

- `/api/v1/intel/policy/feed`
- `/api/v1/intel/personnel/feed`

可用参数：
- `source_id`
- `source_ids`
- `source_name`
- `source_names`

## 推荐调用顺序

1. 用户提到来源但不确定：先 `sources/catalog`。
2. 确认来源后：再调业务接口（policy/personnel/scholars/students）。
3. 结果过大时：按接口分页规则翻页。
