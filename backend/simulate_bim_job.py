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
from app.models.identity import User

async def main():
    async with AsyncSessionLocal() as session:
        print("=== Registering new company ===")
        email = "bim_admin3@techinnovators.com"
        password = "Password123!"
        org_name = "Tech Innovators Inc 3"
        
        try:
            admin_user = await register_user(session, email, password, org_name)
            print(f"Registered User: {admin_user.email} for org: {admin_user.org_id}")
        except Exception as e:
            print(f"Error registering: {e}")
            from sqlalchemy.future import select
            res = await session.execute(select(User).where(User.email == email))
            admin_user = res.scalars().first()
            if not admin_user:
                print("Could not retrieve user!")
                return

        print("\n=== Creating Real Job (BIM Coordinator) ===")
        reqs = JobRequirements(
            required_skills=["Revit", "AutoCAD", "BIM coordinator", "MS Windows"],
            experience_years=3,
            education="BS Architecture"
        )
        job_in = JobCreate(
            title="Senior BIM Coordinator",
            description="Looking for an experienced BIM coordinator.",
            requirements=reqs,
            work_type=WorkType.HYBRID,
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
