import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job

async def run():
    async with AsyncSessionLocal() as session:
        jobs = (await session.execute(select(Job.id, Job.title, Job.description))).all()
        for j in jobs:
            print(f"{j[0]}|{j[1]}")

if __name__ == "__main__":
    asyncio.run(run())
