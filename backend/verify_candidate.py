import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models.candidate import Candidate, CandidateEmbedding, Resume
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

async def verify():
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    async with async_session() as session:
        # Find candidate with qdrant_point_id = 55417291-492a-4533-ad60-0a0c8f704903
        suspect_point_id = "55417291-492a-4533-ad60-0a0c8f704903"
        res = await session.execute(
            select(CandidateEmbedding).where(CandidateEmbedding.qdrant_point_id == suspect_point_id)
        )
        emb = res.scalars().first()
        if not emb:
            print(f"No CandidateEmbedding found for {suspect_point_id}")
            return
            
        print(f"Found candidate embedding. Candidate ID: {emb.candidate_id}")
        
        res = await session.execute(
            select(Candidate).where(Candidate.id == emb.candidate_id).options(
                selectinload(Candidate.resumes).selectinload(Resume.parsed_data)
            )
        )
        suspect = res.scalars().first()
        
        if suspect and suspect.resume and suspect.resume.parsed_data:
            print(f"Parsed Data Experience: {suspect.resume.parsed_data.experience}")
        else:
            print("Candidate not found or missing parsed data.")

if __name__ == "__main__":
    asyncio.run(verify())
