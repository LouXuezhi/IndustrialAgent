#!/usr/bin/env python
"""
Initialize database schema using SQLAlchemy models.

This script creates all tables defined in app.db.models against the DATABASE_URL
configured in environment/.env. It uses the existing async engine and runs a
sync create_all via run_sync.

Usage:
    python scripts/init_db.py
    # or
    uv run python scripts/init_db.py
"""

import asyncio
import sys

from app.db.base import Base
from app.db.session import engine

# Import all models to ensure they are registered with Base.metadata
from app.db import models  # noqa: F401


async def main() -> None:
    """Initialize database by creating all tables."""
    print("Initializing database...")
    print(f"Database URL: {engine.url}")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created successfully!")
        print(f"Created tables: {', '.join(sorted(Base.metadata.tables.keys()))}")
    except Exception as e:
        print(f"✗ Error creating database tables: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())



