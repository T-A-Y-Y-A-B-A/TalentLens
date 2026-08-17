import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Get the latest job to find <new org id> and <job id>
        print("=== LATEST JOB ===")
        res_job = await session.execute(text("""
            SELECT id, title, status, work_type, requirements, org_id, created_at
            FROM jobs
            ORDER BY created_at DESC LIMIT 1;
        """))
        job = res_job.first()
        if not job:
            print("No jobs found!")
            return
            
        print(f"Job ID: {job.id}")
        print(f"Title: {job.title}")
        print(f"Status: {job.status}")
        print(f"Work Type: {job.work_type}")
        print(f"Requirements: {job.requirements}")
        print(f"Org ID: {job.org_id}")
        print(f"Created At: {job.created_at}")
        
        # 2. Check JobMatch rows for this job
        print("\n=== JOB MATCHES FOR LATEST JOB ===")
        res_matches = await session.execute(text("""
            SELECT job_id, candidate_id, match_pct, missing_skills
            FROM job_matches
            WHERE job_id = :job_id;
        """), {"job_id": job.id})
        matches = res_matches.all()
        print(f"Found {len(matches)} matches")
        for m in matches:
            print(f"Candidate: {m.candidate_id}, Match %: {m.match_pct}, Missing: {m.missing_skills}")

        # 3. Get the latest candidate (or all candidates if few)
        print("\n=== CANDIDATES & RESUMES ===")
        res_cands = await session.execute(text("""
            SELECT c.id, r.id as resume_id, rpd.skills
            FROM candidates c
            LEFT JOIN resumes r ON r.candidate_id = c.id
            LEFT JOIN resume_parsed_data rpd ON rpd.resume_id = r.id
            ORDER BY c.created_at DESC LIMIT 5;
        """))
        cands = res_cands.all()
        for c in cands:
            print(f"Candidate ID: {c.id}")
            print(f"Resume ID: {c.resume_id}")
            print(f"Skills: {c.skills}")
            print("---")

if __name__ == "__main__":
    asyncio.run(main())
