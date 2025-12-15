# Alembic 初始化完成

## 概述

已成功初始化 Alembic 数据库迁移工具，项目现在可以使用版本化的数据库迁移管理。

## 已创建的文件

1. **alembic.ini** - Alembic 主配置文件
2. **alembic/env.py** - 迁移环境配置（自动从 `.env` 读取数据库 URL）
3. **alembic/script.py.mako** - 迁移脚本模板
4. **alembic/versions/** - 迁移脚本目录（存放生成的迁移文件）
5. **alembic/README.md** - Alembic 使用文档
6. **scripts/create_initial_migration.py** - 生成初始迁移的辅助脚本

## 配置说明

### 数据库 URL 转换

Alembic 需要同步数据库连接，但项目使用异步连接。`alembic/env.py` 已配置自动转换：

- `mysql+aiomysql://` → `mysql+pymysql://`
- `sqlite+aiosqlite://` → `sqlite://`

### 模型自动检测

`alembic/env.py` 已配置自动导入所有模型：

```python
from app.db.models import *  # 自动导入所有模型
target_metadata = Base.metadata
```

## 使用步骤

### 1. 生成初始迁移（如果数据库已存在表）

如果数据库已经有表（通过 `init_db.py` 创建），需要先创建初始迁移：

```bash
# 方式1: 使用辅助脚本
python scripts/create_initial_migration.py

# 方式2: 手动生成
alembic revision --autogenerate -m "Initial schema"
```

**注意**：如果数据库已有表，生成的迁移可能包含 `create_table` 语句。你可以：
- 选项 A：删除现有表，然后应用迁移（会丢失数据）
- 选项 B：手动编辑迁移文件，移除已存在的表的创建语句

### 2. 应用迁移

```bash
# 升级到最新版本
alembic upgrade head
```

### 3. 后续变更

当需要修改数据库结构时：

```bash
# 1. 修改模型（app/db/models.py）
# 例如：添加新字段

# 2. 生成迁移
alembic revision --autogenerate -m "add new field"

# 3. 检查生成的迁移文件
# 文件位置：alembic/versions/xxx_add_new_field.py

# 4. 执行迁移
alembic upgrade head
```

## 常用命令

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>
```

## 与 init_db.py 的关系

- **init_db.py**: 用于快速创建数据库表（开发环境，会删除现有表）
- **Alembic**: 用于版本化的数据库迁移（生产环境推荐）

**建议**：
- 开发环境：可以使用 `init_db.py` 快速重置
- 生产环境：必须使用 Alembic，避免数据丢失

## 注意事项

1. **依赖安装**：确保安装了 `pymysql`（MySQL）或 `aiosqlite`（SQLite）的同步版本
   ```bash
   pip install pymysql  # MySQL
   ```

2. **数据库备份**：在生产环境执行迁移前，务必先备份数据库

3. **迁移顺序**：迁移按顺序执行，不要跳过中间版本

4. **回滚限制**：某些迁移（如删除数据）可能无法完全回滚

## 下一步

1. 如果数据库已有表，运行 `python scripts/create_initial_migration.py` 生成初始迁移
2. 检查生成的迁移文件，确认 SQL 语句正确
3. 执行 `alembic upgrade head` 应用迁移
4. 后续数据库变更都使用 Alembic 管理

## 相关文档

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- `alembic/README.md` - 项目内 Alembic 使用说明

