# Docker 部署指南

## 概述

本项目提供了完整的 Docker 容器化部署方案，包括开发环境和生产环境的配置。

## 文件说明

- `Dockerfile`: 开发环境 Dockerfile
- `Dockerfile.prod`: 生产环境 Dockerfile（优化版，使用非 root 用户）
- `docker-compose.yml`: 开发环境 Docker Compose 配置
- `docker-compose.prod.yml`: 生产环境 Docker Compose 配置
- `.dockerignore`: Docker 构建忽略文件
- `deploy.sh`: 自动化部署脚本

## 快速开始

### 1. 配置环境变量

```bash
# 复制示例配置
cp env.example .env

# 编辑 .env，至少配置以下内容：
# - MYSQL_ROOT_PASSWORD（MySQL root 密码）
# - MYSQL_PASSWORD（MySQL 用户密码）
# - OPENAI_API_KEY 或 DASHSCOPE_API_KEY（LLM API 密钥）
# - JWT_SECRET（JWT 密钥，生产环境必须使用强密码）
```

### 2. 开发环境部署

```bash
# 方式1: 使用部署脚本（推荐）
./deploy.sh

# 方式2: 手动部署
docker-compose up -d
docker-compose exec app python scripts/init_db.py
```

### 3. 生产环境部署

```bash
# 使用部署脚本
./deploy.sh prod

# 或手动部署
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec app python scripts/init_db.py
```

## 服务说明

### 开发环境（docker-compose.yml）

- **MySQL**: 端口 3306（暴露）
- **Redis**: 端口 6379（暴露）
- **FastAPI App**: 端口 8000（暴露）

### 生产环境（docker-compose.prod.yml）

- **MySQL**: 仅内部访问（不暴露端口）
- **Redis**: 仅内部访问，启用密码认证（不暴露端口）
- **FastAPI App**: 仅内部访问（建议使用 Nginx/Traefik 反向代理）

## 常用命令

### 查看服务状态

```bash
# 开发环境
docker-compose ps

# 生产环境
docker-compose -f docker-compose.prod.yml ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app
docker-compose logs -f mysql
docker-compose logs -f redis
```

### 进入容器

```bash
# 进入应用容器
docker-compose exec app bash

# 进入 MySQL 容器
docker-compose exec mysql bash

# 进入 Redis 容器
docker-compose exec redis sh
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart app
```

### 停止和删除

```bash
# 停止服务（保留数据卷）
docker-compose down

# 停止并删除所有（包括数据卷）
docker-compose down -v
```

### 重新构建

```bash
# 重新构建镜像
docker-compose build --no-cache

# 重新构建并启动
docker-compose up -d --build
```

## 数据持久化

### 数据卷

- `mysql_data`: MySQL 数据存储
- `redis_data`: Redis 数据存储
- `./data/uploads`: 上传的文件
- `./chroma_store`: 向量数据库存储

### 备份数据

```bash
# 备份 MySQL
docker-compose exec mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} industrial_qa > backup.sql

# 备份 Redis
docker-compose exec redis redis-cli --rdb /data/dump.rdb
```

### 恢复数据

```bash
# 恢复 MySQL
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} industrial_qa < backup.sql
```

## 数据库迁移

```bash
# 执行数据库迁移
docker-compose exec app alembic upgrade head

# 创建新迁移
docker-compose exec app alembic revision --autogenerate -m "description"
```

## 健康检查

所有服务都配置了健康检查：

```bash
# 查看健康状态
docker-compose ps

# 手动检查应用健康
curl http://localhost:8000/
```

## 性能优化

### 生产环境建议

1. **Worker 数量**: 根据服务器 CPU 核心数调整
   ```dockerfile
   CMD ["gunicorn", "app.main:app", "--workers", "8", ...]
   ```

2. **使用反向代理**: 推荐使用 Nginx 或 Traefik
   ```nginx
   # Nginx 配置示例
   upstream app {
       server app:8000;
   }
   
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **资源限制**: 在 docker-compose.prod.yml 中添加
   ```yaml
   app:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 4G
   ```

## 安全建议

### 生产环境必须配置

1. **强密码**: 所有密码必须使用强密码
2. **JWT_SECRET**: 使用随机生成的强密钥
3. **Redis 密码**: 启用 Redis 密码认证
4. **CORS**: 限制允许的来源
5. **防火墙**: 仅暴露必要的端口
6. **SSL/TLS**: 使用 HTTPS（通过反向代理）

### 环境变量安全

```bash
# 使用 secrets 管理敏感信息（Docker Swarm）
docker secret create jwt_secret ./jwt_secret.txt

# 或使用环境变量文件（不提交到 Git）
echo "JWT_SECRET=your-secret" > .env.prod
```

## 监控和日志

### 查看实时日志

```bash
# 所有服务
docker-compose logs -f

# 仅应用日志
docker-compose logs -f app | grep -i error
```

### 资源使用情况

```bash
# 查看容器资源使用
docker stats

# 查看特定容器
docker stats industrial-qa-app
```

## 故障排查

### 服务无法启动

1. 检查日志: `docker-compose logs app`
2. 检查环境变量: `docker-compose exec app env`
3. 检查数据库连接: `docker-compose exec app python -c "from app.core.config import settings; print(settings.database_url)"`

### 数据库连接失败

1. 检查 MySQL 是否运行: `docker-compose ps mysql`
2. 检查网络连接: `docker-compose exec app ping mysql`
3. 检查数据库配置: 确认 `DATABASE_URL` 正确

### Redis 连接失败

1. 检查 Redis 是否运行: `docker-compose ps redis`
2. 测试连接: `docker-compose exec redis redis-cli ping`
3. 检查配置: 确认 `REDIS_URL` 正确

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 停止旧服务
docker-compose down

# 4. 启动新服务
docker-compose up -d

# 5. 执行数据库迁移（如有）
docker-compose exec app alembic upgrade head
```

## 多环境部署

### 使用不同的 Compose 文件

```bash
# 开发环境
docker-compose -f docker-compose.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 测试环境
docker-compose -f docker-compose.test.yml up -d
```

## 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn 文档](https://docs.gunicorn.org/)

