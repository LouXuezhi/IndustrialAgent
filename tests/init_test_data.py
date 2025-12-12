#!/usr/bin/env python
"""
Initialize test data for the Industrial QA Backend.

This script creates:
- Test users (operator, maintenance, manager roles)
- Test groups with members
- Test document libraries (user and group libraries)
- Test documents and chunks

Usage:
    python tests/init_test_data.py
    # or
    uv run python tests/init_test_data.py
"""

import asyncio
import bcrypt
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session, engine
from app.db.models import User, Group, GroupMember, DocumentLibrary, Document, Chunk


# Test user credentials
TEST_USERS = [
    {
        "email": "operator@test.com",
        "username": "operator",
        "password": "test123456",
        "role": "operator",
        "full_name": "Operator User",
    },
    {
        "email": "maintenance@test.com",
        "username": "maintenance",
        "password": "test123456",
        "role": "maintenance",
        "full_name": "Maintenance Engineer",
    },
    {
        "email": "manager@test.com",
        "username": "manager",
        "password": "test123456",
        "role": "manager",
        "full_name": "Plant Manager",
    },
    {
        "email": "admin@test.com",
        "username": "admin",
        "password": "test123456",
        "role": "admin",
        "full_name": "System Admin",
    },
]

# Test groups
TEST_GROUPS = [
    {
        "name": "Production Team",
        "description": "Production department team",
    },
    {
        "name": "Maintenance Team",
        "description": "Maintenance department team",
    },
]


def _hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def create_test_users(session: AsyncSession) -> dict[str, User]:
    """Create test users and return a mapping of email to user."""
    print("Creating test users...")
    users = {}
    
    for user_data in TEST_USERS:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == user_data["email"]))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  User {user_data['email']} already exists, skipping...")
            users[user_data["email"]] = existing
            continue
        
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            password_hash=_hash_password(user_data["password"]),
            role=user_data["role"],
            full_name=user_data["full_name"],
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        users[user_data["email"]] = user
        print(f"  Created user: {user_data['email']} ({user_data['role']})")
    
    await session.commit()
    return users


async def create_test_groups(session: AsyncSession, users: dict[str, User]) -> dict[str, Group]:
    """Create test groups with members."""
    print("\nCreating test groups...")
    groups = {}
    
    for group_data in TEST_GROUPS:
        # Check if group already exists
        from sqlalchemy import select
        result = await session.execute(select(Group).where(Group.name == group_data["name"]))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  Group {group_data['name']} already exists, skipping...")
            groups[group_data["name"]] = existing
            continue
        
        group = Group(
            name=group_data["name"],
            description=group_data["description"],
        )
        session.add(group)
        await session.flush()
        
        # Add members based on group name
        if group_data["name"] == "Production Team":
            # operator as owner, maintenance as admin, manager as member
            members_data = [
                (users["operator@test.com"], "owner"),
                (users["maintenance@test.com"], "admin"),
                (users["manager@test.com"], "member"),
            ]
        else:  # Maintenance Team
            # maintenance as owner, operator as admin, manager as member
            members_data = [
                (users["maintenance@test.com"], "owner"),
                (users["operator@test.com"], "admin"),
                (users["manager@test.com"], "member"),
            ]
        
        for user, role in members_data:
            member = GroupMember(
                group_id=group.id,
                user_id=user.id,
                role=role,
            )
            session.add(member)
            print(f"    Added {user.email} as {role}")
        
        groups[group_data["name"]] = group
        print(f"  Created group: {group_data['name']}")
    
    await session.commit()
    return groups


