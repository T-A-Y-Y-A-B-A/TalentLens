import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        c_ids = ['7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4', 'e41c8d81-5ceb-4009-b614-186367872e8b']
        for cid in c_ids:
            res = await session.execute(text("SELECT email FROM users WHERE id = :id"), {"id": cid})
            user = res.first()
            if user:
                print(f"Candidate {cid} exists in users! Email: {user.email}")
            else:
                print(f"Candidate {cid} does NOT exist in users!")

if __name__ == "__main__":
    asyncio.run(main())
