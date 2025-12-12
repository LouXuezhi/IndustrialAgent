# Alembic Migrations

当前仓库尚未初始化 Alembic。为支持用户邮箱验证等新字段，需要初始化迁移并生成首个版本。

## 初始化
```bash
alembic init alembic
```

## 需要包含的模型变更
- `users` 表
  - `username` (nullable, unique)
  - `password_hash` (not null)
  - `full_name` (nullable)
  - `is_active` (bool, default True)
  - `is_verified` (bool, default False)
  - `verification_token` (nullable, index)
  - `verification_token_expires_at` (nullable)
  - `metadata` (JSON, default `{}`)
  - `last_login_at` (nullable)

## 生成迁移
```bash
alembic revision --autogenerate -m "add user verification fields"
```

## 升级
```bash
alembic upgrade head
```



