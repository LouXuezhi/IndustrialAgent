# 搜索缓存实现文档

## 概述

实现了热门查询缓存功能，使用 Redis 缓存搜索结果，显著提升重复查询的响应速度。

## 功能特性

### 1. 缓存策略

- **缓存键设计**：包含查询文本、库ID、限制和用户ID（确保权限隔离）
- **动态 TTL**：根据结果数量和查询长度自动调整缓存时间
- **权限隔离**：每个用户的查询结果独立缓存

### 2. 缓存流程

```
1. 检查缓存
   └─ Redis.get(cache_key)
   
2. 缓存命中
   └─ 直接返回结果（跳过检索）
   └─ 记录缓存命中统计
   
3. 缓存未命中
   └─ 执行混合检索（向量 + BM25）
   └─ 存储到缓存
   └─ 返回结果
   └─ 记录缓存未命中统计
```

### 3. 缓存失效

在以下场景自动清除相关缓存：

- **文档删除**：删除文档时清除该库的搜索缓存
- **批量删除**：批量删除文档时清除所有受影响库的缓存
- **文档向量化**：向量化完成后清除该库的缓存（内容可能变化）
- **库删除**：删除库时清除该库的所有缓存

## 实现细节

### 核心模块

#### `app/core/cache.py`

提供缓存相关的工具函数：

- `generate_search_cache_key()`: 生成缓存键
- `get_cached_search_result()`: 从缓存获取结果
- `cache_search_result()`: 缓存搜索结果
- `invalidate_search_cache()`: 清除缓存
- `record_cache_stats()`: 记录缓存统计
- `get_cache_hit_rate()`: 获取缓存命中率
- `calculate_cache_ttl()`: 动态计算 TTL

### 配置选项

在 `app/core/config.py` 中添加：

```python
enable_search_cache: bool = Field(default=True, description="是否启用搜索缓存")
search_cache_ttl: int = Field(default=3600, description="搜索缓存过期时间（秒），默认1小时")
```

在 `.env` 文件中配置：

```bash
ENABLE_SEARCH_CACHE=true
SEARCH_CACHE_TTL=3600
```

### API 集成

#### `search_documents` 端点

在 `app/api/v1/docs.py` 的 `search_documents` 函数中：

1. **缓存检查**：查询前先检查缓存
2. **缓存写入**：查询后写入缓存
3. **统计记录**：记录命中/未命中

#### 缓存失效集成

在以下函数中添加了缓存清除逻辑：

- `delete_document()`: 删除单个文档
- `batch_delete_documents()`: 批量删除文档
- `delete_library()`: 删除库
- `vectorize_document()`: 向量化文档

## 缓存键格式

```
search:doc:{md5_hash}

其中 md5_hash 基于：
- 查询文本
- 库ID（可选）
- 结果数量限制
- 用户ID（权限隔离）
```

## TTL 策略

动态 TTL 计算：

- **基础 TTL**：1小时（3600秒）
- **热门查询**：结果数量 > 10 时，TTL = 2小时
- **短查询**：查询长度 < 10 时，TTL = 1.5小时
- **上限**：不超过配置的 `SEARCH_CACHE_TTL`

## 缓存统计

使用 Redis Hash 存储统计信息：

```
键: cache:stats:search
字段:
  - hits: 命中次数
  - misses: 未命中次数
```

可通过 `get_cache_hit_rate()` 获取命中率。

## 性能优化

### 1. 使用 SCAN 而非 KEYS

清除缓存时使用 `SCAN` 命令而非 `KEYS`，避免阻塞 Redis：

```python
cursor = 0
while True:
    cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
    if keys:
        await redis_client.delete(*keys)
    if cursor == 0:
        break
```

### 2. 错误处理

- 缓存读取/写入失败不影响主流程
- 使用 `logger.warning` 记录错误，不抛出异常

### 3. 权限隔离

缓存键包含用户ID，确保：
- 不同用户看到不同的缓存结果
- 权限变更后不会返回错误的缓存

## 使用示例

### 启用缓存

在 `.env` 中配置：

```bash
REDIS_URL=redis://localhost:6379/0
ENABLE_SEARCH_CACHE=true
SEARCH_CACHE_TTL=3600
```

### 查看缓存统计

```python
from app.deps import get_redis
from app.core.cache import get_cache_hit_rate

redis_client = get_redis()
hit_rate = await get_cache_hit_rate(redis_client)
print(f"缓存命中率: {hit_rate * 100:.2f}%")
```

### 手动清除缓存

```python
from app.deps import get_redis
from app.core.cache import invalidate_search_cache

redis_client = get_redis()
# 清除特定库的缓存
await invalidate_search_cache(redis_client, library_id="library-uuid")
# 清除所有搜索缓存
await invalidate_search_cache(redis_client)
```

## 注意事项

1. **Redis 依赖**：需要配置 `REDIS_URL`，否则缓存功能自动禁用
2. **内存管理**：合理设置 TTL，避免缓存占用过多内存
3. **数据一致性**：文档更新后会自动清除相关缓存，但可能存在短暂的不一致
4. **权限隔离**：缓存键包含用户ID，确保权限安全

## 未来优化

1. **缓存预热**：预加载热门查询
2. **分层缓存**：L1（内存）+ L2（Redis）
3. **缓存压缩**：对大型结果集进行压缩
4. **智能失效**：基于文档变更时间戳的增量失效
5. **缓存监控**：提供缓存使用情况的监控面板

