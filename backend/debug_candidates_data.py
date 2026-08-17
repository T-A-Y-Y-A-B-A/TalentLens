import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.candidate import Candidate, Resume, ResumeParsedData
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as session:
        candidates_data = (await session.execute(
            select(Candidate.id, ResumeParsedData.skills)
            .join(Resume, Resume.candidate_id == Candidate.id)
            .join(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
            .where(ResumeParsedData.skills != None)
            .distinct(Candidate.id)
            .order_by(Candidate.id, Resume.created_at.desc())
        )).all()
        print(f"Number of candidates fetched: {len(candidates_data)}")
        for c in candidates_data:
            print(f"{c.id}: {c.skills}")

if __name__ == "__main__":
    asyncio.run(main())
