import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models.recruitment import Job
from app.models.candidate import Candidate, Resume
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

async def verify():
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    async with async_session() as session:
        # Count Jobs
        res = await session.execute(select(func.count(Job.id)))
        job_count = res.scalar()
        print(f"Total Jobs in Postgres: {job_count}")
        
        # Count Candidates
        res = await session.execute(select(func.count(Candidate.id)))
        cand_count = res.scalar()
        print(f"Total Candidates in Postgres: {cand_count}")
        
        # Analyze Candidate skips
        res = await session.execute(
            select(Candidate).options(
                selectinload(Candidate.resumes).selectinload(Resume.parsed_data)
            )
        )
        cands = res.scalars().all()
        
        no_resume = 0
        no_parsed_data = 0
        has_parsed_data = 0
        
        for c in cands:
            if not c.resume:
                no_resume += 1
            elif not c.resume.parsed_data:
                no_parsed_data += 1
            else:
                has_parsed_data += 1
                
        print(f"Candidates with no resume: {no_resume}")
        print(f"Candidates with resume but no parsed data: {no_parsed_data}")
        print(f"Candidates with parsed data (eligable for backfill): {has_parsed_data}")
        
        # Investigate Candidate 55417291-492a-4533-ad60-0a0c8f704903
        suspect_id = "55417291-492a-4533-ad60-0a0c8f704903"
        res = await session.execute(
            select(Candidate).where(Candidate.id == suspect_id).options(
                selectinload(Candidate.resumes).selectinload(Resume.parsed_data)
            )
        )
        suspect = res.scalars().first()
        if suspect and suspect.resume and suspect.resume.parsed_data:
            print(f"\nSuspect Candidate {suspect_id} Parsed Data:")
            print(f"  Titles: {suspect.resume.parsed_data.job_titles}")
            print(f"  Experience: {suspect.resume.parsed_data.experience}")
        else:
            print(f"\nSuspect Candidate {suspect_id} not found or has no parsed data.")

if __name__ == "__main__":
    asyncio.run(verify())
