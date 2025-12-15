# Dockerfile
# 阶段1: 构建依赖
FROM python:3.11-slim as builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖
RUN uv sync --frozen --no-dev

# 阶段2: 运行镜像
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV TOKENIZERS_PARALLELISM=false

# 创建必要的目录
RUN mkdir -p data/uploads chroma_store

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令（开发环境使用 uvicorn，生产环境使用 gunicorn）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

