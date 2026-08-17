import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.recruitment import Job, JobStatus, WorkType
import uuid

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@postgres:5432/talentlens")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import text
        result = await session.execute(text("SELECT id FROM organizations LIMIT 1"))
        org_id_row = result.fetchone()
        
        if not org_id_row:
            dummy_org = uuid.uuid4()
            await session.execute(text(f"INSERT INTO organizations (id, name, created_at, updated_at) VALUES ('{dummy_org}', 'Test Org', now(), now())"))
            await session.commit()
        else:
            dummy_org = org_id_row[0]
        
        new_job = Job(
            org_id=dummy_org,
            title="Test Location Job",
            description="Testing location",
            work_type=WorkType.REMOTE,
            status=JobStatus.DRAFT,
            location="Lahore, Pakistan"
        )
        session.add(new_job)
        await session.commit()
        
        print(f"Inserted Job ID: {new_job.id}")
        
        stmt = select(Job).where(Job.id == new_job.id)
        result = await session.execute(stmt)
        saved_job = result.scalar_one()
        
        print(f"SUCCESS: Queried Job Location = {saved_job.location}")
        
        await session.delete(saved_job)
        await session.commit()
        print("Cleaned up test job.")

if __name__ == "__main__":
    asyncio.run(main())
