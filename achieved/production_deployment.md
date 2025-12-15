# 生产环境部署指南

## 概述

本文档提供生产环境的完整部署步骤，包括数据库迁移、Docker 部署和验证。

## 部署顺序

**重要**：生产环境必须使用 **Alembic 迁移**，而不是 `init_db.py`（`init_db.py` 会删除现有表，仅用于开发环境）。

## 完整部署步骤

### 阶段 1: 准备工作

#### 1.1 配置环境变量

```bash
# 复制示例配置
cp env.example .env

# 编辑 .env，配置生产环境参数
```

**必需配置**：

```bash
# 应用环境
APP_ENV=production
APP_NAME=Industrial QA Backend

# 数据库配置（Docker Compose 会自动创建）
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_DATABASE=industrial_qa
MYSQL_USER=industrial
MYSQL_PASSWORD=your_strong_password

# Redis 配置（生产环境必须设置密码）
REDIS_PASSWORD=your_strong_redis_password

# LLM 配置（至少配置一个）
LLM_PROVIDER=openai  # 或 dashscope
OPENAI_API_KEY=sk-xxx
# 或
DASHSCOPE_API_KEY=sk-xxx

# JWT 配置（生产环境必须使用强密钥）
JWT_SECRET=your-very-strong-random-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MINUTES=60

# CORS 配置（生产环境应限制来源）
ALLOWED_ORIGINS=["https://yourdomain.com"]

# 其他配置
ENABLE_SEARCH_CACHE=true
SEARCH_CACHE_TTL=3600
RERANK_CACHE_ENABLE=true
RERANK_CACHE_TTL=7200
```

#### 1.2 检查依赖

```bash
# 确保 Docker 和 Docker Compose 已安装
docker --version
docker compose version  # 或 docker-compose --version
```

### 阶段 2: 启动基础服务

#### 2.1 启动 MySQL 和 Redis

```bash
# 仅启动 MySQL 和 Redis（不启动应用）
docker-compose -f docker-compose.prod.yml up -d mysql redis
```

#### 2.2 等待服务就绪

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 等待 MySQL 就绪（最多 60 秒）
for i in {1..30}; do
    docker-compose -f docker-compose.prod.yml exec -T mysql mysqladmin ping -h localhost --silent 2>/dev/null && break
    sleep 2
done

# 等待 Redis 就绪
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli -a "${REDIS_PASSWORD}" ping
```

### 阶段 3: 数据库迁移（重要）

#### 3.1 构建应用镜像（用于运行迁移）

```bash
# 构建应用镜像
docker-compose -f docker-compose.prod.yml build app
```

#### 3.2 执行数据库迁移

**方式 1: 使用 Docker 容器执行迁移（推荐）**

```bash
# 临时启动应用容器执行迁移
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head
```

**方式 2: 在本地执行迁移（如果本地环境配置正确）**

```bash
# 确保本地已安装依赖
uv sync

# 执行迁移
alembic upgrade head
```

#### 3.3 验证迁移结果

```bash
# 检查迁移版本
docker-compose -f docker-compose.prod.yml run --rm app alembic current

# 验证管理员账号（通过 MySQL 客户端）
docker-compose -f docker-compose.prod.yml exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "SELECT email, username, role FROM industrial_qa.users WHERE email='louxuezhi@outlook.com';"
```

**预期结果**：
- 数据库表已创建
- 管理员账号已创建（用户名: LXZ, 邮箱: louxuezhi@outlook.com）

### 阶段 4: 启动应用服务

#### 4.1 启动所有服务

```bash
# 启动所有服务（包括应用）
docker-compose -f docker-compose.prod.yml up -d
```

#### 4.2 检查服务状态

```bash
# 查看所有服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看应用日志
docker-compose -f docker-compose.prod.yml logs -f app
```

#### 4.3 验证服务健康

```bash
# 健康检查（如果配置了端口映射或反向代理）
curl http://localhost:8000/

# 或从容器内部检查
docker-compose -f docker-compose.prod.yml exec app curl http://localhost:8000/
```

### 阶段 5: 配置反向代理（推荐）

生产环境建议使用 Nginx 或 Traefik 作为反向代理。

#### Nginx 配置示例

```nginx
# /etc/nginx/sites-available/industrial-qa
upstream app {
    server localhost:8000;  # 如果应用暴露了端口
    # 或使用 Docker 网络
    # server app:8000;  # 需要 Nginx 也在 Docker 网络中
}

