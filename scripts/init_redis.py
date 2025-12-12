#!/usr/bin/env python
"""
Initialize and test Redis connection.

This script tests Redis connectivity and basic operations used by the application:
- Connection test
- Basic set/get/delete operations
- JWT token blacklist functionality test
- Key expiration test

Usage:
    python scripts/init_redis.py
    # or
    uv run python scripts/init_redis.py
"""

import asyncio
import sys
import time

import redis.asyncio as redis

from app.core.config import get_settings


async def test_connection(client: redis.Redis) -> bool:
    """Test basic Redis connection."""
    try:
        pong = await client.ping()
        if pong:
            print("✓ Redis connection successful")
            return True
        else:
            print("✗ Redis ping failed", file=sys.stderr)
            return False
    except Exception as e:
        print(f"✗ Redis connection failed: {e}", file=sys.stderr)
        return False


async def test_basic_operations(client: redis.Redis) -> bool:
    """Test basic Redis operations (set/get/delete)."""
    try:
        test_key = "test:init:basic"
        test_value = b"test_value"
        
        # Set
        await client.set(test_key, test_value)
        print("✓ SET operation successful")
        
        # Get
        value = await client.get(test_key)
        if value == test_value:
            print("✓ GET operation successful")
        else:
            print(f"✗ GET operation failed: expected {test_value}, got {value}", file=sys.stderr)
            return False
        
        # Delete
        await client.delete(test_key)
        deleted = await client.get(test_key)
        if deleted is None:
            print("✓ DELETE operation successful")
        else:
            print("✗ DELETE operation failed: key still exists", file=sys.stderr)
            return False
        
        return True
    except Exception as e:
        print(f"✗ Basic operations test failed: {e}", file=sys.stderr)
        return False


async def test_jwt_blacklist(client: redis.Redis) -> bool:
    """Test JWT token blacklist functionality."""
    try:
        test_jti = "test-jti-12345"
        blacklist_key = f"jwt:blacklist:{test_jti}"
        ttl_seconds = 60
        
        # Set blacklisted token
        await client.set(blacklist_key, b"revoked", ex=ttl_seconds)
        print("✓ JWT blacklist SET operation successful")
        
        # Check if token is blacklisted
        exists = await client.exists(blacklist_key)
        if exists:
            print("✓ JWT blacklist EXISTS check successful")
        else:
            print("✗ JWT blacklist EXISTS check failed", file=sys.stderr)
            return False
        
        # Get TTL
        ttl = await client.ttl(blacklist_key)
        if 0 < ttl <= ttl_seconds:
            print(f"✓ JWT blacklist TTL check successful (TTL: {ttl}s)")
        else:
            print(f"✗ JWT blacklist TTL check failed: {ttl}", file=sys.stderr)
            return False
        
        # Cleanup
        await client.delete(blacklist_key)
        print("✓ JWT blacklist cleanup successful")
        
        return True
    except Exception as e:
        print(f"✗ JWT blacklist test failed: {e}", file=sys.stderr)
        return False


async def test_expiration(client: redis.Redis) -> bool:
    """Test key expiration."""
    try:
        test_key = "test:init:expiration"
        test_value = b"expire_me"
        expire_seconds = 2
        
        # Set with expiration
        await client.setex(test_key, expire_seconds, test_value)
        print(f"✓ SETEX operation successful (expires in {expire_seconds}s)")
        
        # Check key exists
        exists = await client.exists(test_key)
        if not exists:
            print("✗ Key should exist immediately after SETEX", file=sys.stderr)
            return False
        
        # Wait for expiration
        print(f"  Waiting {expire_seconds + 1} seconds for key to expire...")
        await asyncio.sleep(expire_seconds + 1)
        
        # Check key is gone
        exists_after = await client.exists(test_key)
        if not exists_after:
            print("✓ Key expiration successful")
        else:
            print("✗ Key expiration failed: key still exists", file=sys.stderr)
            return False
        
        return True
    except Exception as e:
        print(f"✗ Expiration test failed: {e}", file=sys.stderr)
        return False


async def get_redis_info(client: redis.Redis) -> None:
    """Display Redis server information."""
    try:
        info = await client.info()
        print("\nRedis Server Information:")
        print(f"  Version: {info.get('redis_version', 'unknown')}")
        print(f"  OS: {info.get('os', 'unknown')}")
        print(f"  Used Memory: {info.get('used_memory_human', 'unknown')}")
        print(f"  Connected Clients: {info.get('connected_clients', 'unknown')}")
        print(f"  Total Keys: {info.get('db0', {}).get('keys', 0) if 'db0' in info else 'unknown'}")
    except Exception as e:
        print(f"  Warning: Could not retrieve server info: {e}")


async def main() -> None:
    """Run Redis initialization tests."""
    print("Initializing Redis connection...")
    settings = get_settings()
    print(f"Redis URL: {settings.redis_url}")
    
    client = None
    try:
        # Create Redis client
        client = redis.from_url(settings.redis_url, decode_responses=False)
        
        # Run tests
        tests = [
            ("Connection", test_connection),
            ("Basic Operations", test_basic_operations),
            ("JWT Blacklist", test_jwt_blacklist),
            ("Expiration", test_expiration),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n--- Testing {test_name} ---")
            result = await test_func(client)
            results.append((test_name, result))
        
        # Display server info
        await get_redis_info(client)
        
        # Summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        all_passed = True
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n✓ All Redis tests passed! Redis is ready to use.")
        else:
            print("\n✗ Some tests failed. Please check Redis configuration.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Redis initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if client:
            await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())