async def create_test_libraries(session: AsyncSession, users: dict[str, User], groups: dict[str, Group]) -> dict:
    """Create test document libraries."""
    print("\nCreating test libraries...")
    libraries = {}
    
    # User libraries
    for email, user in users.items():
        lib_name = f"{user.username}'s Library"
        from sqlalchemy import select
        result = await session.execute(
            select(DocumentLibrary).where(
                DocumentLibrary.owner_id == user.id,
                DocumentLibrary.owner_type == "user",
                DocumentLibrary.name == lib_name,
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  Library '{lib_name}' already exists, skipping...")
            libraries[f"user_{email}"] = existing
            continue
        
        library = DocumentLibrary(
            name=lib_name,
            description=f"Personal library for {user.full_name}",
            owner_id=user.id,
            owner_type="user",
            vector_collection_name=f"library_{user.id}",
        )
        session.add(library)
        libraries[f"user_{email}"] = library
        print(f"  Created user library: {lib_name}")
    
    # Group libraries
    for group_name, group in groups.items():
        lib_name = f"{group_name} Library"
        from sqlalchemy import select
        result = await session.execute(
            select(DocumentLibrary).where(
                DocumentLibrary.owner_id == group.id,
                DocumentLibrary.owner_type == "group",
                DocumentLibrary.name == lib_name,
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  Library '{lib_name}' already exists, skipping...")
            libraries[f"group_{group_name}"] = existing
            continue
        
        library = DocumentLibrary(
            name=lib_name,
            description=f"Shared library for {group_name}",
            owner_id=group.id,
            owner_type="group",
            vector_collection_name=f"library_{group.id}",
        )
        session.add(library)
        libraries[f"group_{group_name}"] = library
        print(f"  Created group library: {lib_name}")
    
    await session.commit()
    return libraries


async def create_test_documents(session: AsyncSession, libraries: dict) -> list[Document]:
    """Create test documents with chunks."""
    print("\nCreating test documents...")
    documents = []
    
    # Sample document content
    sample_texts = [
        "设备维护手册\n\n第一章：日常维护\n设备需要定期检查，包括清洁、润滑和部件更换。\n\n第二章：故障排除\n常见故障包括：\n1. 设备过热\n2. 噪音异常\n3. 性能下降\n\n解决方案：\n- 检查冷却系统\n- 检查轴承和传动部件\n- 进行性能测试",
        "安全生产规范\n\n1. 进入生产区域必须佩戴安全帽\n2. 操作设备前需进行安全检查\n3. 发现安全隐患立即报告\n4. 遵守操作规程，禁止违章作业\n5. 定期参加安全培训",
        "质量管理体系\n\n质量目标：\n- 产品合格率 ≥ 99%\n- 客户满意度 ≥ 95%\n- 投诉处理及时率 100%\n\n质量控制措施：\n1. 原材料检验\n2. 生产过程监控\n3. 成品检测\n4. 持续改进",
    ]
    
    # Create documents in first user library
    user_lib_key = "user_operator@test.com"
    if user_lib_key in libraries:
        library = libraries[user_lib_key]
        
        for i, text in enumerate(sample_texts):
            doc_title = f"测试文档_{i+1}.txt"
            from sqlalchemy import select
            result = await session.execute(
                select(Document).where(
                    Document.library_id == library.id,
                    Document.title == doc_title,
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  Document '{doc_title}' already exists, skipping...")
                documents.append(existing)
                continue
            
            # Create document
            document = Document(
                title=doc_title,
                source_path=f"/tmp/{doc_title}",  # Placeholder path
                library_id=library.id,
                meta={"file_type": ".txt", "file_size": len(text.encode("utf-8"))},
            )
            session.add(document)
            await session.flush()
            
            # Create chunks
            chunk_size = 200
            chunks = []
            for start in range(0, len(text), chunk_size):
                chunk_text = text[start : start + chunk_size]
                chunk = Chunk(
                    document_id=document.id,
                    content=chunk_text,
                    meta={"offset": start, "length": len(chunk_text)},
                )
                chunks.append(chunk)
            
            session.add_all(chunks)
            documents.append(document)
            print(f"  Created document: {doc_title} with {len(chunks)} chunks")
    
    await session.commit()
    return documents


async def main():
    """Main function to initialize all test data."""
    print("=" * 60)
    print("Initializing Test Data for Industrial QA Backend")
    print("=" * 60)
    
    try:
        async with async_session() as session:
            try:
                # Create test users
                users = await create_test_users(session)
                
                # Create test groups
                groups = await create_test_groups(session, users)
                
                # Create test libraries
                libraries = await create_test_libraries(session, users, groups)
                
                # Create test documents
                documents = await create_test_documents(session, libraries)
                
                print("\n" + "=" * 60)
                print("Test Data Initialization Complete!")
                print("=" * 60)
                print("\nTest User Credentials:")
                print("-" * 60)
                for user_data in TEST_USERS:
                    print(f"  Email: {user_data['email']}")
                    print(f"  Password: {user_data['password']}")
                    print(f"  Role: {user_data['role']}")
                    print()
                
                print("\nTest Groups:")
                print("-" * 60)
                for group_name, group in groups.items():
                    print(f"  {group_name} (ID: {group.id})")
                
                print("\nTest Libraries:")
                print("-" * 60)
                for lib_key, library in libraries.items():
                    print(f"  {library.name} (ID: {library.id}, Type: {library.owner_type})")
                
                print(f"\nCreated {len(documents)} test documents")
                print("\nYou can now use these credentials to test the API endpoints.")
                
            except Exception as e:
                print(f"\nError initializing test data: {e}")
                import traceback
                traceback.print_exc()
                await session.rollback()
                raise
    finally:
        # Explicitly close the engine to avoid "Event loop is closed" warnings
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