server {
    listen 80;
    server_name yourdomain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 阶段 6: 验证部署

#### 6.1 测试管理员登录

```bash
curl -X POST http://yourdomain.com/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "louxuezhi@outlook.com",
    "password": "271828LXZ"
  }'
```

#### 6.2 测试 API 端点

```bash
# 健康检查
curl http://yourdomain.com/

# API 文档
curl http://yourdomain.com/docs
```

## 部署检查清单

### 部署前检查

- [ ] `.env` 文件已配置所有必需参数
- [ ] 所有密码使用强密码
- [ ] `JWT_SECRET` 已设置为随机强密钥
- [ ] `ALLOWED_ORIGINS` 已限制为实际域名
- [ ] Redis 密码已设置
- [ ] 数据库备份策略已规划

### 部署后检查

- [ ] MySQL 服务正常运行
- [ ] Redis 服务正常运行
- [ ] 应用服务正常运行
- [ ] 数据库迁移已执行（`alembic current`）
- [ ] 管理员账号已创建
- [ ] 健康检查通过
- [ ] API 端点可访问
- [ ] 日志无错误

## 常见问题

### Q1: 数据库迁移失败怎么办？

**A**: 
1. 检查数据库连接配置
2. 确保 MySQL 服务已启动
3. 检查数据库用户权限
4. 查看迁移日志：`docker-compose -f docker-compose.prod.yml logs app`

### Q2: 如何重置数据库？

**A**: 
```bash
# 警告：会删除所有数据！
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d mysql redis
# 等待服务就绪后
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head
```

### Q3: 如何更新应用？

**A**:
```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose -f docker-compose.prod.yml build app

# 3. 执行新的迁移（如果有）
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 4. 重启应用
docker-compose -f docker-compose.prod.yml up -d --no-deps app
```

### Q4: 如何备份数据库？

**A**:
```bash
# 备份 MySQL
docker-compose -f docker-compose.prod.yml exec mysql mysqldump \
    -u root -p${MYSQL_ROOT_PASSWORD} \
    industrial_qa > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份 Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} \
    --rdb /data/dump.rdb
```

## 安全建议

1. **密码安全**
   - 所有密码使用强密码（至少 16 位，包含大小写字母、数字、特殊字符）
   - 定期更换密码
   - 使用密码管理器

2. **网络安全**
   - 使用 HTTPS（SSL/TLS）
   - 配置防火墙，仅开放必要端口
   - 使用反向代理，不直接暴露应用端口

3. **数据安全**
   - 定期备份数据库
   - 加密敏感数据
   - 限制数据库访问权限

4. **监控和日志**
   - 配置日志收集（如 ELK、Loki）
   - 设置监控告警
   - 定期检查日志

## 快速部署脚本

创建 `deploy_prod.sh`：

```bash
#!/bin/bash
set -e

echo "🚀 开始生产环境部署..."

# 1. 启动基础服务
echo "📦 启动 MySQL 和 Redis..."
docker-compose -f docker-compose.prod.yml up -d mysql redis

# 2. 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 15

# 3. 构建应用镜像
echo "🔨 构建应用镜像..."
docker-compose -f docker-compose.prod.yml build app

# 4. 执行数据库迁移
echo "🗄️  执行数据库迁移..."
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 5. 启动应用
echo "🚀 启动应用..."
docker-compose -f docker-compose.prod.yml up -d

# 6. 验证
echo "✅ 验证部署..."
sleep 10
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml exec app curl -f http://localhost:8000/ || echo "⚠️  健康检查失败，请查看日志"

echo "✅ 部署完成！"
```

## 总结

**关键步骤顺序**：

1. ✅ 配置环境变量
2. ✅ 启动 MySQL 和 Redis
3. ✅ **执行数据库迁移（Alembic）** ← 重要！
4. ✅ 启动应用服务
5. ✅ 配置反向代理
6. ✅ 验证部署

**重要提醒**：
- 生产环境**必须使用 Alembic 迁移**，不要使用 `init_db.py`
- Alembic 迁移会自动创建管理员账号
- 执行迁移前确保 MySQL 服务已启动并就绪

