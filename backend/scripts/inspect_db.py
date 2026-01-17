import asyncio
import json
from sqlalchemy import select
from app.core.db import init_db, get_session, Document

async def main():
    await init_db()
    async with get_session() as session:
        result = await session.execute(select(Document).limit(3))
        docs = result.scalars().all()
        for d in docs:
            print(f"Doc ID: {d.id}")
            print(f"Meta JSON: {d.meta_json}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
