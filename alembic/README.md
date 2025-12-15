# Alembic 数据库迁移

## 概述

本项目使用 Alembic 进行数据库版本控制和迁移管理。

## 初始化状态

✅ Alembic 已初始化并配置完成。

## 初始迁移

✅ 已创建初始迁移脚本 `001_create_admin_user.py`，包含：
- 创建管理员账号（用户名: LXZ, 邮箱: louxuezhi@outlook.com）
- 如果账号已存在，则更新为管理员权限

## 常用命令

### 生成迁移

```bash
# 自动生成迁移（基于模型变更）
alembic revision --autogenerate -m "描述信息"

# 手动创建迁移
alembic revision -m "描述信息"
```

### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

### 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# 回滚到基础版本
alembic downgrade base
```

## 工作流程

### 1. 修改模型

在 `app/db/models.py` 中修改模型定义，例如：

```python
class User(Base):
    # ... 现有字段
    new_field: Mapped[str] = mapped_column(default="")  # 新增字段
```

### 2. 生成迁移

```bash
alembic revision --autogenerate -m "add new_field to users"
```

### 3. 检查迁移文件

检查 `alembic/versions/` 目录下生成的迁移文件，确认 SQL 语句正确。

### 4. 执行迁移

```bash
alembic upgrade head
```

## 配置说明

- **alembic.ini**: Alembic 配置文件
- **alembic/env.py**: 迁移环境配置（已配置为从 `.env` 读取数据库 URL）
- **alembic/versions/**: 迁移脚本目录

## 注意事项

1. **数据库 URL**: 迁移脚本会自动从 `.env` 文件读取 `DATABASE_URL`
2. **模型导入**: 确保所有模型都在 `app/db/models.py` 中导入，以便自动检测变更
3. **生产环境**: 在生产环境执行迁移前，务必先备份数据库
4. **回滚**: 某些迁移可能无法完全回滚（如删除数据），请谨慎操作

## 与 init_db.py 的关系

- `scripts/init_db.py`: 用于首次创建数据库表（开发环境）
- `alembic`: 用于后续的数据库结构变更（生产环境推荐）

建议：
- 开发环境：可以使用 `init_db.py` 快速重置数据库
- 生产环境：必须使用 Alembic 进行迁移，避免数据丢失
