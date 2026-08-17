import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT title, description FROM jobs LIMIT 10;"))
        for r in res.all():
            print(f"Title: {r.title}")
            print(f"Description: {r.description[:200]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
