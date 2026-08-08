import asyncio
import sys
import os
import uuid
import structlog

# Ensure the app context is available
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.candidate import Candidate, CandidateEmbedding
from app.core.qdrant import qdrant_client
from qdrant_client.http.models import PointStruct

logger = structlog.get_logger()

async def mock_qdrant_data():
    logger.info("Mocking Qdrant data for backfill testing...")
    
    async with AsyncSessionLocal() as db:
        # Get all candidates
        result = await db.execute(select(Candidate))
        candidates = result.scalars().all()
        
        if not candidates:
            logger.error("No candidates found in DB. Run seed.py first.")
            return
            
        for candidate in candidates:
            point_id = str(uuid.uuid4())
            
            # Create CandidateEmbedding in Postgres
            embedding = CandidateEmbedding(
                candidate_id=candidate.id,
                qdrant_point_id=point_id,
                model_version="bge-small-en-v1.5"
            )
            db.add(embedding)
            
            # Upsert directly to Qdrant with an empty/old payload (to simulate the leak)
            # We give it a dummy 384-dimensional vector
            dummy_vector = [0.1] * 384
            await qdrant_client.upsert(
                collection_name="candidates",
                points=[
                    PointStruct(
                        id=point_id,
                        vector={
                            "dense": dummy_vector,
                            "sparse": {"indices": [1, 2, 3], "values": [0.5, 0.6, 0.7]}
                        },
                        payload={
                            "candidate_id": str(candidate.id),
                            "skills": ["Python", "Docker"]
                        }
                    )
                ]
            )
            
        await db.commit()
        logger.info(f"Mocked Qdrant points for {len(candidates)} candidates.")

if __name__ == "__main__":
    asyncio.run(mock_qdrant_data())
