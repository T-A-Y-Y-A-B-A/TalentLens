import asyncio
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.models.recruitment import Job, JobStatus
from sqlalchemy import select
from app.services.matching import compute_job_embeddings
from app.workers.tasks.keyword_matching import _match_job_to_all_candidates
import logging

logging.basicConfig(level=logging.INFO)

async def sync():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.status == JobStatus.OPEN))
        jobs = result.scalars().all()
        
        print(f"Syncing embeddings and matches for {len(jobs)} jobs...")
        for i, job in enumerate(jobs):
            print(f"[{i+1}/{len(jobs)}] Syncing Job {job.id}...")
            # Compute embedding
            await compute_job_embeddings(session, job)
            # Recompute matches
            await _match_job_to_all_candidates(str(job.id))
            
    print("Done!")

if __name__ == "__main__":
    asyncio.run(sync())
