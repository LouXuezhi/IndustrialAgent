#!/usr/bin/env python
"""
测试 Redis 是否被实际使用。

检查：
1. Redis 连接是否正常
2. JWT 黑名单功能是否工作
3. 是否有数据写入/读取
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.security import revoke_token
from app.deps import get_redis
import redis.asyncio as redis


async def test_redis_connection():
    """测试 Redis 连接"""
    print("=" * 60)
    print("测试 Redis 连接")
    print("=" * 60)
    
    settings = get_settings()
    print(f"Redis URL: {settings.redis_url}")
    
    if not settings.redis_url:
        print("❌ Redis URL 未配置！")
        return False
    
    try:
        client = await get_redis()
        # 测试连接
        await client.ping()
        print("✓ Redis 连接成功")
        
        # 获取 Redis 信息
        info = await client.info("server")
        print(f"✓ Redis 版本: {info.get('redis_version', 'unknown')}")
        
        await client.aclose()
        return True
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False


async def test_jwt_blacklist():
    """测试 JWT 黑名单功能"""
    print("\n" + "=" * 60)
    print("测试 JWT 黑名单功能")
    print("=" * 60)
    
    settings = get_settings()
    if not settings.redis_url:
        print("❌ Redis URL 未配置，跳过测试")
        return False
    
    try:
        client = await get_redis()
        
        # 测试写入黑名单
        test_jti = "test-jti-12345"
        test_exp = 1735689600  # 未来时间戳
        
        print(f"写入测试 token (jti: {test_jti}) 到黑名单...")
        await revoke_token(client, test_jti, test_exp)
        
        # 检查是否写入成功
        key = f"jwt:blacklist:{test_jti}"
        exists = await client.exists(key)
        
        if exists:
            print(f"✓ Token 已成功写入黑名单 (key: {key})")
            
            # 获取 TTL
            ttl = await client.ttl(key)
            print(f"✓ TTL: {ttl} 秒")
            
            # 清理测试数据
            await client.delete(key)
            print("✓ 测试数据已清理")
            return True
        else:
            print("❌ Token 未写入黑名单")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await client.aclose()
        except:
            pass


async def check_redis_keys():
    """检查 Redis 中的键"""
    print("\n" + "=" * 60)
    print("检查 Redis 中的键")
    print("=" * 60)
    
    settings = get_settings()
    if not settings.redis_url:
        print("❌ Redis URL 未配置，跳过检查")
        return
    
    try:
        client = await get_redis()
        
        # 查找所有 JWT 黑名单相关的键
        pattern = "jwt:blacklist:*"
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key.decode() if isinstance(key, bytes) else key)
        
        if keys:
            print(f"✓ 找到 {len(keys)} 个黑名单 token:")
            for key in keys[:10]:  # 只显示前10个
                ttl = await client.ttl(key)
                print(f"  - {key} (TTL: {ttl}s)")
            if len(keys) > 10:
                print(f"  ... 还有 {len(keys) - 10} 个")
        else:
            print("ℹ 当前没有黑名单 token（这是正常的，如果最近没有注销操作）")
        
        # 查找邮箱验证相关的键
        pattern = "email:verify:*"
        verify_keys = []
        async for key in client.scan_iter(match=pattern):
            verify_keys.append(key.decode() if isinstance(key, bytes) else key)
        
        if verify_keys:
            print(f"\n✓ 找到 {len(verify_keys)} 个邮箱验证 token")
        
        # 统计所有键
        all_keys = []
        async for key in client.scan_iter(match="*"):
            all_keys.append(key.decode() if isinstance(key, bytes) else key)
        
        print(f"\n✓ Redis 中总共有 {len(all_keys)} 个键")
        
        await client.aclose()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


async def test_actual_usage():
    """测试实际使用场景"""
    print("\n" + "=" * 60)
    print("测试实际使用场景")
    print("=" * 60)
    
    print("提示：要测试实际使用，请：")
    print("1. 启动 FastAPI 服务")
    print("2. 调用 POST /api/v1/login 登录")
    print("3. 调用 POST /api/v1/logout 注销")
    print("4. 然后运行此脚本检查 Redis 中的键")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Redis 使用情况检查")
    print("=" * 60 + "\n")
    
    # 1. 测试连接
    connected = await test_redis_connection()
    
    if not connected:
        print("\n❌ Redis 连接失败，请检查配置")
        return
    
    # 2. 测试黑名单功能
    await test_jwt_blacklist()
    
    # 3. 检查现有键
    await check_redis_keys()
    
    # 4. 使用建议
    await test_actual_usage()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

