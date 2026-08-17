import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("""
            SELECT c.id, u.email, r.id as resume_id, rpd.skills
            FROM candidates c
            JOIN users u ON u.id = c.id
            JOIN resumes r ON r.candidate_id = c.id
            JOIN resume_parsed_data rpd ON rpd.resume_id = r.id
        """))
        cands = res.all()
        for cand in cands:
            print(f"Cand ID: {cand.id}")
            print(f"Email: {cand.email}")
            print(f"Skills: {cand.skills}")
            print("---")

if __name__ == "__main__":
    asyncio.run(main())
