import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.recruitment import Job
from app.core.qdrant import qdrant_client
from app.ai.embeddings import embed_text
from qdrant_client.models import PointStruct
import uuid
import sys

async def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_phase2_sync.py <job_id>")
        return
        
    job_id = sys.argv[1]
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalars().first()
        
        if not job:
            print("Job not found")
            return
            
        print("Computing real embeddings synchronously... (may take a minute to download BAAI weights)")
        # Run embed_text directly, no run_in_executor
        resp_text = " ".join(job.key_responsibilities) if job.key_responsibilities else ""
        req_text = " ".join(job.requirements.get("required_skills", [])) if job.requirements else ""
        exp_text = " ".join(job.expectations) if job.expectations else ""
        
        responsibilities_vec = embed_text(resp_text) if resp_text else None
        requirements_vec = embed_text(req_text) if req_text else None
        expectations_vec = embed_text(exp_text) if exp_text else None
        dense_vec = embed_text(f"{job.title} {job.description} {resp_text} {req_text}")
        
        vectors = {}
        if responsibilities_vec: vectors["responsibilities_vec"] = responsibilities_vec
        if requirements_vec: vectors["requirements_vec"] = requirements_vec
        if expectations_vec: vectors["expectations_vec"] = expectations_vec
        vectors["dense"] = dense_vec
        
        point_id = str(uuid.uuid4())
        
        print(f"Upserting to Qdrant with point_id: {point_id}")
        await qdrant_client.upsert(
            collection_name="jobs",
            points=[
                PointStruct(
                    id=point_id,
                    vector=vectors,
                    payload={"job_id": str(job.id), "org_id": str(job.org_id)}
                )
            ]
        )
        
        print("Querying Qdrant for vectors...")
        points = await qdrant_client.retrieve(
            collection_name="jobs",
            ids=[point_id],
            with_vectors=True
        )
        if points:
            point = points[0]
            if isinstance(point.vector, dict):
                print("Vectors found on point:")
                for vec_name, vec_values in point.vector.items():
                    # Check dimension and non-zero
                    dim = len(vec_values)
                    sample = vec_values[:3]
                    is_zero = all(v == 0.0 for v in vec_values)
                    print(f"  - {vec_name}: dimension={dim}, all_zero={is_zero}, sample={[round(x, 4) for x in sample]}")
            else:
                print("Vector is not a dict (named vectors).")
        else:
            print("Point not found in Qdrant.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
