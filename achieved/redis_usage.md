# Redis 使用情况说明

## 测试结果

✅ **Redis 正在被使用！**

测试脚本 `scripts/test_redis_usage.py` 显示：
- ✓ Redis 连接成功（版本 8.4.0）
- ✓ JWT 黑名单功能正常工作
- ✓ 当前 Redis 中有 **12 个黑名单 token**

## Redis 的使用场景

### 1. JWT Token 黑名单（主要用途）

**位置**: `app/core/security.py`

**功能**:
- 用户注销时，将 token 的 `jti` 写入 Redis 黑名单
- 每次验证 token 时，检查是否在黑名单中
- 黑名单键的 TTL 与 token 过期时间一致，自动清理

**键格式**: `jwt:blacklist:{jti}`

**使用流程**:
```python
# 注销时
await revoke_token(redis_client, jti, exp_ts)

# 验证时
key = f"jwt:blacklist:{jti}"
exists = await redis_client.exists(key)
if exists:
    raise HTTPException(401, "Token revoked")
```

**当前状态**: 
- 已有 12 个黑名单 token（说明已经有用户注销操作）
- TTL 范围：303 秒到 6401 秒不等（根据 token 剩余过期时间）

### 2. 邮箱验证 Token（已禁用但代码保留）

**位置**: `app/users/email_verification.py`

**功能**:
- 存储邮箱验证 token
- 验证后删除 token

**键格式**: `email:verify:{token}`

**状态**: 当前功能已禁用（返回 503），但代码保留

## 为什么看不到 Redis 使用日志？

Redis 的使用是**静默的**，不会在 Redis 服务器日志中显示操作详情。Redis 服务器日志只显示：
- 启动信息
- 连接信息
- 警告和错误

要查看 Redis 的使用情况，可以：

### 方法 1: 使用测试脚本
```bash
uv run python scripts/test_redis_usage.py
```

### 方法 2: 使用 Redis CLI 监控
```bash
# 连接到 Redis
redis-cli

# 查看所有键
KEYS *

# 查看 JWT 黑名单键
KEYS jwt:blacklist:*

# 查看某个键的 TTL
TTL jwt:blacklist:{jti}

# 监控实时命令
MONITOR
```

### 方法 3: 查看应用日志
在 FastAPI 应用中添加日志，记录 Redis 操作：
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Checking blacklist for jti: {jti}")
```

## 验证 Redis 是否工作

### 测试步骤

1. **登录获取 token**
   ```bash
   POST /api/v1/login
   {
     "payload": {
       "email": "user@example.com",
       "password": "pwd123"
     }
   }
   ```
   响应中包含 `access_token`

2. **使用 token 访问受保护接口**
   ```bash
   GET /api/v1/docs/libraries
   Authorization: Bearer <access_token>
   ```
   应该成功（token 有效）

3. **注销 token**
   ```bash
   POST /api/v1/logout
   Authorization: Bearer <access_token>
   ```
   此时 token 的 `jti` 被写入 Redis 黑名单

4. **再次使用同一个 token**
   ```bash
   GET /api/v1/docs/libraries
   Authorization: Bearer <same_access_token>
   ```
   应该返回 401 Unauthorized（token 已被注销）

5. **检查 Redis**
   ```bash
   redis-cli
   > KEYS jwt:blacklist:*
   ```
   应该能看到刚才注销的 token

## Redis 配置

**环境变量**: `REDIS_URL`

**格式**: `redis://[password@]host:port/db`

**示例**:
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_URL=redis://:password@localhost:6379/0
REDIS_URL=redis://user:password@localhost:6379/1
```

**默认值**: 空字符串（必须通过环境变量配置）

## 性能考虑

- **连接池**: Redis 客户端使用连接池，避免频繁创建连接
- **异步操作**: 所有 Redis 操作都是异步的，不阻塞请求
- **自动过期**: 黑名单键自动过期，无需手动清理
- **错误处理**: Redis 错误时采用"失败安全"策略（允许通过），避免 Redis 故障影响服务

## 监控建议

### 1. 监控黑名单键数量
```bash
redis-cli --eval - 0 <<EOF
local keys = redis.call('keys', 'jwt:blacklist:*')
return #keys
EOF
```

### 2. 监控 Redis 内存使用
```bash
redis-cli INFO memory
```

### 3. 监控 Redis 命令统计
```bash
redis-cli INFO stats
```

## 总结

✅ Redis **确实在被使用**，主要用于 JWT 黑名单功能

✅ 当前已有 **12 个黑名单 token**，说明注销功能正常工作

✅ Redis 连接正常，功能测试通过

**注意**: Redis 的使用是静默的，不会在服务器日志中显示详细操作。要查看使用情况，请使用测试脚本或 Redis CLI。

