import asyncio
from sqlalchemy import select
from app.core.config import settings
from app.models.recruitment import Job, JobStatus
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.identity import User
from app.services.matching import compute_candidate_embeddings
from app.workers.tasks.keyword_matching import match_candidate_to_all_jobs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import json

async def seed():
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    async with async_session() as session:
        # Get a job
        res = await session.execute(
            select(Job).where(Job.status == JobStatus.OPEN).limit(1)
        )
        job = res.scalars().first()
        if not job:
            print("No open jobs found.")
            return
            
        print(f"Targeting Job: {job.title}")
        reqs = job.requirements if isinstance(job.requirements, dict) else job.requirements.model_dump()
        skills = reqs.get("required_skills", [])
        
        # 1. Padded Candidate (Mismatched Experience)
        padded_cand = Candidate(
            name="Alice The Padded",
            email="alice.padded@example.com",
            phone="555-0100"
        )
        session.add(padded_cand)
        await session.flush()
        
        padded_resume = Resume(
            candidate_id=padded_cand.id,
            file_url="mock/padded.pdf",
            parse_status="done"
        )
        session.add(padded_resume)
        await session.flush()
        
        padded_parsed = ResumeParsedData(
            resume_id=padded_resume.id,
            skills=skills, # 100% keyword match
            experience=[
                {
                    "title": "Senior Barista",
                    "company": "Local Cafe",
                    "start_date": "2020-01-01",
                    "end_date": "2023-01-01",
                    "description": "Served coffee and managed the register. Delivered excellent customer service to morning commuters."
                },
                {
                    "title": "Professional Dog Walker",
                    "company": "Self-employed",
                    "start_date": "2018-01-01",
                    "end_date": "2020-01-01",
                    "description": "Walked dogs around the neighborhood. Ensured animals were safe and exercised."
                }
            ],
            education=[{"degree": "High School Diploma"}]
        )
        session.add(padded_parsed)
        
        # 2. Strong Candidate (Legit Experience)
        strong_cand = Candidate(
            name="Bob The Legit",
            email="bob.legit@example.com",
            phone="555-0200"
        )
        session.add(strong_cand)
        await session.flush()
        
        strong_resume = Resume(
            candidate_id=strong_cand.id,
            file_url="mock/strong.pdf",
            parse_status="done"
        )
        session.add(strong_resume)
        await session.flush()
        
        strong_parsed = ResumeParsedData(
            resume_id=strong_resume.id,
            skills=skills, # 100% keyword match
            experience=[
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "start_date": "2019-01-01",
                    "end_date": "2023-01-01",
                    "description": "Architected and deployed scalable backend microservices using Python, FastAPI, and Docker on AWS. Led a team of 5 engineers to migrate legacy monolithic systems to a modern distributed architecture. Designed and implemented robust CI/CD pipelines, optimized PostgreSQL database queries, and collaborated with cross-functional teams to deliver high-quality software on time."
                }
            ],
            education=[{"degree": "B.S. Computer Science"}]
        )
        session.add(strong_parsed)
        
        await session.commit()
        
        # Compute embeddings for both
        await compute_candidate_embeddings(session, padded_cand, padded_parsed, collection_name="candidates")
        await compute_candidate_embeddings(session, strong_cand, strong_parsed, collection_name="candidates")
        
        print(f"Created Padded Candidate: {padded_cand.id}")
        print(f"Created Strong Candidate: {strong_cand.id}")
        
    # Trigger matching for both synchronously
    print("\nMatching padded candidate...")
    match_candidate_to_all_jobs(str(padded_cand.id))
    print("Matching strong candidate...")
    match_candidate_to_all_jobs(str(strong_cand.id))
    
if __name__ == "__main__":
    asyncio.run(seed())
