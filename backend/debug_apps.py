import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT id, candidate_id, org_id FROM applications WHERE candidate_id = '7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4'
        """))
        print("Applications:")
        for row in result.all():
            print(row)
            
        result = await session.execute(text("""
            SELECT profile FROM candidates WHERE id = '7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4'
        """))
        print("\nCandidate Profile:")
        print(result.fetchone())

if __name__ == "__main__":
    asyncio.run(main())
