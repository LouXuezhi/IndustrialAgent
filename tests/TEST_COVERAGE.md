# 测试覆盖范围详细说明

本文档详细说明测试脚本覆盖的所有功能和端点。

## 功能覆盖矩阵

### 认证模块 (`/api/v1/auth`)

| 端点 | 方法 | 测试状态 | 说明 |
|------|------|----------|------|
| `/auth/login` | POST | ✅ | 测试所有用户类型登录 |
| `/auth/refresh` | POST | ✅ | 测试Token刷新 |
| `/auth/logout` | POST | ✅ | 测试登出和Token黑名单 |
| `/auth/register` | POST | ⚠️ | 未测试（需要邮箱验证） |
| `/auth/verify-email` | POST | ⚠️ | 未测试（已停用） |

### 库管理模块 (`/api/v1/docs/libraries`)

| 端点 | 方法 | 测试状态 | 说明 |
|------|------|----------|------|
| `POST /docs/libraries` | POST | ✅ | 创建用户库 |
| `GET /docs/libraries` | GET | ✅ | 列出库（用户/群组） |
| `GET /docs/libraries/{id}` | GET | ✅ | 获取库详情 |
| `PUT /docs/libraries/{id}` | PUT | ✅ | 更新库信息 |
| `DELETE /docs/libraries/{id}` | DELETE | ✅ | 删除库 |
| `GET /docs/libraries/{id}/stats` | GET | ✅ | 获取库统计信息 |

### 文档管理模块 (`/api/v1/docs`)

| 端点 | 方法 | 测试状态 | 说明 |
|------|------|----------|------|
| `POST /docs/ingest` | POST | ✅ | 上传并摄取文档 |
| `GET /docs/libraries/{id}/documents` | GET | ✅ | 列出库中的文档 |
| `GET /docs/documents/{id}` | GET | ✅ | 获取文档详情 |
| `DELETE /docs/documents/{id}` | DELETE | ✅ | 删除文档 |
| `POST /docs/documents/search` | POST | ✅ | 搜索文档 |
| `GET /docs/documents/{id}/preview` | GET | ✅ | 预览文档内容 |
| `GET /docs/documents/{id}/download` | GET | ⚠️ | 测试（文件可能不存在） |
| `POST /docs/documents/batch-download` | POST | ⚠️ | 未测试 |
| `POST /docs/documents/batch-delete` | POST | ⚠️ | 未测试 |
| `POST /docs/reindex` | POST | ⚠️ | 未测试（占位实现） |

### 问答模块 (`/api/v1/qa`)

| 端点 | 方法 | 测试状态 | 说明 |
|------|------|----------|------|
| `POST /qa/ask` | POST | ⚠️ | 未测试（需要向量库数据） |

## 用户类型测试覆盖

### Operator（操作员）
- ✅ 登录认证
- ✅ 创建个人库
- ✅ 管理个人库
- ✅ 上传文档
- ✅ 访问群组库（根据角色）

### Maintenance（维护工程师）
- ✅ 登录认证
- ✅ 创建个人库
- ✅ 管理个人库
- ✅ 访问群组库（根据角色）

### Manager（经理）
- ✅ 登录认证
- ✅ 创建个人库
- ✅ 管理个人库
- ✅ 访问群组库（成员权限）

### Admin（管理员）
- ✅ 登录认证
- ✅ 创建个人库
- ✅ 管理个人库

## 群组权限测试覆盖

### Production Team
- ✅ Owner (operator) 可以创建库
- ✅ Admin (maintenance) 可以创建库
- ✅ Member (manager) 可以访问库

### Maintenance Team
- ✅ Owner (maintenance) 可以创建库
- ✅ Admin (operator) 可以创建库
- ✅ Member (manager) 可以访问库

## 权限边界测试

### 已测试
- ✅ 用户无法访问其他用户的个人库
- ✅ 群组成员可以访问群组库（根据角色）
- ✅ 非群组成员无法访问群组库

### 未测试
- ⚠️ 群组库的写权限（owner/admin vs member）
- ⚠️ 批量操作的权限检查
- ⚠️ Token黑名单的实际效果

## 文件类型支持测试

### 已测试
- ✅ TXT 文件上传和解析

### 未测试
- ⚠️ PDF 文件解析
- ⚠️ DOCX 文件解析
- ⚠️ Markdown 文件解析

## 数据完整性测试

### 已测试
- ✅ 文档和分块的创建
- ✅ 库统计信息准确性

### 未测试
- ⚠️ 向量库数据同步
- ⚠️ 级联删除（文档删除时删除分块）
- ⚠️ 库删除时清理向量集合

## 性能测试

### 未测试
- ⚠️ 响应时间
- ⚠️ 并发请求
- ⚠️ 大量数据查询
- ⚠️ 文件上传大小限制

## 错误处理测试

### 已测试
- ✅ 404 错误（资源不存在）
- ✅ 403 错误（权限不足）
- ✅ 400 错误（无效请求）

### 未测试
- ⚠️ 500 错误（服务器错误）
- ⚠️ 网络超时
- ⚠️ 数据库连接失败
- ⚠️ Redis 连接失败

## 边界条件测试

### 已测试
- ✅ 空库列表
- ✅ 单个文档

### 未测试
- ⚠️ 大量文档（>1000）
- ⚠️ 大文件上传（>100MB）
- ⚠️ 特殊字符处理
- ⚠️ 超长文本搜索

## 建议的测试扩展

### 高优先级
1. **批量操作测试**
   - 批量删除文档
   - 批量下载文档

2. **文件类型测试**
   - PDF 上传和解析
   - DOCX 上传和解析

3. **问答功能测试**
   - RAG 管道测试
   - 向量检索测试

### 中优先级
1. **性能测试**
   - 响应时间基准
   - 并发请求处理

2. **错误处理**
   - 各种错误场景
   - 异常恢复

### 低优先级
1. **集成测试**
   - 端到端工作流
   - 多用户协作场景

2. **压力测试**
   - 大量数据
   - 高并发

## 测试数据统计

### 创建的数据
- **用户**: 4个（operator, maintenance, manager, admin）
- **群组**: 2个（Production Team, Maintenance Team）
- **群组成员**: 6个（每个群组3个成员）
- **库**: 6个（4个用户库 + 2个群组库）
- **文档**: 3个（在operator的个人库中）
- **分块**: ~15个（每个文档约5个分块）

### 测试执行时间
- 数据初始化: ~2-5秒
- API测试: ~10-20秒
- 总计: ~15-25秒

## 持续改进

测试覆盖范围会随着新功能的添加而扩展。建议：

1. 每次添加新功能时，同步添加测试用例
2. 定期审查测试覆盖范围
3. 使用代码覆盖率工具（如 coverage.py）
4. 集成到 CI/CD 流程

