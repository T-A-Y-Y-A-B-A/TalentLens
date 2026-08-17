import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id, title FROM jobs WHERE title = 'Senior BIM Coordinator' ORDER BY created_at DESC LIMIT 1"))
        job = res.first()
        if not job:
            return
            
        print(f"Job: {job.title} ({job.id})")
        
        res2 = await session.execute(text("""
            SELECT candidate_id, match_pct, missing_skills
            FROM job_matches
            WHERE job_id = :j_id
            ORDER BY match_pct DESC
        """), {"j_id": job.id})
        
        matches = res2.all()
        print(f"Total Matches: {len(matches)}")
        for m in matches:
            print(f"Cand: {m.candidate_id} | Match %: {m.match_pct} | Missing: {m.missing_skills}")

if __name__ == "__main__":
    asyncio.run(main())
