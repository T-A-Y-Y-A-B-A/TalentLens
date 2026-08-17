import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def update_jobs():
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            UPDATE jobs 
            SET requirements = jsonb_set(
                COALESCE(requirements, '{}'::jsonb), 
                '{required_skills}', 
                '["Python", "FastAPI", "SQL", "React", "TypeScript"]'::jsonb
            )
        """))
        await session.commit()
        print("Jobs updated with mock required_skills.")

if __name__ == "__main__":
    asyncio.run(update_jobs())
