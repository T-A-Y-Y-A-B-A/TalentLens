import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.recruitment import Job
from app.services.matching import compute_job_embeddings
from app.core.qdrant import qdrant_client
import sys

async def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_phase2.py <job_id>")
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
            
        print("Computing embeddings... (this might take a few minutes if downloading model weights)")
        emb = await compute_job_embeddings(session, job)
        print(f"Generated/Updated JobEmbedding row with point_id: {emb.qdrant_point_id}")
        
        print("Querying Qdrant for vectors...")
        # Get point from qdrant
        points = await qdrant_client.retrieve(
            collection_name="jobs",
            ids=[emb.qdrant_point_id],
            with_vectors=True
        )
        if points:
            point = points[0]
            if isinstance(point.vector, dict):
                print("Vectors found on point:")
                for vec_name in point.vector.keys():
                    print(f"  - {vec_name}")
            else:
                print("Vector is not a dict (named vectors).")
        else:
            print("Point not found in Qdrant.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
