import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.recruitment import Job
from app.models.candidate import ResumeParsedData

async def main():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        # Check 3-5 Jobs for requirements format
        print("--- JOBS: REQUIREMENTS SHAPE ---")
        result = await session.execute(select(Job).limit(5))
        jobs = result.scalars().all()
        for job in jobs:
            print(f"Job {job.id}: {type(job.requirements)} - {job.requirements}")
            
        print("\n--- RESUMES: DATE FORMAT ---")
        res_result = await session.execute(select(ResumeParsedData).limit(5))
        resumes = res_result.scalars().all()
        for res in resumes:
            for exp in (res.experience or []):
                print(f"Resume {res.id}, Exp: {exp.get('start_date')} -> {exp.get('end_date')}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
