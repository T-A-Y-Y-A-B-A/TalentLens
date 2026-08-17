import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.workers.tasks.keyword_matching import match_candidate_to_all_jobs

async def main(candidate_id: str):
    print(f"--- Debugging Candidate: {candidate_id} ---")
    
    # 1. Delete existing rows
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@postgres:5432/talentlens")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(
            text(f"DELETE FROM job_matches WHERE candidate_id = '{candidate_id}' RETURNING id")
        )
        deleted_ids = result.fetchall()
        await session.commit()
        print(f"Deleted {len(deleted_ids)} old job_matches rows for this candidate.")
    
    # 2. Trigger matching (runs synchronously)
    print("\nRunning matching synchronously...")
    from app.workers.tasks.keyword_matching import _match_candidate_to_all_jobs
    await _match_candidate_to_all_jobs(candidate_id)
    print("Matching complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: docker-compose exec backend python debug_matching.py <candidate_id>")
        sys.exit(1)
    
    candidate_id = sys.argv[1]
    asyncio.run(main(candidate_id))
