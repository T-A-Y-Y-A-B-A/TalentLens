import asyncio
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.workers.tasks.keyword_matching import match_candidate_to_all_jobs
import logging
from sqlalchemy import text
import sys

logging.basicConfig(level=logging.INFO)
logging.getLogger("app.api.v1.matching").setLevel(logging.DEBUG)

async def test():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session() as s:
        res = await s.execute(text("SELECT id FROM candidates WHERE email='padded.demo@example.com'"))
        cid = res.scalar()
        
    print(f"Padded Candidate ID: {cid}")
    match_candidate_to_all_jobs(str(cid))

if __name__ == "__main__":
    asyncio.run(test())
