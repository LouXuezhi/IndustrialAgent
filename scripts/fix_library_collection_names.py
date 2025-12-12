#!/usr/bin/env python
"""
Fix vector_collection_name for existing libraries.

This script updates vector_collection_name to use library.id instead of owner_id
for all existing libraries.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import async_session
from app.db.models import DocumentLibrary


async def fix_collection_names():
    """Update vector_collection_name for all libraries."""
    async with async_session() as session:
        # Get all libraries
        result = await session.execute(select(DocumentLibrary))
        libraries = result.scalars().all()
        
        if not libraries:
            print("No libraries found.")
            return
        
        print(f"Found {len(libraries)} libraries.")
        updated_count = 0
        
        for library in libraries:
            # Expected collection name based on library.id
            expected_name = f"library_{library.id}"
            
            # Current collection name
            current_name = library.vector_collection_name
            
            if current_name != expected_name:
                print(f"\nUpdating library: {library.name}")
                print(f"  ID: {library.id}")
                print(f"  Current collection name: {current_name}")
                print(f"  Expected collection name: {expected_name}")
                
                library.vector_collection_name = expected_name
                updated_count += 1
            else:
                print(f"✓ Library {library.name} already has correct collection name")
        
        if updated_count > 0:
            await session.commit()
            print(f"\n✓ Updated {updated_count} libraries.")
            print("\n⚠️  Note: Documents vectorized before this fix may be in the old collection.")
            print("   You may need to re-vectorize documents in affected libraries.")
        else:
            print("\n✓ All libraries already have correct collection names.")


if __name__ == "__main__":
    asyncio.run(fix_collection_names())

