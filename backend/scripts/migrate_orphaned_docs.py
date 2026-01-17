import asyncio
import sys
import os
from sqlalchemy import select, update

# Add backend to path
sys.path.append(os.getcwd())

from app.core.db import get_session, Document, init_db

async def main(target_user_id: str):
    print(f"Migrating orphaned documents to user: {target_user_id}")
    await init_db()
    
    async with get_session() as session:
        # Find orphaned docs
        stmt = select(Document).where(Document.user_id == None)
        result = await session.execute(stmt)
        docs = result.scalars().all()
        
        count = len(docs)
        print(f"Found {count} orphaned documents.")
        
        if count == 0:
            return

        # Update
        stmt = update(Document).where(Document.user_id == None).values(user_id=target_user_id)
        await session.execute(stmt)
        await session.commit()
        
        print(f"Successfully assigned {count} documents to {target_user_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_orphaned_docs.py <TARGET_USER_ID>")
        sys.exit(1)
    
    target_id = sys.argv[1]
    asyncio.run(main(target_id))
