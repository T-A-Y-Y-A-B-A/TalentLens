import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.candidate import Candidate, ResumeParsedData
from app.core.qdrant import qdrant_client
from app.ai.embeddings import embed_text
from qdrant_client.models import PointStruct
import uuid
import sys

async def verify_sync_embedding(session, candidate_id: str, test_name: str, exp_data: list):
    print(f"\n--- Testing Scenario: {test_name} ---")
    result = await session.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalars().first()
    
    if not candidate:
        print("Candidate not found")
        return
        
    print(f"Candidate found: {candidate.name}")
    
    # Mock ResumeParsedData
    resume_data = ResumeParsedData(
        experience=exp_data
    )
    
    exp_bullets = []
    exp_titles = []
    
    if resume_data and resume_data.experience:
        for job in resume_data.experience:
            if isinstance(job, dict):
                title = job.get("title")
                if title: exp_titles.append(title)
                bullets = job.get("description")
                if isinstance(bullets, list):
                    exp_bullets.extend(bullets)
                elif isinstance(bullets, str):
                    exp_bullets.append(bullets)
                
    exp_text = " ".join(exp_bullets).strip()
    titles_text = " ".join(exp_titles).strip()
    
    print(f"Extracted titles_text: '{titles_text}'")
    print(f"Extracted exp_text: '{exp_text}'")
    
    experience_vec = embed_text(exp_text) if exp_text else None
    titles_vec = embed_text(titles_text) if titles_text else None
    
    dense_text = f"{candidate.name} {titles_text} {exp_text}".strip()
    dense_vec = embed_text(dense_text)
    
    vectors = {}
    if experience_vec: vectors["experience_vec"] = experience_vec
    if titles_vec: vectors["titles_vec"] = titles_vec
    vectors["dense"] = dense_vec
    
    point_id = str(uuid.uuid4())
    
    print(f"Upserting to Qdrant with point_id: {point_id}")
    await qdrant_client.upsert(
        collection_name="candidates",
        points=[
            PointStruct(
                id=point_id,
                vector=vectors,
                payload={"candidate_id": str(candidate.id)}
            )
        ]
    )
    
    print("Querying Qdrant for vectors...")
    points = await qdrant_client.retrieve(
        collection_name="candidates",
        ids=[point_id],
        with_vectors=True
    )
    if points:
        point = points[0]
        if isinstance(point.vector, dict):
            print("Vectors found on point:")
            for vec_name, vec_values in point.vector.items():
                dim = len(vec_values)
                sample = vec_values[:3]
                is_zero = all(v == 0.0 for v in vec_values)
                print(f"  - {vec_name}: dimension={dim}, all_zero={is_zero}, sample={[round(x, 4) for x in sample]}")
        else:
            print("Vector is not a dict (named vectors).")
    else:
        print("Point not found in Qdrant.")
        

async def main():
    candidate_id = sys.argv[1] if len(sys.argv) > 1 else None
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        if not candidate_id:
            res = await session.execute(select(Candidate).limit(1))
            cand = res.scalars().first()
            if not cand:
                print("No candidates in DB")
                return
            candidate_id = str(cand.id)
            
        # Scenario 1: Normal with both titles and bullets
        exp_full = [
            {"title": "Senior Engineer", "description": ["Did some python", "Led a team"]},
            {"title": "Junior Engineer", "description": "Fixed bugs"}
        ]
        await verify_sync_embedding(session, candidate_id, "Full Experience", exp_full)
        
        # Scenario 2: Titles only, no bullets
        exp_titles_only = [
            {"title": "CTO"},
            {"title": "VP of Engineering"}
        ]
        await verify_sync_embedding(session, candidate_id, "Titles Only (Empty Bullets)", exp_titles_only)
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
