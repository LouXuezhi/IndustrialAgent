# 🚀 服务启动指南

## 快速启动

### 1. 检查环境

确保已安装依赖：

```bash
# 使用 uv（推荐）
uv sync --dev

# 或使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp env.example .env

# 编辑 .env 文件，填入必要的配置
# 至少需要配置：
# - DATABASE_URL（MySQL 连接）
# - OPENAI_API_KEY 或 DASHSCOPE_API_KEY（LLM API）
# - REDIS_URL（Redis 连接，可选）
```

**必需配置**：

```bash
# 数据库（必需）
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/industrial_qa

# LLM API（必需，至少配置一个）
OPENAI_API_KEY=sk-xxx
# 或
DASHSCOPE_API_KEY=sk-xxx
LLM_PROVIDER=dashscope
```

### 3. 初始化数据库

```bash
# 初始化数据库表结构
uv run python scripts/init_db.py
```

### 4. 启动服务

#### 方式 1: 使用 uvicorn（开发环境）

```bash
# 基础启动
uvicorn app.main:app --reload

# 指定端口和主机
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 使用 uv 运行
uv run uvicorn app.main:app --reload
```

#### 方式 2: 使用 Python 直接运行

```python
# 创建 start.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发时启用自动重载
    )
```

然后运行：

```bash
python start.py
# 或
uv run python start.py
```

#### 方式 3: 生产环境启动

```bash
# 使用 gunicorn + uvicorn workers（推荐生产环境）
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

### 5. 验证服务

启动成功后，访问：

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/
- **API 根路径**: http://localhost:8000/api/v1

## 启动参数说明

### uvicorn 常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--host` | 监听地址 | `0.0.0.0`（所有接口）或 `127.0.0.1`（仅本地） |
| `--port` | 监听端口 | `8000`（默认） |
| `--reload` | 自动重载 | 开发时启用，代码变更自动重启 |
| `--workers` | 工作进程数 | 生产环境建议 4-8 |
| `--log-level` | 日志级别 | `info`、`debug`、`warning` |

### 完整启动命令示例

```bash
# 开发环境（自动重载）
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug

# 生产环境（多进程）
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

## 前置条件检查

### 1. 数据库（MySQL）

确保 MySQL 服务已启动：

```bash
# 检查 MySQL 是否运行
mysql -u root -p -e "SELECT 1"

# 或使用 Docker
docker run -d \
    --name mysql \
    -e MYSQL_ROOT_PASSWORD=your_password \
    -e MYSQL_DATABASE=industrial_qa \
    -p 3306:3306 \
    mysql:8.0
```

### 2. Redis（可选但推荐）

```bash
# 检查 Redis 是否运行
redis-cli ping

# 或使用 Docker
docker run -d \
    --name redis \
    -p 6379:6379 \
    redis:7-alpine
```

### 3. 环境变量

检查 `.env` 文件是否存在且配置正确：

```bash
# 检查 .env 文件
cat .env | grep -E "(DATABASE_URL|API_KEY|REDIS_URL)"
```

## 常见问题

### 问题 1: 端口被占用

```bash
# 检查端口占用
lsof -i :8000

# 或使用其他端口
uvicorn app.main:app --port 8001
```

### 问题 2: 数据库连接失败

- 检查 `DATABASE_URL` 格式是否正确
- 确认 MySQL 服务已启动
- 验证用户名和密码
- 检查数据库是否存在

### 问题 3: 模块导入错误

```bash
# 确保在项目根目录运行
cd /Users/louxuezhi/IndustrialAgent

# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 使用 uv 运行（自动设置路径）
uv run uvicorn app.main:app --reload
```

### 问题 4: API 密钥未配置

确保至少配置了以下之一：
- `OPENAI_API_KEY`（如果使用 OpenAI）
- `DASHSCOPE_API_KEY`（如果使用 DashScope/Qwen）

### 问题 5: 依赖缺失

```bash
# 重新安装依赖
uv sync --dev

# 或
pip install -r requirements.txt
```

## 启动脚本（可选）

创建 `start.sh` 脚本：

```bash
#!/bin/bash

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在，请先配置环境变量"
    exit 1
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
python -c "from app.core.config import settings; print(f'数据库: {settings.database_url[:20]}...')" || {
    echo "❌ 数据库配置错误"
    exit 1
}

# 启动服务
echo "🚀 启动服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

使用：

```bash
chmod +x start.sh
./start.sh
```

## 生产环境部署

### 使用 systemd（Linux）

创建 `/etc/systemd/system/industrial-qa.service`：

```ini
[Unit]
Description=Industrial QA Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/IndustrialAgent
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl start industrial-qa
sudo systemctl enable industrial-qa
```

### 使用 Docker（推荐）

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
docker build -t industrial-qa .
docker run -d -p 8000:8000 --env-file .env industrial-qa
```

## 验证启动成功

启动后，你应该看到类似输出：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

访问 http://localhost:8000/docs 查看 API 文档。

## 下一步

- 📖 查看 [API 文档](achieved/api.md) 了解所有接口
- 🧪 运行测试验证功能
- 🔧 根据需求调整配置

---

**祝使用愉快！** 🎉

