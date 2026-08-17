import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        # Verify candidate is test candidate (should be test_candidate@example.com from previous turns)
        c_id = 'd29f41e3-6920-4174-b2c6-5f4ac02055c8'
        res = await session.execute(text("SELECT email FROM users WHERE id = :id"), {"id": c_id})
        user = res.first()
        print(f"Candidate Email: {user.email if user else 'Not found'}")
        
        # Verify job is the test job
        j_id = '46373f96-9709-4bc8-985b-309e6d275f4f'
        res2 = await session.execute(text("SELECT title FROM jobs WHERE id = :id"), {"id": j_id})
        job = res2.first()
        print(f"Job Title: {job.title if job else 'Not found'}")

        print("Executing cleanup...")
        await session.execute(text("DELETE FROM job_matches WHERE job_id = :j_id"), {"j_id": j_id})
        await session.execute(text("DELETE FROM pipeline_stages WHERE job_id = :j_id"), {"j_id": j_id})
        await session.execute(text("DELETE FROM jobs WHERE id = :j_id"), {"j_id": j_id})
        
        # Also clean up the organization 'Zee Company' if it was a test org, but I'll leave it unless specified.
        
        # Note: resume_parsed_data id is usually the resume_id itself since we modified it or the resume_id FK
        # Wait, the user query said DELETE FROM resume_parsed_data WHERE id = ... wait, it's resume_id
        await session.execute(text("DELETE FROM resume_parsed_data WHERE resume_id = '7c4a6663-7418-4ef5-bc79-39c45628f23a'"))
        await session.execute(text("DELETE FROM resumes WHERE candidate_id = :c_id"), {"c_id": c_id})
        await session.execute(text("DELETE FROM candidates WHERE id = :c_id"), {"c_id": c_id})
        await session.execute(text("DELETE FROM users WHERE id = :c_id"), {"c_id": c_id})
        
        await session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
