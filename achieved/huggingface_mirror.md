# Hugging Face 镜像配置指南

## 问题描述

如果启动服务时遇到以下错误：

```
SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol
Max retries exceeded with url: /BAAI/bge-reranker-base/resolve/main/config.json
```

这通常是因为无法访问 `huggingface.co`（网络问题或 SSL 问题）。

## 解决方案

### 方案 1: 使用 Hugging Face 镜像（推荐）

在 `.env` 文件中添加：

```bash
# 使用国内镜像（推荐）
HF_ENDPOINT=https://hf-mirror.com
```

或者在启动前设置环境变量：

```bash
export HF_ENDPOINT=https://hf-mirror.com
uvicorn app.main:app --reload
```

**可用的镜像站点**：
- `https://hf-mirror.com` - 国内镜像（推荐）
- `https://huggingface.co` - 官方站点（默认）

### 方案 2: 临时禁用重排序

如果暂时不需要重排序功能，可以在 `.env` 中禁用：

```bash
ENABLE_RERANK=false
```

服务会正常启动，但不会使用重排序功能。

### 方案 3: 配置代理

如果使用代理，设置代理环境变量：

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### 方案 4: 手动下载模型到本地

1. 使用镜像站点手动下载模型：
   ```bash
   # 访问 https://hf-mirror.com/BAAI/bge-reranker-base
   # 下载所有文件到本地目录
   ```

2. 修改代码使用本地模型：
   ```python
   # 在 app/rag/reranker.py 中
   self.model = CrossEncoder(
       model_name="/path/to/local/bge-reranker-base",
       local_files_only=True
   )
   ```

## 验证配置

启动服务后，检查日志：

```
✅ 使用 Hugging Face 镜像: https://hf-mirror.com
🔄 初始化重排序模型: BAAI/bge-reranker-base
✅ 重排序模型加载完成
```

如果看到这些日志，说明配置成功。

## 常见问题

### Q: 镜像站点也无法访问？

A: 尝试：
1. 检查网络连接
2. 尝试其他镜像站点
3. 使用代理
4. 临时禁用重排序功能

### Q: 模型下载很慢？

A: 使用镜像站点通常比官方站点快很多，特别是国内用户。

### Q: 如何知道模型是否已下载？

A: 模型会缓存到 `~/.cache/huggingface/hub/` 目录，下载一次后下次启动会直接使用缓存。

## 总结

最简单的解决方案是在 `.env` 文件中添加：

```bash
HF_ENDPOINT=https://hf-mirror.com
```

这样就能正常下载和使用重排序模型了。

