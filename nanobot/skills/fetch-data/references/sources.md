# 信源查询与控制（代码对齐）

后端地址：`http://10.1.132.21:8001`
后端项目：`/home/ubuntu/workspace/DeanAgent-Backend`

## 首选接口

- `GET /api/v1/sources/catalog`：目录检索（分页 + 分面）
- `GET /api/v1/sources/facets`：分面候选值
- `GET /api/v1/sources`：兼容列表（数组）

## 常见场景

### 全量目录 + 分面

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?include_facets=true&page_size=200"
```

### 高校领导相关信源

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?tag=leadership"
```

### 学者信源

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?dimension=scholars"
```

### 异常信源

```bash
curl "http://10.1.132.21:8001/api/v1/sources/catalog?health_status=failing"
```

### 某信源日志

```bash
curl "http://10.1.132.21:8001/api/v1/sources/<source_id>/logs?limit=20"
```

## 与业务接口联动

当用户要“只看某来源政策/人事/前沿信号”时，先用 `sources/catalog` 确定 `source_id`，再带入：

- `/api/v1/intel/policy/feed`
- `/api/v1/intel/personnel/feed`
- `/api/v1/intel/personnel/enriched-feed`
- `/api/v1/intel/tech-frontier/signals`

可用来源参数：
- `source_id`
- `source_ids`
- `source_name`
- `source_names`
