import asyncio
import logging
import structlog
import os
from dotenv import load_dotenv
load_dotenv()

from app.workers.tasks.resume_parser import async_parse_resume
from app.core.database import AsyncSessionLocal, engine
from app.models.candidate import Resume
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
)

async def main():
    async with AsyncSessionLocal() as db:
        # Reset all FAILED resumes to PENDING
        from sqlalchemy import update
        await db.execute(update(Resume).where(Resume.parse_status == 'FAILED').values(parse_status='PENDING'))
        await db.commit()
        
        # Find a pending resume
        result = await db.execute(select(Resume).where(Resume.parse_status == 'PENDING').limit(1))
        resume = result.scalars().first()
        if not resume:
            print("No pending resumes found.")
            await engine.dispose()
            return
        
        resume_id = str(resume.id)
        print(f"Testing resume_parser on Resume ID: {resume_id}")
    
    try:
        await async_parse_resume(resume_id)
        
        async with AsyncSessionLocal() as db:
            from app.models.candidate import ResumeParsedData
            result = await db.execute(select(ResumeParsedData).where(ResumeParsedData.resume_id == resume_id))
            parsed = result.scalars().first()
            if parsed:
                print("\n\n====== PARSED DATA ======")
                import json
                print(json.dumps({
                    "skills": parsed.skills,
                    "experience": parsed.experience,
                    "education": parsed.education,
                    "projects": parsed.projects
                }, indent=2))
                print("=========================\n\n")
            else:
                print("No parsed data found in DB!")
    finally:
        await engine.dispose()
        
if __name__ == "__main__":
    asyncio.run(main())
