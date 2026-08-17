import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT COUNT(*) FROM resume_parsed_data"))
        count = res.scalar()
        print(f"Total parsed resumes: {count}")

        if count > 0:
            res = await session.execute(text("SELECT id, resume_id, skills FROM resume_parsed_data LIMIT 5"))
            rows = res.all()
            for r in rows:
                print(r)

if __name__ == "__main__":
    asyncio.run(main())
