"""
缓存工具模块：提供查询结果缓存功能。
"""
import hashlib
import json
import logging
from typing import Any

try:
    import redis.asyncio as redis
except ImportError:
    # 如果 redis 未安装，使用同步版本（向后兼容）
    try:
        import redis
    except ImportError:
        redis = None

logger = logging.getLogger(__name__)


def generate_search_cache_key(
    query: str,
    library_id: str | None,
    limit: int,
    user_id: str | None = None
) -> str:
    """
    生成搜索缓存键。
    
    Args:
        query: 查询文本
        library_id: 文档库ID
        limit: 返回结果数量限制
        user_id: 用户ID（用于权限隔离）
    
    Returns:
        缓存键字符串
    """
    # 构建键数据（包含用户ID确保权限隔离）
    key_data = f"{query}:{library_id}:{limit}:{user_id or ''}"
    key_hash = hashlib.md5(key_data.encode('utf-8')).hexdigest()
    return f"search:doc:{key_hash}"


async def get_cached_search_result(
    redis_client: redis.Redis,
    cache_key: str
) -> list[dict] | None:
    """
    从缓存获取搜索结果。
    
    Args:
        redis_client: Redis 客户端
        cache_key: 缓存键
    
    Returns:
        缓存的搜索结果，如果不存在则返回 None
    """
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            result = json.loads(cached)
            logger.debug(f"缓存命中: {cache_key}")
            return result
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"缓存数据解析失败: {cache_key}, {e}")
        return None
    except Exception as e:
        logger.error(f"缓存读取失败: {cache_key}, {e}", exc_info=True)
        return None


async def cache_search_result(
    redis_client: redis.Redis | None,
    cache_key: str,
    result: list[dict],
    ttl: int = 3600
) -> None:
    """
    缓存搜索结果。
    
    Args:
        redis_client: Redis 客户端
        cache_key: 缓存键
        result: 搜索结果（字典列表）
        ttl: 过期时间（秒），默认1小时
    """
    if redis_client is None:
        return
    try:
        await redis_client.setex(
            cache_key,
            ttl,
            json.dumps(result, ensure_ascii=False, default=str)
        )
        logger.debug(f"缓存写入: {cache_key}, TTL: {ttl}s")
    except Exception as e:
        logger.error(f"缓存写入失败: {cache_key}, {e}", exc_info=True)


async def invalidate_search_cache(
    redis_client: redis.Redis | None,
    library_id: str | None = None,
    pattern: str | None = None
) -> int:
    """
    清除搜索缓存。
    
    Args:
        redis_client: Redis 客户端
        library_id: 文档库ID（如果提供，只清除该库的缓存）
        pattern: 自定义缓存键模式（如果提供，使用此模式）
    
    Returns:
        清除的缓存数量
    """
    if redis_client is None:
        return 0
    try:
        if pattern:
            cache_pattern = pattern
        elif library_id:
            # 清除该库的所有搜索缓存
            cache_pattern = f"search:doc:*"
        else:
            # 清除所有搜索缓存
            cache_pattern = "search:doc:*"
        
        # 使用 SCAN 而不是 KEYS（避免阻塞 Redis）
        deleted_count = 0
        cursor = 0
        
        while True:
            cursor, keys = await redis_client.scan(
                cursor,
                match=cache_pattern,
                count=100  # 每次扫描100个键
            )
            
            if keys:
                # 如果指定了 library_id，需要进一步过滤
                if library_id and not pattern:
                    # 读取每个键的值，检查是否包含该 library_id
                    # 注意：这需要反序列化，性能较差
                    # 更好的方案是在缓存键中包含 library_id
                    filtered_keys = []
                    for key in keys:
                        try:
                            value = await redis_client.get(key)
                            if value:
                                data = json.loads(value)
                                # 检查结果中是否有该库的文档
                                if any(
                                    item.get("library_id") == str(library_id)
                                    for item in data
                                    if isinstance(item, dict)
                                ):
                                    filtered_keys.append(key)
                        except Exception:
                            continue
                    keys = filtered_keys
                
                if keys:
                    deleted = await redis_client.delete(*keys)
                    deleted_count += deleted
            
            if cursor == 0:
                break
        
        if deleted_count > 0:
            logger.info(f"清除搜索缓存: {cache_pattern}, 删除 {deleted_count} 个键")
        
        return deleted_count
    except Exception as e:
        logger.error(f"清除缓存失败: {e}", exc_info=True)
        return 0


async def record_cache_stats(
    redis_client: redis.Redis | None,
    hit: bool
) -> None:
    """
    记录缓存统计信息。
    
    Args:
        redis_client: Redis 客户端
        hit: 是否命中缓存
    """
    if redis_client is None:
        return
    try:
        stats_key = "cache:stats:search"
        if hit:
            await redis_client.hincrby(stats_key, "hits", 1)
        else:
            await redis_client.hincrby(stats_key, "misses", 1)
        
        # 设置过期时间（24小时）
        await redis_client.expire(stats_key, 86400)
    except Exception as e:
        logger.debug(f"缓存统计记录失败: {e}")


async def get_cache_hit_rate(redis_client: redis.Redis | None) -> float:
    """
    获取缓存命中率。
    
    Args:
        redis_client: Redis 客户端
    
    Returns:
        命中率（0.0-1.0），如果无法计算则返回 0.0
    """
    if redis_client is None:
        return 0.0
    try:
        stats = await redis_client.hgetall("cache:stats:search")
        hits = int(stats.get(b"hits", 0) if isinstance(stats.get("hits"), bytes) else stats.get("hits", 0))
        misses = int(stats.get(b"misses", 0) if isinstance(stats.get("misses"), bytes) else stats.get("misses", 0))
        total = hits + misses
        return hits / total if total > 0 else 0.0
    except Exception as e:
        logger.debug(f"获取缓存命中率失败: {e}")
        return 0.0


def calculate_cache_ttl(result_count: int, query_length: int) -> int:
    """
    根据查询特征动态计算缓存 TTL。
    
    Args:
        result_count: 结果数量
        query_length: 查询文本长度
    
    Returns:
        TTL（秒）
    """
    base_ttl = 3600  # 基础1小时
    
    # 结果多说明查询热门，缓存更久
    if result_count > 10:
        return 7200  # 2小时
    
    # 短查询（可能是热门查询）
    if query_length < 10:
        return 5400  # 1.5小时
    
    return base_ttl

