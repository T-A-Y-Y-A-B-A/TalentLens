import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT r.id, r.created_at, r.parse_status, rpd.id as parsed_id, rpd.skills
            FROM resumes r
            LEFT JOIN resume_parsed_data rpd ON rpd.resume_id = r.id
            WHERE r.candidate_id = '7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4'
            ORDER BY r.created_at DESC
        """))
        for row in result.all():
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
