# 系统重置指南

## 概述

系统重置会删除所有数据并重新初始化系统，包括：
- MySQL 数据库中的所有数据
- Redis 缓存中的所有数据
- 向量数据库（ChromaDB）中的所有集合
- 上传的文件
- 用户账号、文档库、文档等所有业务数据

**⚠️ 警告：此操作不可恢复！请确保已备份重要数据！**

## 使用场景

系统重置适用于以下场景：
1. **开发/测试环境**：需要清理测试数据，重新开始
2. **系统迁移**：需要清空旧数据，重新部署
3. **数据损坏**：数据库损坏，需要重新初始化
4. **安全重置**：需要完全清除所有数据

## 重置方法

### 方法 1: 使用重置脚本（推荐）

项目提供了自动化重置脚本 `scripts/reset_system.sh`：

```bash
# 执行重置脚本
./scripts/reset_system.sh
```

**脚本功能**：
1. 停止所有服务
2. 删除 MySQL 和 Redis 数据卷
3. 清空向量数据库目录
4. 删除上传的文件
5. 重新启动服务
6. 重新初始化数据库（使用 Alembic 或 init_db.py）
7. 验证系统状态

**注意事项**：
- 脚本会要求输入 `YES` 确认操作
- 自动检测开发/生产环境
- 自动处理数据卷名称差异

### 方法 2: 手动重置（Docker Compose）

#### 开发环境

```bash
# 1. 停止服务并删除数据卷
docker compose down -v

# 2. 删除向量数据库
rm -rf chroma_store/*

# 3. 删除上传的文件
rm -rf data/uploads/*

# 4. 重新启动服务
docker compose up -d mysql redis

# 5. 等待服务就绪
sleep 10

# 6. 初始化数据库
docker compose run --rm app python scripts/init_db.py

# 7. 启动应用
docker compose up -d
```

#### 生产环境

```bash
# 1. 停止服务并删除数据卷
docker compose -f docker-compose.prod.yml down -v

# 2. 删除向量数据库
rm -rf chroma_store/*

# 3. 删除上传的文件
rm -rf data/uploads/*

# 4. 重新启动基础服务
docker compose -f docker-compose.prod.yml up -d mysql redis

# 5. 等待服务就绪
sleep 10

# 6. 执行数据库迁移（会创建管理员账号）
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 7. 启动应用
docker compose -f docker-compose.prod.yml up -d
```

### 方法 3: 仅重置数据库（保留文件）

如果只想重置数据库，保留上传的文件和向量数据：

```bash
# 1. 停止服务
docker compose down

# 2. 删除数据库数据卷
docker volume rm industrialagent_mysql_data
docker volume rm industrialagent_redis_data

# 3. 重新启动服务
docker compose up -d mysql redis

# 4. 等待服务就绪
sleep 10

# 5. 初始化数据库
docker compose run --rm app python scripts/init_db.py

# 6. 启动应用
docker compose up -d
```

### 方法 4: 使用 SQL 命令重置（不删除数据卷）

如果不想删除数据卷，可以直接在数据库中执行 SQL：

```bash
# 1. 进入 MySQL 容器
docker compose exec mysql bash

# 2. 登录 MySQL
mysql -u root -p${MYSQL_ROOT_PASSWORD}

# 3. 删除数据库并重新创建
DROP DATABASE IF EXISTS industrial_qa;
CREATE DATABASE industrial_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 4. 退出 MySQL 和容器
exit
exit

# 5. 重新初始化数据库
docker compose run --rm app python scripts/init_db.py
# 或生产环境
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head
```

## 重置后状态

重置完成后，系统将处于初始状态：

### 数据库状态
- 所有表已创建（空表）
- 如果使用 Alembic（生产环境），会自动创建管理员账号：
  - 邮箱: `louxuezhi@outlook.com`
  - 用户名: `LXZ`
  - 密码: `271828LXZ`

### 其他状态
- Redis 缓存已清空
- 向量数据库已清空
- 上传文件目录已清空
- 所有用户、文档库、文档等数据已删除

## 重置前备份

**强烈建议在重置前备份数据**：

```bash
# 1. 备份数据库
./scripts/backup.sh

# 2. 或手动备份
docker compose exec mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} industrial_qa > backup_before_reset.sql

# 3. 备份上传的文件
tar -czf uploads_backup.tar.gz data/uploads/

# 4. 备份向量数据库
tar -czf chroma_backup.tar.gz chroma_store/
```

## 验证重置

重置完成后，验证系统状态：

```bash
# 1. 检查服务状态
docker compose ps

# 2. 检查数据库表
docker compose exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "SHOW TABLES FROM industrial_qa;"

# 3. 检查管理员账号（生产环境）
docker compose -f docker-compose.prod.yml exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "SELECT email, username, role FROM industrial_qa.users WHERE email='louxuezhi@outlook.com';"

# 4. 检查应用健康
curl http://localhost:8000/

# 5. 测试登录（生产环境）
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"payload": {"email": "louxuezhi@outlook.com", "password": "271828LXZ"}}'
```

## 常见问题

### Q1: 重置后无法登录？

**A**: 检查管理员账号是否已创建：
- 开发环境：需要手动创建管理员账号
- 生产环境：Alembic 迁移会自动创建管理员账号

如果账号不存在，可以手动创建：
```bash
docker compose run --rm app python scripts/create_admin.py
```

### Q2: 数据卷删除失败？

**A**: 确保服务已完全停止：
```bash
# 强制停止并删除
docker compose down -v --remove-orphans
docker volume prune -f
```

### Q3: 重置后服务无法启动？

**A**: 检查日志：
```bash
docker compose logs app
docker compose logs mysql
docker compose logs redis
```

### Q4: 如何只重置特定数据？

**A**: 可以手动操作：
- 只清空 Redis: `docker compose exec redis redis-cli FLUSHALL`
- 只删除向量数据库: `rm -rf chroma_store/*`
- 只删除上传文件: `rm -rf data/uploads/*`
- 只重置数据库: 使用方法 4（SQL 命令）

## 安全建议

1. **生产环境重置前**：
   - 必须备份所有数据
   - 通知所有用户
   - 在维护窗口期间执行

2. **开发环境**：
   - 可以频繁重置用于测试
   - 建议使用重置脚本自动化

3. **数据保护**：
   - 定期备份
   - 使用版本控制管理配置
   - 记录重置操作日志

## 相关文档

- 备份恢复: `scripts/README_BACKUP.md`
- 部署指南: `achieved/production_deployment_guide.md`
- Docker 部署: `achieved/docker_deployment.md`
- Alembic 迁移: `achieved/alembic_setup.md`

