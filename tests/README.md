# 测试文档

本文档说明如何运行 Industrial QA Backend 的测试套件。

## 目录结构

```
tests/
├── README.md                 # 本文档
├── init_test_data.py        # 测试数据初始化脚本
├── test_api_endpoints.py    # API端点功能测试脚本
├── test_response.py         # 响应格式测试
└── test_smoke.py            # 冒烟测试
```

## 前置条件

1. **数据库已初始化**
   ```bash
   python scripts/init_db.py
   ```

2. **Redis 服务运行中**
   ```bash
   # macOS
   brew services start redis
   # 或
   redis-server
   
   # Linux
   sudo systemctl start redis-server
   ```

3. **依赖已安装**
   ```bash
   uv sync
   ```

4. **环境变量配置**
   - 确保 `.env` 文件已配置正确的数据库和Redis连接

## 测试步骤

### 1. 初始化测试数据

首先运行测试数据初始化脚本，创建测试用户、群组、库和文档：

```bash
python tests/init_test_data.py
# 或
uv run python tests/init_test_data.py
```

**创建的测试数据：**

#### 测试用户

| 邮箱 | 用户名 | 密码 | 角色 |
|------|--------|------|------|
| operator@test.com | operator | test123456 | operator |
| maintenance@test.com | maintenance | test123456 | maintenance |
| manager@test.com | manager | test123456 | manager |
| admin@test.com | admin | test123456 | admin |

#### 测试群组

1. **Production Team**
   - Owner: operator@test.com
   - Admin: maintenance@test.com
   - Member: manager@test.com

2. **Maintenance Team**
   - Owner: maintenance@test.com
   - Admin: operator@test.com
   - Member: manager@test.com

#### 测试库

- 每个用户都有一个个人库
- 每个群组都有一个共享库

#### 测试文档

- 在 operator 的个人库中创建了3个测试文档
- 每个文档包含多个分块（chunks）

### 2. 启动服务器

在另一个终端启动 FastAPI 服务器：

```bash
uvicorn app.main:app --reload
```

服务器应该运行在 `http://localhost:8000`

### 3. 运行API端点测试

运行完整的功能测试：

```bash
python tests/test_api_endpoints.py
# 或
uv run python tests/test_api_endpoints.py
```

## 测试覆盖范围

### 1. 认证测试 (`test_authentication`)

- ✅ 用户登录（所有用户类型）
- ✅ Token 刷新
- ✅ 用户登出

### 2. 库管理测试 (`test_library_management`)

- ✅ 创建库
- ✅ 列出库
- ✅ 获取库详情
- ✅ 更新库
- ✅ 获取库统计信息

### 3. 文档管理测试 (`test_document_management`)

- ✅ 上传文档
- ✅ 列出文档
- ✅ 获取文档详情
- ✅ 搜索文档
- ✅ 预览文档
- ✅ 下载文档

### 4. 权限测试 (`test_permissions`)

- ✅ 用户库访问权限
- ✅ 群组库访问权限
- ✅ 跨用户访问限制

## 测试用户类型说明

### Operator（操作员）
- 默认角色
- 可以创建和管理自己的库
- 可以访问所属群组的库（根据角色）

### Maintenance（维护工程师）
- 维护相关角色
- 可以创建和管理自己的库
- 可以访问所属群组的库

### Manager（经理）
- 管理角色
- 可以创建和管理自己的库
- 可以访问所属群组的库（成员权限）

### Admin（管理员）
- 系统管理员角色
- 可以创建和管理自己的库
- 可以访问所属群组的库

## 群组角色说明

### Owner（所有者）
- 可以创建群组库
- 可以管理群组库（更新、删除）
- 可以添加/移除成员

### Admin（管理员）
- 可以创建群组库
- 可以管理群组库（更新、删除）
- 可以添加/移除成员

### Member（成员）
- 可以查看群组库
- 可以上传文档到群组库
- 不能删除群组库

## 测试数据清理

测试脚本会在最后自动清理创建的测试数据：
- 删除测试文档
- 删除测试库

**注意：** 基础测试数据（用户、群组）不会被删除，可以重复使用。

## 手动测试

### 使用 curl

#### 1. 登录获取Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "operator@test.com",
    "password": "test123456"
  }'
```

#### 2. 使用Token访问API

```bash
TOKEN="your_token_here"

# 列出库
curl -X GET "http://localhost:8000/api/v1/docs/libraries?owner_type=user" \
  -H "Authorization: Bearer $TOKEN"

# 搜索文档
curl -X POST "http://localhost:8000/api/v1/docs/documents/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "设备维护",
    "limit": 10
  }'
```

### 使用 Python requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 登录
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "operator@test.com", "password": "test123456"}
)
token = response.json()["data"]["access_token"]

# 使用Token
headers = {"Authorization": f"Bearer {token}"}

# 列出库
response = requests.get(f"{BASE_URL}/docs/libraries?owner_type=user", headers=headers)
libraries = response.json()["data"]
print(f"Found {len(libraries)} libraries")
```

## 故障排除

### 1. 数据库连接错误

**错误：** `Could not connect to database`

**解决：**
- 检查 `.env` 文件中的 `DATABASE_URL`
- 确保 MySQL 服务正在运行
- 验证数据库用户权限

### 2. Redis 连接错误

**错误：** `Redis connection failed`

**解决：**
- 检查 `.env` 文件中的 `REDIS_URL`
- 确保 Redis 服务正在运行
- 验证 Redis 配置

### 3. 测试数据已存在

**错误：** `User already exists`

**解决：**
- 这是正常的，脚本会跳过已存在的数据
- 如果想重新创建，可以手动删除测试数据

### 4. 服务器未启动

**错误：** `Cannot connect to server`

**解决：**
- 确保服务器正在运行：`uvicorn app.main:app --reload`
- 检查端口是否被占用
- 验证 `BASE_URL` 配置

## 持续集成

这些测试脚本可以集成到 CI/CD 流程中：

```yaml
# GitHub Actions 示例
- name: Initialize test data
  run: python tests/init_test_data.py

- name: Start server
  run: uvicorn app.main:app &
  
- name: Run API tests
  run: python tests/test_api_endpoints.py
```

## 扩展测试

### 添加新的测试用例

1. 在 `test_api_endpoints.py` 中添加新的测试函数
2. 在 `main()` 函数中调用新测试
3. 更新本文档的测试覆盖范围

### 性能测试

可以扩展测试脚本以包含性能测试：

```python
import time

async def test_performance(client):
    start = time.time()
    # ... perform operations ...
    elapsed = time.time() - start
    assert elapsed < 1.0, "Operation too slow"
```

## 联系与支持

如有问题或建议，请查看项目文档或提交 Issue。

