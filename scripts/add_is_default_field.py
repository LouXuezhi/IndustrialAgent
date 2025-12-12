#!/usr/bin/env python
"""
Add is_default field to document_libraries table.

This migration script adds the is_default boolean field to the document_libraries table
for existing databases. New databases will have this field created automatically via init_db.py.

Usage:
    python scripts/add_is_default_field.py
    # or
    uv run python scripts/add_is_default_field.py
"""

import asyncio
import sys

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import async_session, engine


async def main() -> None:
    """Add is_default field to document_libraries table."""
    settings = get_settings()
    print("Adding is_default field to document_libraries table...")
    print(f"Database URL: {settings.database_url}")
    
    try:
        async with async_session() as session:
            # Check if column already exists
            if "mysql" in settings.database_url.lower():
                # MySQL syntax
                check_query = text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'document_libraries'
                    AND COLUMN_NAME = 'is_default'
                """)
            else:
                # SQLite/PostgreSQL syntax (fallback)
                check_query = text("""
                    SELECT COUNT(*) as count
                    FROM pragma_table_info('document_libraries')
                    WHERE name = 'is_default'
                """)
            
            result = await session.execute(check_query)
            count = result.scalar() or 0
            
            if count > 0:
                print("✓ Column 'is_default' already exists. Skipping migration.")
                return
            
            # Add the column
            if "mysql" in settings.database_url.lower():
                # MySQL syntax
                alter_query = text("""
                    ALTER TABLE document_libraries
                    ADD COLUMN is_default BOOLEAN DEFAULT FALSE NOT NULL
                """)
            else:
                # SQLite/PostgreSQL syntax (fallback)
                alter_query = text("""
                    ALTER TABLE document_libraries
                    ADD COLUMN is_default BOOLEAN DEFAULT 0 NOT NULL
                """)
            
            await session.execute(alter_query)
            await session.commit()
            print("✓ Successfully added 'is_default' field to document_libraries table.")
            print("  All existing libraries have is_default=False by default.")
            
    except Exception as e:
        print(f"✗ Error adding is_default field: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

