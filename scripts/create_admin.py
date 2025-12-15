#!/usr/bin/env python
"""
创建管理员用户的脚本

Usage:
    python scripts/create_admin.py <email> <password> [username] [full_name]
    # 或
    uv run python scripts/create_admin.py <email> <password> [username] [full_name]

示例:
    python scripts/create_admin.py admin@example.com admin123
    python scripts/create_admin.py admin@example.com admin123 admin "系统管理员"
"""

import asyncio
import bcrypt
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session, engine
from app.db.models import User, DocumentLibrary


def _hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def create_admin(
    email: str,
    password: str,
    username: str | None = None,
    full_name: str | None = None,
) -> User:
    """创建管理员用户，如果用户已存在则更新为管理员角色。"""
    async with async_session() as session:
        # 检查用户是否已存在
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"用户 {email} 已存在，更新为管理员...")
            existing.role = "admin"
            await session.commit()
            await session.refresh(existing)
            print(f"✓ 用户角色已更新为管理员")
            return existing
        
        # 检查用户名是否已被使用
        if username:
            username_result = await session.execute(select(User).where(User.username == username))
            if username_result.scalar_one_or_none():
                raise ValueError(f"用户名 {username} 已被使用")
        
        # 创建新管理员
        admin = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=_hash_password(password),
            role="admin",
            is_verified=True,
        )
        session.add(admin)
        await session.flush()
        
        # 创建默认个人库
        library_name = f"{full_name or username or email.split('@')[0]}的个人库"
        library = DocumentLibrary(
            name=library_name,
            description="个人默认文档库",
            owner_id=admin.id,
            owner_type="user",
            is_default=True,
        )
        session.add(library)
        await session.flush()
        library.vector_collection_name = f"library_{library.id}"
        
        await session.commit()
        await session.refresh(admin)
        print(f"✓ 管理员用户创建成功")
        print(f"  - 邮箱: {email}")
        print(f"  - 用户名: {username or '(未设置)'}")
        print(f"  - 全名: {full_name or '(未设置)'}")
        print(f"  - 角色: admin")
        print(f"  - 默认库ID: {library.id}")
        return admin


async def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/create_admin.py <email> <password> [username] [full_name]")
        print("\n参数说明:")
        print("  email      - 管理员邮箱（必填）")
        print("  password   - 管理员密码（必填）")
        print("  username   - 用户名（可选）")
        print("  full_name  - 全名（可选）")
        print("\n示例:")
        print("  python scripts/create_admin.py admin@example.com admin123")
        print("  python scripts/create_admin.py admin@example.com admin123 admin '系统管理员'")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    username = sys.argv[3] if len(sys.argv) > 3 else None
    full_name = sys.argv[4] if len(sys.argv) > 4 else None
    
    # 验证密码长度
    if len(password) < 6:
        print("✗ 错误: 密码长度至少为 6 个字符", file=sys.stderr)
        sys.exit(1)
    
    try:
        await create_admin(email, password, username, full_name)
    except ValueError as e:
        print(f"✗ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ 创建失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

