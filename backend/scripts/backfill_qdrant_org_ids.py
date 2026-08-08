import asyncio
import os
import sys

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.candidate import CandidateEmbedding
from app.services.candidate_visibility import sync_candidate_qdrant_orgs
import structlog

logger = structlog.get_logger()

async def backfill():
    logger.info("starting_qdrant_org_ids_backfill")
    
    async with AsyncSessionLocal() as db:
        # Get all distinct candidates that have an embedding
        result = await db.execute(select(CandidateEmbedding.candidate_id).distinct())
        candidate_ids = result.scalars().all()
        
        logger.info(f"found_{len(candidate_ids)}_candidates_with_embeddings_to_process")
        
        success_count = 0
        failure_count = 0
        
        for cid in candidate_ids:
            try:
                await sync_candidate_qdrant_orgs(db, cid)
                success_count += 1
            except Exception as e:
                logger.error("backfill_failed_for_candidate", candidate_id=str(cid), error=str(e))
                failure_count += 1
                
        logger.info("backfill_completed", success_count=success_count, failure_count=failure_count)

if __name__ == "__main__":
    asyncio.run(backfill())
