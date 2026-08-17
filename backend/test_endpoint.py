import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from app.core.database import AsyncSessionLocal
from app.api.v1.candidate_auth import get_candidate_jobs
from app.models.candidate import Candidate
from uuid import UUID

async def main():
    async with AsyncSessionLocal() as session:
        # Get a real candidate
        from sqlalchemy import text
        res = await session.execute(text("SELECT id FROM candidates LIMIT 1"))
        cand_id = res.scalar()
        if not cand_id:
            print("No candidate found.")
            return
            
        class MockCandidate:
            id = cand_id
            
        print(f"Testing with candidate ID: {cand_id}")
        
        try:
            # We need to simulate the Depends
            result = await get_candidate_jobs(org_id=None, db=session, current_candidate=MockCandidate())
            print(f"Result count: {len(result)}")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
