# Alembic 管理员账号迁移

## 概述

已创建 Alembic 迁移脚本 `001_create_admin_user.py`，用于在数据库迁移时自动创建管理员账号。

## 管理员账号信息

- **用户名**: `LXZ`
- **邮箱**: `louxuezhi@outlook.com`
- **密码**: `271828LXZ`
- **角色**: `admin`
- **状态**: `is_active=True`, `is_verified=True`

## 迁移脚本功能

### upgrade() 函数

1. **检查用户是否存在**
   - 通过邮箱或用户名检查
   - 如果用户已存在，更新为管理员角色并重置密码

2. **创建新用户**
   - 如果用户不存在，创建新的管理员账号
   - 自动生成 UUID
   - 使用 bcrypt 哈希密码

### downgrade() 函数

- 删除管理员账号（谨慎使用）
- 通过邮箱或用户名匹配删除

## 使用方法

### 执行迁移

```bash
# 升级到最新版本（创建管理员账号）
alembic upgrade head

# 或升级到指定版本
alembic upgrade 001_create_admin_user
```

### 验证管理员账号

迁移执行后，可以使用以下方式验证：

```bash
# 使用登录 API 测试
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "louxuezhi@outlook.com",
    "password": "271828LXZ"
  }'
```

### 回滚迁移（谨慎）

```bash
# 回滚迁移（会删除管理员账号）
alembic downgrade -1
```

## 注意事项

1. **密码安全**: 密码以 bcrypt 哈希形式存储在数据库中
2. **重复执行**: 如果管理员账号已存在，迁移会更新其角色和密码
3. **生产环境**: 在生产环境执行迁移后，建议立即修改默认密码
4. **数据备份**: 执行迁移前请备份数据库

## 迁移文件位置

- 文件路径: `alembic/versions/001_create_admin_user.py`
- 迁移 ID: `001_create_admin_user`
- 依赖: 无（初始迁移）

## 后续迁移

如果需要修改管理员账号信息，可以：

1. **方式1**: 创建新的迁移脚本修改账号信息
2. **方式2**: 使用 `scripts/create_admin.py` 脚本手动更新
3. **方式3**: 通过 API 或数据库直接修改

## 相关文件

- `alembic/versions/001_create_admin_user.py` - 迁移脚本
- `scripts/create_admin.py` - 手动创建管理员的脚本
- `app/api/v1/auth.py` - 认证相关 API

