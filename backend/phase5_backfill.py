import asyncio
import uuid
import random
from sqlalchemy import select
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, PayloadSchemaType
from app.core.config import settings
from app.core.qdrant import qdrant_client
from app.models.recruitment import Job
from app.models.candidate import Candidate, ResumeParsedData
from app.services.matching import compute_job_embeddings, compute_candidate_embeddings

async def backfill():
    collections = await qdrant_client.get_collections()
    collection_names = [c.name for c in collections.collections]

    print("--- 1. Creating v2 Collections ---")
    if "jobs_v2" not in collection_names:
        print("Creating jobs_v2...")
        await qdrant_client.create_collection(
            collection_name="jobs_v2",
            vectors_config={
                "dense": VectorParams(size=384, distance=Distance.COSINE),
                "responsibilities_vec": VectorParams(size=384, distance=Distance.COSINE),
                "requirements_vec": VectorParams(size=384, distance=Distance.COSINE),
                "expectations_vec": VectorParams(size=384, distance=Distance.COSINE),
            }
        )
    
    if "candidates_v2" not in collection_names:
        print("Creating candidates_v2...")
        await qdrant_client.create_collection(
            collection_name="candidates_v2",
            vectors_config={
                "dense": VectorParams(size=384, distance=Distance.COSINE),
                "experience_vec": VectorParams(size=384, distance=Distance.COSINE),
                "titles_vec": VectorParams(size=384, distance=Distance.COSINE),
            }
        )
        await qdrant_client.create_payload_index(
            collection_name="candidates_v2",
            field_name="org_ids",
            field_schema=PayloadSchemaType.KEYWORD
        )
        
    print("--- 2. Running Backfill ---")
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import func
        # Jobs
        res = await session.execute(select(func.count(Job.id)))
        total_pg_jobs = res.scalar()
        
        res = await session.execute(select(Job))
        jobs = res.scalars().all()
        print(f"Found {len(jobs)} jobs to backfill.")
        for j in jobs:
            await compute_job_embeddings(session, j, collection_name="jobs_v2")
        from sqlalchemy.orm import selectinload
        from app.models.candidate import Resume
        res = await session.execute(
            select(Candidate).options(
                selectinload(Candidate.resumes).selectinload(Resume.parsed_data)
            )
        )
        cands = res.scalars().all()
        print(f"Found {len(cands)} total candidates in Postgres.")
        
        pg_cands_eligible = 0
        for c in cands:
            if c.resume and c.resume.parsed_data:
                pg_cands_eligible += 1
                await compute_candidate_embeddings(session, c, c.resume.parsed_data, collection_name="candidates_v2")
                
        print(f"  -> {pg_cands_eligible} have parsed resume data and were backfilled.")
        print(f"  -> {len(cands) - pg_cands_eligible} were skipped (no resume or parsing failed).")

    print("\n--- 3. Verification Gate (Counts) ---")
    # Old counts
    j_count = (await qdrant_client.count(collection_name="jobs")).count
    # New counts
    j_v2_count = (await qdrant_client.count(collection_name="jobs_v2")).count
    c_v2_count = (await qdrant_client.count(collection_name="candidates_v2")).count
    
    print(f"Jobs: Postgres ({total_pg_jobs}) -> Qdrant_v2 ({j_v2_count}) {'(PASS)' if total_pg_jobs == j_v2_count else '(FAIL)'}")
    print(f"Candidates: Postgres Eligible ({pg_cands_eligible}) -> Qdrant_v2 ({c_v2_count}) {'(PASS)' if pg_cands_eligible == c_v2_count else '(FAIL)'}")
    
    print("\n--- 4. Spot Check Named Vectors ---")
    if j_v2_count > 0:
        j_points, _ = await qdrant_client.scroll(collection_name="jobs_v2", limit=5, with_vectors=True)
        print("Jobs v2 Spot Check:")
        for p in j_points:
            vecs = p.vector.keys() if hasattr(p.vector, "keys") else p.vector
            print(f"  Point {p.id}: {vecs}")
            
    if c_v2_count > 0:
        c_points, _ = await qdrant_client.scroll(collection_name="candidates_v2", limit=5, with_vectors=True)
        print("\nCandidates v2 Spot Check:")
        for p in c_points:
            vecs = p.vector.keys() if hasattr(p.vector, "keys") else p.vector
            print(f"  Point {p.id}: {vecs}")

if __name__ == "__main__":
    asyncio.run(backfill())
