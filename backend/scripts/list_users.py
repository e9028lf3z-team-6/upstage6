import asyncio
from app.core.db import get_session, User, init_db
from sqlalchemy import select

async def main():
    await init_db()
    async with get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"ID: {u.id} | Email: {u.email} | Name: {u.name}")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(main())
