#!/bin/bash

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在，请先配置环境变量"
    echo "运行: cp env.example .env"
    exit 1
fi

# 如果 .env 中没有设置 HF_ENDPOINT，使用镜像（解决 Hugging Face 下载问题）
if ! grep -q "HF_ENDPOINT" .env; then
    echo "💡 提示: 如果遇到 Hugging Face 模型下载问题，可在 .env 中添加:"
    echo "   HF_ENDPOINT=https://hf-mirror.com"
    echo ""
fi

# 如果 .env 中配置了 HF_ENDPOINT，在启动前设置环境变量
if grep -q "HF_ENDPOINT" .env 2>/dev/null; then
    export HF_ENDPOINT=$(grep "^HF_ENDPOINT=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$HF_ENDPOINT" ]; then
        echo "✅ 使用 Hugging Face 镜像: $HF_ENDPOINT"
        export HF_ENDPOINT
    fi
fi

# 禁用 tokenizers 并行化警告（避免 fork 后的死锁警告）
export TOKENIZERS_PARALLELISM=false

# 启动服务
echo "🚀 启动 Industrial QA Backend..."
echo "📍 访问地址: http://localhost:8000"
echo "📖 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
