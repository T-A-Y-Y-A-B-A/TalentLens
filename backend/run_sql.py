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
            WHERE c.email = 'tayyabathree@gmail.com'
            ORDER BY r.created_at DESC
            LIMIT 1;
        """))
        row = result.fetchone()
        print(row)

if __name__ == "__main__":
    asyncio.run(main())
