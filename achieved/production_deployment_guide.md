# 生产环境服务器部署详细指南

## 目录

1. [服务器环境准备](#1-服务器环境准备)
2. [代码部署](#2-代码部署)
3. [环境配置](#3-环境配置)
4. [数据库迁移](#4-数据库迁移)
5. [服务启动](#5-服务启动)
6. [反向代理配置](#6-反向代理配置)
7. [验证和测试](#7-验证和测试)
8. [监控和维护](#8-监控和维护)
9. [故障排查](#9-故障排查)

---

## 1. 服务器环境准备

### 1.1 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **CPU**: 至少 2 核（推荐 4 核+）
- **内存**: 至少 4GB（推荐 8GB+）
- **磁盘**: 至少 20GB 可用空间（推荐 50GB+）
- **网络**: 可访问互联网（用于下载依赖和模型）

### 1.2 安装 Docker 和 Docker Compose

#### Ubuntu/Debian

```bash
# 更新系统包
sudo apt-get update
sudo apt-get upgrade -y

# 安装必要的工具
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

#### CentOS/RHEL

```bash
# 安装必要的工具
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 1.3 配置 Docker（可选但推荐）

```bash
# 将当前用户添加到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使更改生效
newgrp docker

# 配置 Docker 镜像加速（国内用户推荐）
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

# 重启 Docker
sudo systemctl restart docker
```

### 1.4 安装 Nginx（用于反向代理）

```bash
# Ubuntu/Debian
sudo apt-get install -y nginx

# CentOS/RHEL
sudo yum install -y nginx

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 1.5 配置防火墙

```bash
# Ubuntu (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```
# Ubuntu (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# 直接使用 iptables（适用于所有 Linux 发行版）
# 允许 SSH (22)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 允许 HTTP (80)
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# 允许 HTTPS (443)
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许已建立的连接和本地回环
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT

# 设置默认策略（拒绝所有其他入站连接）
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# 保存 iptables 规则（根据发行版选择）
# Ubuntu/Debian
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

# CentOS/RHEL 7+
sudo yum install -y iptables-services
sudo systemctl enable iptables
sudo service iptables save

# 或者手动保存（通用方法）
sudo iptables-save > /etc/iptables/rules.v4  # IPv4
sudo iptables-save > /etc/iptables/rules.v6   # IPv6（如果使用）
---

## 2. 代码部署

### 2.1 创建应用目录

```bash
# 创建应用目录
sudo mkdir -p /opt/industrial-qa
sudo chown $USER:$USER /opt/industrial-qa
cd /opt/industrial-qa
```

### 2.2 克隆代码仓库

```bash
# 方式1: 从 Git 仓库克隆
git clone <your-repository-url> .

# 方式2: 从本地传输文件
# 在本地机器执行：
# scp -r /path/to/IndustrialAgent/* user@server:/opt/industrial-qa/

# 方式3: 使用 rsync（推荐，支持断点续传）
# 在本地机器执行：
# rsync -avz --progress /path/to/IndustrialAgent/ user@server:/opt/industrial-qa/
```

### 2.3 验证文件结构

```bash
cd /opt/industrial-qa

# 检查关键文件是否存在
ls -la docker-compose.prod.yml
ls -la Dockerfile.prod
ls -la deploy_prod.sh
ls -la env.example
ls -la alembic.ini
ls -la alembic/
```

---

## 3. 环境配置

### 3.1 创建环境变量文件

```bash
cd /opt/industrial-qa

# 复制示例配置文件
cp env.example .env

# 编辑配置文件
nano .env
# 或使用 vim
# vim .env
```

### 3.2 配置环境变量

编辑 `.env` 文件，至少配置以下内容：

```bash
# ============================================
# 应用基础配置
# ============================================
APP_ENV=production
APP_NAME=Industrial QA Backend

# ============================================
# 数据库配置（MySQL）
# ============================================
# 注意：这些变量会被 docker-compose.prod.yml 使用
MYSQL_ROOT_PASSWORD=your_strong_root_password_here
MYSQL_DATABASE=industrial_qa
MYSQL_USER=industrial
MYSQL_PASSWORD=your_strong_user_password_here

# DATABASE_URL 会在 docker-compose.prod.yml 中自动构建
# 格式: mysql+aiomysql://user:password@mysql:3306/database

# ============================================
# Redis 配置
# ============================================
REDIS_PASSWORD=your_strong_redis_password_here
# REDIS_URL 会在 docker-compose.prod.yml 中自动构建

# ============================================
# JWT 安全配置（生产环境必须使用强密钥）
# ============================================
# 生成强密钥（在服务器上执行）:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your_generated_jwt_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MINUTES=60

# ============================================
# LLM 配置（选择一种）
# ============================================

# 选项1: 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4o-mini

# 选项2: 使用 DashScope/Qwen（阿里云）
# LLM_PROVIDER=dashscope
# DASHSCOPE_API_KEY=your-dashscope-api-key
# DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# LLM_MODEL=qwen-plus

# ============================================
# Embedding 配置
# ============================================
EMBEDDING_MODEL=bge-large

# ============================================
# 重排序配置
# ============================================
RERANKER_MODEL=BAAI/bge-reranker-base
ENABLE_RERANK=true
RERANK_CANDIDATE_COUNT=0
RERANK_CACHE_ENABLE=true
RERANK_CACHE_TTL=7200

# ============================================
# Hugging Face 配置（国内用户推荐配置镜像）
# ============================================
HF_ENDPOINT=https://hf-mirror.com
TOKENIZERS_PARALLELISM=false

# ============================================
# 查询扩展配置
# ============================================
ENABLE_QUERY_EXPANSION=true
USE_LLM_EXPANSION=false
# SYNONYM_DICT_PATH=/path/to/synonym_dict.json  # 可选

# ============================================
# 缓存配置
# ============================================
ENABLE_SEARCH_CACHE=true
SEARCH_CACHE_TTL=3600

# ============================================
# CORS 配置（生产环境应限制来源）
# ============================================
# 示例: ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
ALLOWED_ORIGINS=["https://yourdomain.com"]

# ============================================
# 存储配置
# ============================================
STORAGE_DIR=/app/data/uploads
VECTOR_DB_URI=chroma://./chroma_store
```

### 3.3 设置文件权限

```bash
# 确保 .env 文件权限安全（仅所有者可读）
chmod 600 .env

# 确保部署脚本可执行
chmod +x deploy_prod.sh
```

### 3.4 创建数据目录

```bash
# 创建数据存储目录
mkdir -p data/uploads
mkdir -p chroma_store

# 设置适当的权限
chmod -R 755 data/uploads chroma_store
```

---

## 4. 数据库迁移

### 4.1 启动基础服务

```bash
cd /opt/industrial-qa

# 使用部署脚本（推荐）
./deploy_prod.sh

# 或手动执行：
# docker compose -f docker-compose.prod.yml up -d mysql redis
```

### 4.2 等待服务就绪

```bash
# 检查 MySQL 是否就绪
docker compose -f docker-compose.prod.yml exec mysql mysqladmin ping -h localhost --silent

# 检查 Redis 是否就绪
docker compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping
```

### 4.3 执行数据库迁移

```bash
cd /opt/industrial-qa

# 方式1: 使用部署脚本（会自动执行迁移）
./deploy_prod.sh

# 方式2: 手动执行迁移
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head
```

### 4.4 验证管理员账号

```bash
# 检查管理员账号是否创建成功
docker compose -f docker-compose.prod.yml exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "SELECT email, username, role FROM ${MYSQL_DATABASE}.users WHERE email='admin@louxuezhi.com';"
```

**默认管理员账号信息**:
- 邮箱: `admin@louxuezhi.com`
- 用户名: `LXZ`
- 密码: `271828LXZ`

**⚠️ 重要**: 首次登录后请立即修改密码！

---

## 5. 服务启动

### 5.1 构建应用镜像

```bash
cd /opt/industrial-qa

# 构建生产环境镜像
docker compose -f docker-compose.prod.yml build app

# 如果构建失败，可以查看详细日志
docker compose -f docker-compose.prod.yml build --progress=plain app
```

### 5.2 启动所有服务

```bash
# 使用部署脚本（推荐，会自动处理所有步骤）
./deploy_prod.sh

# 或手动启动
docker compose -f docker-compose.prod.yml up -d
```

### 5.3 检查服务状态

```bash
# 查看所有服务状态
docker compose -f docker-compose.prod.yml ps

# 查看服务日志
docker compose -f docker-compose.prod.yml logs -f app

# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f
```

### 5.4 验证服务健康

```bash
# 检查应用健康状态
docker compose -f docker-compose.prod.yml exec app curl -f http://localhost:8000/

# 或从外部检查（如果暴露了端口）
curl http://localhost:8000/
```

---

## 5.5 部署备份脚本（重要）

备份脚本应该在服务启动后立即部署，确保数据安全。

### 5.5.1 创建备份目录

```bash
# 创建备份目录
sudo mkdir -p /opt/backups
sudo chown $USER:$USER /opt/backups
```

### 5.5.2 复制备份脚本

```bash
cd /opt/industrial-qa

# 复制所有备份相关脚本
cp scripts/backup.sh /opt/backups/backup.sh
cp scripts/restore_backup.sh /opt/backups/restore_backup.sh
cp scripts/check_backup.sh /opt/backups/check_backup.sh
cp scripts/cleanup_backups.sh /opt/backups/cleanup_backups.sh

# 设置执行权限
chmod +x /opt/backups/*.sh
```

### 5.5.3 配置备份脚本

```bash
# 编辑备份脚本，配置保留策略
nano /opt/backups/backup.sh

# 主要配置项：
# RETENTION_DAYS=7      # 保留天数（基于时间）
# RETENTION_COUNT=0     # 保留数量（0表示不限制，基于数量）
```

### 5.5.4 测试备份脚本

```bash
# 手动执行一次备份，验证功能
/opt/backups/backup.sh

# 查看备份日志
tail -f /opt/backups/backup.log

# 检查备份文件
ls -lh /opt/backups/
```

### 5.5.5 配置定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点执行备份）
0 2 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1

# 可选：每小时检查备份状态
0 * * * * /opt/backups/check_backup.sh >> /opt/backups/backup_check.log 2>&1

# 可选：每天凌晨 3 点清理旧备份（如果备份在 2 点执行）
0 3 * * * /opt/backups/cleanup_backups.sh >> /opt/backups/cleanup.log 2>&1
```

### 5.5.6 验证定时任务

```bash
# 查看已配置的定时任务
crontab -l

# 查看 cron 服务状态
sudo systemctl status cron  # Ubuntu/Debian
sudo systemctl status crond # CentOS/RHEL
```

---

## 6. 反向代理配置

### 6.1 配置 Nginx

创建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/industrial-qa
# 或 CentOS: sudo nano /etc/nginx/conf.d/industrial-qa.conf
```

### 6.2 HTTP 配置（临时，用于测试）

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名或 IP

    # 日志
    access_log /var/log/nginx/industrial-qa-access.log;
    error_log /var/log/nginx/industrial-qa-error.log;

    # 客户端最大请求体大小（用于文件上传）
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查端点
    location /healthz {
        proxy_pass http://127.0.0.1:8000/api/v1/admin/healthz;
        access_log off;
    }
}
```

### 6.3 HTTPS 配置（生产环境推荐）

使用 Let's Encrypt 免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx  # Ubuntu/Debian
# 或
sudo yum install -y certbot python3-certbot-nginx      # CentOS/RHEL

# 获取 SSL 证书（会自动配置 Nginx）
sudo certbot --nginx -d your-domain.com

# 证书会自动续期（通过 cron 任务）
```

### 6.4 启用配置并重启 Nginx

```bash
# Ubuntu/Debian
sudo ln -s /etc/nginx/sites-available/industrial-qa /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 6.5 修改 Docker Compose 配置（暴露端口给 Nginx）

如果需要从宿主机访问应用，可以临时暴露端口：

```yaml
# 在 docker-compose.prod.yml 中，取消注释 app 服务的 ports
app:
  # ...
  ports:
    - "127.0.0.1:8000:8000"  # 仅本地访问
```

---

## 7. 验证和测试

### 7.1 基础功能测试

```bash
# 1. 健康检查
curl http://your-domain.com/api/v1/admin/healthz

# 2. 连通性测试
curl http://your-domain.com/api/v1/admin/ping

# 3. 管理员登录测试
curl -X POST http://your-domain.com/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "email": "admin@louxuezhi.com",
      "password": "271828LXZ"
    }
  }'
```

### 7.2 API 功能测试

```bash
# 获取访问令牌
TOKEN=$(curl -s -X POST http://your-domain.com/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"payload": {"email": "admin@louxuezhi.com", "password": "271828LXZ"}}' \
  | jq -r '.data.access_token')

# 测试获取用户列表
curl -X GET http://your-domain.com/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN"

# 测试创建用户
curl -X POST http://your-domain.com/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "username": "testuser",
    "full_name": "Test User",
    "role": "operator"
  }'
```

### 7.3 性能测试

```bash
# 使用 Apache Bench 进行简单压力测试
ab -n 100 -c 10 http://your-domain.com/api/v1/admin/ping

# 或使用 curl 测试响应时间
time curl http://your-domain.com/api/v1/admin/ping
```

---

## 8. 监控和维护

### 8.1 查看服务日志

```bash
# 实时查看应用日志
docker compose -f docker-compose.prod.yml logs -f app

# 查看最近 100 行日志
docker compose -f docker-compose.prod.yml logs --tail=100 app

# 查看错误日志
docker compose -f docker-compose.prod.yml logs app | grep -i error

# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f
```

### 8.2 查看资源使用情况

```bash
# 查看容器资源使用
docker stats

# 查看特定容器
docker stats industrial-qa-app-prod

# 查看系统资源
htop  # 需要安装: sudo apt-get install htop
# 或
top
```

### 8.3 备份数据

#### 备份 MySQL

```bash
# 创建备份目录
mkdir -p /opt/backups

# 备份数据库
docker compose -f docker-compose.prod.yml exec mysql mysqldump \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ${MYSQL_DATABASE} > /opt/backups/industrial_qa_$(date +%Y%m%d_%H%M%S).sql

# 或使用压缩备份
docker compose -f docker-compose.prod.yml exec mysql mysqldump \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  ${MYSQL_DATABASE} | gzip > /opt/backups/industrial_qa_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### 备份 Redis

```bash
# Redis 数据已通过 AOF 持久化，但也可以手动备份
docker compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} \
  BGSAVE

# 复制 RDB 文件
docker cp industrial-qa-redis-prod:/data/dump.rdb /opt/backups/redis_$(date +%Y%m%d_%H%M%S).rdb
```

#### 备份文件数据

```bash
# 备份上传的文件
tar -czf /opt/backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz /opt/industrial-qa/data/uploads

# 备份向量数据库
tar -czf /opt/backups/chroma_store_$(date +%Y%m%d_%H%M%S).tar.gz /opt/industrial-qa/chroma_store
```

### 8.4 自动备份脚本

项目已提供完整的备份脚本，位于 `scripts/` 目录。

#### 8.4.1 部署备份脚本

```bash
# 1. 创建备份目录
sudo mkdir -p /opt/backups
sudo chown $USER:$USER /opt/backups

# 2. 复制备份脚本到服务器
# 方式1: 如果脚本在项目目录中
cp /opt/industrial-qa/scripts/backup.sh /opt/backups/backup.sh
cp /opt/industrial-qa/scripts/restore_backup.sh /opt/backups/restore_backup.sh
cp /opt/industrial-qa/scripts/check_backup.sh /opt/backups/check_backup.sh

# 3. 设置执行权限
chmod +x /opt/backups/backup.sh
chmod +x /opt/backups/restore_backup.sh
chmod +x /opt/backups/check_backup.sh

# 4. 测试备份脚本
/opt/backups/backup.sh
```

#### 8.4.2 设置定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（根据需求选择一种）
```

**推荐配置（每天凌晨 2 点执行）**:
```bash
0 2 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1
```

**其他定时策略**:
```bash
# 每天凌晨 2 点和下午 2 点执行（每天两次）
0 2,14 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1

# 每周日凌晨 3 点执行完整备份，每天凌晨 2 点执行增量备份
0 3 * * 0 /opt/backups/backup.sh full >> /opt/backups/backup.log 2>&1
0 2 * * 1-6 /opt/backups/backup.sh incremental >> /opt/backups/backup.log 2>&1

# 每小时执行一次（高频备份，谨慎使用）
0 * * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1
```

**添加备份状态检查（每小时检查一次）**:
```bash
# 每小时检查备份状态，如果失败发送通知
0 * * * * /opt/backups/check_backup.sh || echo "备份检查失败" | mail -s "备份警告" admin@example.com
```

#### 8.4.3 备份脚本功能

备份脚本 (`backup.sh`) 包含以下功能：

1. **自动备份**:
   - MySQL 数据库（压缩格式）
   - Redis 数据（RDB 文件）
   - 上传的文件
   - 向量数据库（ChromaDB）

2. **错误处理**:
   - 自动验证备份文件完整性
   - 错误时记录日志并退出
   - 支持邮件通知（可选）

3. **自动清理**:
   - 自动删除超过保留期的旧备份（默认 7 天）
   - 可配置保留天数

4. **远程备份**（可选）:
   - 支持 AWS S3
   - 支持阿里云 OSS
   - 支持 SCP 上传

#### 8.4.4 恢复备份

```bash
# 查看可用备份
/opt/backups/restore_backup.sh

# 恢复指定备份
/opt/backups/restore_backup.sh 20241215_020000

# 恢复后重启服务
docker compose -f /opt/industrial-qa/docker-compose.prod.yml restart app
```

#### 8.4.5 检查备份状态

```bash
# 手动检查备份状态
/opt/backups/check_backup.sh

# 输出示例:
# ✅ 备份状态正常
# 最新备份: 20241215_020000
# 备份时间: 2024-12-15 02:00:00
# 备份年龄: 5 小时
```

#### 8.4.6 备份配置选项

编辑 `/opt/backups/backup.sh` 可以配置：

```bash
# 保留天数（默认 7 天）
RETENTION_DAYS=7

# 远程备份（取消注释并配置）
# REMOTE_BACKUP_ENABLED=true
# REMOTE_BACKUP_TYPE="s3"  # s3, oss, scp
# REMOTE_BACKUP_PATH="s3://your-bucket/backups/"

# 邮件通知（取消注释并配置）
# EMAIL_ENABLED=true
# EMAIL_TO="admin@example.com"
```

#### 8.4.7 备份策略建议

| 场景 | 备份频率 | 保留时间 | 说明 |
|------|---------|---------|------|
| 生产环境 | 每天 1-2 次 | 7-30 天 | 平衡存储和恢复需求 |
| 重要数据 | 每小时 | 7 天 | 高频备份 |
| 开发环境 | 每周 | 7 天 | 低频备份 |
| 测试环境 | 手动 | 3 天 | 按需备份 |

### 8.5 更新部署

```bash
cd /opt/industrial-qa

# 1. 备份当前数据
/opt/backups/backup.sh

# 2. 拉取最新代码
git pull
# 或重新上传新版本文件

# 3. 重新构建镜像
docker compose -f docker-compose.prod.yml build app

# 4. 执行数据库迁移（如有新迁移）
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 5. 重启服务
docker compose -f docker-compose.prod.yml restart app

# 或完全重新部署
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## 9. 故障排查

### 9.1 服务无法启动

```bash
# 查看详细日志
docker compose -f docker-compose.prod.yml logs app

# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 检查容器资源使用
docker stats

# 进入容器调试
docker compose -f docker-compose.prod.yml exec app bash
```

### 9.2 数据库连接失败

```bash
# 检查 MySQL 是否运行
docker compose -f docker-compose.prod.yml ps mysql

# 检查 MySQL 日志
docker compose -f docker-compose.prod.yml logs mysql

# 测试数据库连接
docker compose -f docker-compose.prod.yml exec mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1;"

# 检查网络连接
docker compose -f docker-compose.prod.yml exec app ping mysql
```

### 9.3 Redis 连接失败

```bash
# 检查 Redis 是否运行
docker compose -f docker-compose.prod.yml ps redis

# 测试 Redis 连接
docker compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping

# 查看 Redis 日志
docker compose -f docker-compose.prod.yml logs redis
```

### 9.4 应用响应慢

```bash
# 查看应用日志中的错误
docker compose -f docker-compose.prod.yml logs app | grep -i error

# 检查资源使用
docker stats

# 检查数据库查询性能
docker compose -f docker-compose.prod.yml exec mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "SHOW PROCESSLIST;"

# 检查慢查询
docker compose -f docker-compose.prod.yml exec mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} \
  -e "SHOW VARIABLES LIKE 'slow_query%';"
```

### 9.5 端口冲突

```bash
# 检查端口占用
sudo netstat -tulpn | grep :8000
# 或
sudo ss -tulpn | grep :8000

# 如果端口被占用，可以修改 docker-compose.prod.yml 中的端口映射
```

### 9.6 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理 Docker 未使用的资源
docker system prune -a

# 清理旧的日志文件
docker compose -f docker-compose.prod.yml logs --tail=0 app > /dev/null
```

### 9.7 权限问题

```bash
# 检查文件权限
ls -la /opt/industrial-qa

# 修复权限
sudo chown -R $USER:$USER /opt/industrial-qa
chmod 600 /opt/industrial-qa/.env
chmod +x /opt/industrial-qa/deploy_prod.sh
```

---

## 10. 安全建议

### 10.1 必须配置的安全项

1. **强密码**: 所有密码（MySQL、Redis、JWT）必须使用强密码
2. **JWT_SECRET**: 使用随机生成的强密钥（至少 32 字符）
3. **防火墙**: 仅开放必要端口（22, 80, 443）
4. **SSL/TLS**: 生产环境必须使用 HTTPS
5. **CORS**: 限制允许的来源域名
6. **定期更新**: 定期更新系统和 Docker 镜像

### 10.2 生成强密钥

```bash
# 生成 JWT Secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成随机密码
openssl rand -base64 32
```

### 10.3 限制 SSH 访问

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 建议配置：
# PermitRootLogin no
# PasswordAuthentication no  # 使用密钥认证
# Port 2222  # 修改默认端口

# 重启 SSH
sudo systemctl restart sshd
```

---

## 11. 完整部署流程总结

### 11.1 快速部署步骤（按顺序执行）

```bash
# ============================================
# 步骤 1: 服务器环境准备
# ============================================
# 1.1 安装 Docker 和 Docker Compose（参考 1.2 节）
# 1.2 安装 Nginx（参考 1.4 节）
# 1.3 配置防火墙（参考 1.5 节）

# ============================================
# 步骤 2: 代码部署
# ============================================
cd /opt
sudo mkdir -p industrial-qa
sudo chown $USER:$USER industrial-qa
cd industrial-qa

# 方式1: Git 克隆
git clone <your-repository-url> .

# 方式2: 文件传输（从本地）
# scp -r /path/to/IndustrialAgent/* user@server:/opt/industrial-qa/

# ============================================
# 步骤 3: 环境配置
# ============================================
cp env.example .env
nano .env  # 配置所有必需变量
chmod 600 .env

# 创建数据目录
mkdir -p data/uploads chroma_store
chmod -R 755 data/uploads chroma_store

# ============================================
# 步骤 4: 数据库迁移和服务启动
# ============================================
# 使用自动化部署脚本（推荐）
./deploy_prod.sh

# 或手动执行：
# docker compose -f docker-compose.prod.yml up -d mysql redis
# docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head
# docker compose -f docker-compose.prod.yml up -d

# ============================================
# 步骤 5: 部署备份脚本（重要！）
# ============================================
# 5.1 创建备份目录
sudo mkdir -p /opt/backups
sudo chown $USER:$USER /opt/backups

# 5.2 复制备份脚本
cp scripts/backup.sh /opt/backups/backup.sh
cp scripts/restore_backup.sh /opt/backups/restore_backup.sh
cp scripts/check_backup.sh /opt/backups/check_backup.sh
cp scripts/cleanup_backups.sh /opt/backups/cleanup_backups.sh
chmod +x /opt/backups/*.sh

# 5.3 测试备份
/opt/backups/backup.sh

# 5.4 配置定时任务
crontab -e
# 添加: 0 2 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1

# ============================================
# 步骤 6: 配置反向代理（可选但推荐）
# ============================================
# 参考 6. 反向代理配置章节

# ============================================
# 步骤 7: 验证和测试
# ============================================
# 参考 7. 验证和测试章节
```

### 11.2 部署检查清单

---

## 12. 快速部署检查清单

部署前请确认：

- [ ] Docker 和 Docker Compose 已安装
- [ ] `.env` 文件已配置所有必需变量
- [ ] 所有密码已设置为强密码
- [ ] JWT_SECRET 已生成并配置
- [ ] 数据目录已创建（`data/uploads`, `chroma_store`）
- [ ] 防火墙已配置
- [ ] Nginx 已安装并配置（如使用反向代理）
- [ ] SSL 证书已配置（生产环境）
- [ ] 备份脚本已部署并测试（`scripts/backup.sh`）
- [ ] 定时任务已配置（crontab）
- [ ] 备份恢复脚本已测试（`scripts/restore_backup.sh`）
- [ ] 备份检查脚本已配置（`scripts/check_backup.sh`）
- [ ] 监控和日志查看方式已了解

---

## 13. 常用命令速查

### 13.1 服务管理

```bash
# 进入应用目录
cd /opt/industrial-qa

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f app

# 重启服务
docker compose -f docker-compose.prod.yml restart app

# 停止服务
docker compose -f docker-compose.prod.yml down

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 执行数据库迁移
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 进入容器
docker compose -f docker-compose.prod.yml exec app bash

# 查看资源使用
docker stats
```

### 13.2 备份管理

```bash
# 手动执行备份
/opt/backups/backup.sh

# 查看备份日志（实时）
tail -f /opt/backups/backup.log

# 检查备份状态
/opt/backups/check_backup.sh

# 查看可用备份
/opt/backups/restore_backup.sh

# 恢复指定备份
/opt/backups/restore_backup.sh 20241215_020000

# 手动清理旧备份
/opt/backups/cleanup_backups.sh

# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e
```

### 13.3 数据库管理

```bash
# 备份数据库（使用备份脚本，推荐）
/opt/backups/backup.sh

# 手动备份数据库
docker compose -f docker-compose.prod.yml exec mysql mysqldump \
  -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > backup.sql

# 进入 MySQL
docker compose -f docker-compose.prod.yml exec mysql mysql \
  -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}
```

### 13.4 日志查看

```bash
# 应用日志
docker compose -f docker-compose.prod.yml logs -f app

# 备份日志
tail -f /opt/backups/backup.log

# 备份检查日志
tail -f /opt/backups/backup_check.log

# 清理日志
tail -f /opt/backups/cleanup.log

# 系统日志（查看 cron 执行情况）
sudo tail -f /var/log/syslog | grep CRON  # Ubuntu/Debian
sudo tail -f /var/log/cron                # CentOS/RHEL
```

---

## 总结

完成以上步骤后，您的 Industrial QA 系统应该已经成功部署到生产服务器上。如果遇到问题，请参考故障排查章节或查看日志文件。

**重要提醒**:
1. 首次部署后请立即修改默认管理员密码
2. 定期备份数据
3. 监控系统资源使用情况
4. 保持系统和依赖的更新
5. 定期检查日志文件

祝部署顺利！🚀

