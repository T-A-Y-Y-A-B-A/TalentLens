import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
import json
from fastapi.encoders import jsonable_encoder
from app.core.database import AsyncSessionLocal
from app.api.v1.candidate_auth import get_candidate_jobs
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id FROM candidates LIMIT 1"))
        cand_id = res.scalar()
        
        class MockCandidate:
            id = cand_id
            
        try:
            result = await get_candidate_jobs(org_id=None, db=session, current_candidate=MockCandidate())
            # Try to JSON encode it exactly as FastAPI would
            encoded = jsonable_encoder(result)
            json_str = json.dumps(encoded)
            print(f"Successfully encoded {len(result.get('jobs', []))} jobs.")
            # Print the first job to see what it looks like
            if result.get('jobs'):
                print(json.dumps(encoded['jobs'][0], indent=2))
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
