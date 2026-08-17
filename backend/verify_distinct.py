import asyncio
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.candidate import Candidate, Resume, ResumeParsedData

async def verify():
    # 1. Print compiled SQL
    stmt = (
        select(Candidate, ResumeParsedData.skills)
        .join(Resume, Resume.candidate_id == Candidate.id)
        .join(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
        .where(ResumeParsedData.skills != None)
        .distinct(Candidate.id)
        .order_by(Candidate.id, Resume.created_at.desc())
    )
    from sqlalchemy.dialects import postgresql
    print("--- COMPILED SQL ---")
    print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    
    # 2. Count candidates with multiple resumes
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(
            "SELECT candidate_id, COUNT(*) FROM resumes GROUP BY candidate_id HAVING COUNT(*) > 1;"
        ))
        rows = result.all()
        print("\n--- MULTIPLE RESUMES ---")
        if not rows:
            print("No candidates with multiple resumes found.")
        else:
            for row in rows:
                print(f"Candidate {row[0]}: {row[1]} resumes")

if __name__ == "__main__":
    asyncio.run(verify())
