import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT c.id, c.email, rpd.skills, c.profile->>'experience_years' as experience_years
            FROM candidates c
            LEFT JOIN resumes r ON r.candidate_id = c.id
            LEFT JOIN resume_parsed_data rpd ON rpd.resume_id = r.id
            ORDER BY r.created_at DESC
        """))
        for row in result.all():
            print(f"ID: {row.id}")
            print(f"Email: {row.email}")
            print(f"Skills: {row.skills}")
            print(f"Exp: {row.experience_years}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
