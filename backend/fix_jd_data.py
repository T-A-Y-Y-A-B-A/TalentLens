import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update
from app.models.recruitment import Job
from dotenv import load_dotenv
load_dotenv()

async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/talentlens")
    # For railway proxy, ensure ssl
    if "railway.internal" not in db_url and "localhost" not in db_url and "127.0.0.1" not in db_url:
        if "?" not in db_url:
            db_url += "?ssl=require"
        
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        jobs = (await session.execute(select(Job))).scalars().all()
        print(f"Found {len(jobs)} jobs. Fixing JD data...")
        
        for job in jobs:
            updated = False
            
            for field in ["key_responsibilities", "expectations", "benefits"]:
                val = getattr(job, field)
                
                # val might be a dict {'error': 'invalid json', 'raw': '...'} because of JSONType
                if isinstance(val, dict) and "raw" in val:
                    raw_str = val["raw"]
                elif isinstance(val, str):
                    raw_str = val
                else:
                    continue
                    
                # Convert bullet points string into a list of strings
                lines = [line.strip().lstrip("-").strip() for line in raw_str.split("\n") if line.strip()]
                
                setattr(job, field, lines)
                updated = True
                
            if updated:
                session.add(job)
                print(f"Updated job {job.id}")
                
        await session.commit()
        print("Done!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
