import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.auth import register_user
from app.services.recruitment import create_job
from app.schemas.recruitment import JobCreate, JobRequirements, WorkType
from app.workers.tasks.keyword_matching import _match_job_to_all_candidates

async def main():
    async with AsyncSessionLocal() as session:
        print("=== Registering new company ===")
        email = "admin@techinnovators.com"
        password = "Password123!"
        org_name = "Tech Innovators Inc"
        
        try:
            admin_user = await register_user(session, email, password, org_name)
            print(f"Registered User: {admin_user.email} for org: {admin_user.org_id}")
        except Exception as e:
            print(f"Error registering: {e}")
            from app.models.identity import User
            from sqlalchemy.future import select
            res = await session.execute(select(User).where(User.email == email))
            admin_user = res.scalars().first()

        print("\n=== Creating Real Job ===")
        reqs = JobRequirements(
            required_skills=["Python", "React", "SQL", "FastAPI", "PostgreSQL"],
            experience_years=3,
            education="BS Computer Science"
        )
        job_in = JobCreate(
            title="Senior Full Stack Engineer",
            description="Looking for an experienced engineer to build amazing stuff.",
            requirements=reqs,
            work_type=WorkType.REMOTE,
            status="open"
        )
        
        job = await create_job(session, job_in, admin_user)
        print(f"Created Job: {job.title} ({job.id})")
        
        print("\n=== Running Job Matcher ===")
        await _match_job_to_all_candidates(str(job.id))
        print("Matching complete.")
        
        print("\n=== Job Matches ===")
        res = await session.execute(text("""
            SELECT jm.candidate_id, u.email, jm.match_pct, jm.missing_skills
            FROM job_matches jm
            JOIN users u ON u.id = jm.candidate_id
            WHERE jm.job_id = :j_id
            ORDER BY jm.match_pct DESC
            LIMIT 10
        """), {"j_id": job.id})
        matches = res.all()
        for m in matches:
            print(f"Cand: {m.email} | Match %: {m.match_pct} | Missing: {m.missing_skills}")
            
if __name__ == "__main__":
    asyncio.run(main())
