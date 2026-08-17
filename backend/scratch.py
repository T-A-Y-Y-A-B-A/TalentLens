import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Job))
        jobs = res.scalars().all()
        has_reqs = [j for j in jobs if j.requirements]
        print('Total Jobs:', len(jobs))
        print('Jobs with reqs:', len(has_reqs))
        for j in has_reqs:
            print(f"ID: {j.id}, Reqs: {j.requirements}")

if __name__ == "__main__":
    asyncio.run(check())
