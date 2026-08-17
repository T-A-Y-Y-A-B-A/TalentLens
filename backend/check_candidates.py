import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT COUNT(*) FROM candidates"))
        c_count = res.scalar()
        print(f"Candidates count: {c_count}")
        
        res = await session.execute(text("SELECT COUNT(*) FROM users"))
        u_count = res.scalar()
        print(f"Users count: {u_count}")

if __name__ == "__main__":
    asyncio.run(main())
