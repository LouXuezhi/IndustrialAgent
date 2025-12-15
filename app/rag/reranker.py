"""
重排序模块：使用 Cross-Encoder 对检索结果进行重新排序，提升检索质量。
支持缓存机制以提升重复查询的性能。
"""
import hashlib
import json
import logging
from dataclasses import replace
from typing import Any

logger = logging.getLogger(__name__)


class Reranker:
    """
    重排序器：使用 Cross-Encoder 模型对检索结果重新排序。
    
    Cross-Encoder 通过同时编码查询和文档，能够更准确地评估相关性。
    """
    
    def __init__(self, model_name: str | None = None, enable: bool = True, enable_cache: bool = True):
        """
        初始化重排序器。
        
        Args:
            model_name: 重排序模型名称，默认使用中文模型 BAAI/bge-reranker-base
            enable: 是否启用重排序（默认 True）
            enable_cache: 是否启用缓存（默认 True）
        """
        self.enable = enable
        self.enable_cache = enable_cache
        self.model = None
        self.model_name = model_name or "BAAI/bge-reranker-base"
        self.cache_ttl = 7200  # 默认2小时
        self._redis_client = None
        self._memory_cache = {}  # 内存缓存作为后备
        
        if self.enable:
            try:
                import os
                
                # 配置 Hugging Face 镜像（必须在导入 sentence_transformers 之前设置）
                # 优先使用 Settings 中的配置，其次使用环境变量
                from app.core.config import get_settings
                settings = get_settings()
                hf_mirror = settings.hf_endpoint or os.getenv("HF_ENDPOINT", "")
                if hf_mirror:
                    # 设置多个可能的环境变量，确保镜像生效
                    os.environ["HF_ENDPOINT"] = hf_mirror
                    os.environ["HUGGINGFACE_HUB_CACHE"] = os.getenv("HUGGINGFACE_HUB_CACHE", "")
                    logger.info(f"使用 Hugging Face 镜像: {hf_mirror}")
                
                # 初始化缓存
                if self.enable_cache:
                    self.cache_ttl = settings.rerank_cache_ttl
                    # 尝试连接 Redis（如果可用）
                    if settings.redis_url:
                        try:
                            import redis.asyncio as redis
                            self._redis_client = redis.from_url(settings.redis_url, decode_responses=True)
                            logger.info("✅ 重排序缓存：使用 Redis")
                        except Exception as e:
                            logger.warning(f"⚠️ Redis 连接失败，使用内存缓存: {e}")
                            self._redis_client = None
                    else:
                        logger.info("ℹ️ 重排序缓存：使用内存缓存（Redis 未配置）")
                
                # 在设置环境变量后再导入
                from sentence_transformers import CrossEncoder
                
                logger.info(f"🔄 初始化重排序模型: {self.model_name}")
                self.model = CrossEncoder(self.model_name)
                logger.info("✅ 重排序模型加载完成")
            except ImportError:
                logger.warning(
                    "⚠️ sentence-transformers 未安装，重排序功能已禁用。"
                    "请运行: pip install sentence-transformers"
                )
                self.enable = False
            except Exception as e:
                error_msg = str(e)
                if "SSL" in error_msg or "huggingface.co" in error_msg:
                    logger.warning(
                        f"⚠️ 无法从 Hugging Face 下载模型（网络问题），重排序功能已禁用。\n"
                        f"解决方案：\n"
                        f"1. 设置环境变量 HF_ENDPOINT=https://hf-mirror.com（使用镜像）\n"
                        f"2. 或设置 ENABLE_RERANK=false 禁用重排序\n"
                        f"3. 或配置代理后重试"
                    )
                else:
                    logger.error(f"❌ 重排序模型加载失败: {e}", exc_info=True)
                self.enable = False
    
    def _generate_cache_key(self, query: str, chunk_texts: list[str]) -> str:
        """生成缓存键"""
        # 使用查询和文档文本的哈希值生成缓存键
        content = f"{query}|||{','.join(chunk_texts)}"
        key_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"rerank:{key_hash}"
    
    async def _get_cached_scores(self, cache_key: str) -> list[float] | None:
        """从缓存获取重排序分数"""
        if not self.enable_cache:
            return None
        
        try:
            # 优先使用 Redis
            if self._redis_client:
                try:
                    cached = await self._redis_client.get(cache_key)
                    if cached:
                        scores = json.loads(cached)
                        logger.debug(f"重排序缓存命中（Redis）: {cache_key}")
                        return scores
                except Exception as e:
                    logger.debug(f"Redis 缓存读取失败: {e}")
            
            # 后备：使用内存缓存
            if cache_key in self._memory_cache:
                cached_data = self._memory_cache[cache_key]
                scores = cached_data.get("scores")
                logger.debug(f"重排序缓存命中（内存）: {cache_key}")
                return scores
        except Exception as e:
            logger.debug(f"缓存读取失败: {e}")
        
        return None
    
    async def _set_cached_scores(self, cache_key: str, scores: list[float]) -> None:
        """缓存重排序分数"""
        if not self.enable_cache:
            return
        
        try:
            # 优先使用 Redis
            if self._redis_client:
                try:
                    await self._redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(scores)
                    )
                    logger.debug(f"重排序缓存写入（Redis）: {cache_key}, TTL: {self.cache_ttl}s")
                    return
                except Exception as e:
                    logger.debug(f"Redis 缓存写入失败: {e}")
            
            # 后备：使用内存缓存（限制大小，避免内存溢出）
            if len(self._memory_cache) < 1000:  # 最多缓存1000条
                self._memory_cache[cache_key] = {
                    "scores": scores,
                    "timestamp": __import__("time").time()
                }
                logger.debug(f"重排序缓存写入（内存）: {cache_key}")
            else:
                # 简单的 LRU：删除最旧的条目
                if self._memory_cache:
                    oldest_key = min(
                        self._memory_cache.keys(),
                        key=lambda k: self._memory_cache[k].get("timestamp", 0)
                    )
                    del self._memory_cache[oldest_key]
                    self._memory_cache[cache_key] = {
                        "scores": scores,
                        "timestamp": __import__("time").time()
                    }
        except Exception as e:
            logger.debug(f"缓存写入失败: {e}")
    
    async def rerank_async(
        self,
        query: str,
        chunks: list[Any],
        top_k: int | None = None
    ) -> list[Any]:
        """
        异步重排序（支持缓存）。
        
        Args:
            query: 查询文本
            chunks: 检索结果列表（RetrievedChunk 对象）
            top_k: 返回结果数量，None 表示返回所有结果
        
        Returns:
            重排序后的结果列表
        """
        if not self.enable or not self.model or not chunks:
            return chunks
        
        if len(chunks) <= 1:
            return chunks
        
        try:
            # 构建查询-文档对
            chunk_texts = [chunk.text for chunk in chunks]
            pairs = [[query, text] for text in chunk_texts]
            
            # 尝试从缓存获取
            cache_key = self._generate_cache_key(query, chunk_texts)
            cached_scores = await self._get_cached_scores(cache_key)
            
            if cached_scores is not None:
                # 使用缓存的分数
                scores = cached_scores
                logger.debug(f"使用缓存的重排序分数: {len(scores)} 条")
            else:
                # 计算相关性分数（Cross-Encoder 会同时编码查询和文档）
                scores = self.model.predict(pairs)
                # 缓存分数
                await self._set_cached_scores(cache_key, scores.tolist() if hasattr(scores, 'tolist') else list(scores))
            
            # 将分数添加到 chunks 并重新排序
            reranked_chunks = []
            for chunk, score in zip(chunks, scores):
                # 更新分数为重排序分数
                reranked_chunk = replace(
                    chunk,
                    score=float(score),
                    source_type="reranked"
                )
                reranked_chunks.append(reranked_chunk)
            
            # 按重排序分数降序排列
            reranked_chunks.sort(key=lambda c: c.score, reverse=True)
            
            logger.debug(
                f"重排序完成: {len(chunks)} 条结果，"
                f"分数范围: {min(scores):.4f} - {max(scores):.4f}"
            )
            
            # 返回 Top-K
            if top_k is not None:
                return reranked_chunks[:top_k]
            return reranked_chunks
            
        except Exception as e:
            logger.error(f"重排序失败: {e}", exc_info=True)
            # 失败时返回原始结果
            return chunks
    
    def rerank(
        self,
        query: str,
        chunks: list[Any],
        top_k: int | None = None
    ) -> list[Any]:
        """
        同步重排序（兼容旧接口，内部调用异步版本）。
        
        Args:
            query: 查询文本
            chunks: 检索结果列表（RetrievedChunk 对象）
            top_k: 返回结果数量，None 表示返回所有结果
        
        Returns:
            重排序后的结果列表
        """
        import asyncio
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用同步版本（不使用缓存）
                return self._rerank_sync(query, chunks, top_k)
            else:
                # 如果事件循环未运行，可以运行异步版本
                return loop.run_until_complete(self.rerank_async(query, chunks, top_k))
        except RuntimeError:
            # 没有事件循环，使用同步版本
            return self._rerank_sync(query, chunks, top_k)
    
    def _rerank_sync(self, query: str, chunks: list[Any], top_k: int | None = None) -> list[Any]:
        """同步重排序（不使用缓存，用于兼容）"""
        if not self.enable or not self.model or not chunks:
            return chunks
        
        if len(chunks) <= 1:
            return chunks
        
        try:
            pairs = [[query, chunk.text] for chunk in chunks]
            scores = self.model.predict(pairs)
            
            reranked_chunks = []
            for chunk, score in zip(chunks, scores):
                reranked_chunk = replace(
                    chunk,
                    score=float(score),
                    source_type="reranked"
                )
                reranked_chunks.append(reranked_chunk)
            
            reranked_chunks.sort(key=lambda c: c.score, reverse=True)
            
            if top_k is not None:
                return reranked_chunks[:top_k]
            return reranked_chunks
            
        except Exception as e:
            logger.error(f"重排序失败: {e}", exc_info=True)
            return chunks
    
    def is_enabled(self) -> bool:
        """检查重排序是否启用且可用。"""
        return self.enable and self.model is not None

