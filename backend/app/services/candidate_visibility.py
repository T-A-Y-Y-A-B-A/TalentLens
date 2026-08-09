import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.application import Application
from app.models.candidate import CandidateEmbedding
from app.core.qdrant import qdrant_client

logger = structlog.get_logger()

async def get_candidate_org_ids(db: AsyncSession, candidate_id: uuid.UUID) -> List[str]:
    """
    Computes the definitive list of org_ids a candidate is associated with
    by querying their active applications.
    """
    result = await db.execute(
        select(Application.org_id)
        .where(Application.candidate_id == candidate_id)
        # Optionally filter by status if withdrawn candidates shouldn't be searchable
        # .where(Application.status != "withdrawn") 
    )
    # Return as list of strings since Qdrant payload prefers strings for UUIDs
    org_ids = [str(row) for row in result.scalars().all()]
    # Deduplicate
    return list(set(org_ids))

async def sync_candidate_qdrant_orgs(
    db: AsyncSession, 
    candidate_id: uuid.UUID, 
    force_org_id: Optional[str] = None
):
    """
    Recomputes the org_ids for a candidate from Postgres and overwrites the Qdrant payload.
    If force_org_id is provided (e.g. during HR manual upload before an application exists),
    it is appended to the computed list.
    """
    logger.info("sync_candidate_qdrant_orgs_started", candidate_id=str(candidate_id))
    
    # 1. Compute the authoritative list of orgs from Postgres
    org_ids = await get_candidate_org_ids(db, candidate_id)
    if force_org_id and force_org_id not in org_ids:
        org_ids.append(force_org_id)
        
    # 2. Get the candidate's embedding point ID
    result = await db.execute(
        select(CandidateEmbedding.qdrant_point_id)
        .where(CandidateEmbedding.candidate_id == candidate_id)
    )
    point_id = result.scalars().first()
    
    if not point_id:
        logger.info("sync_candidate_skipped_no_embedding", candidate_id=str(candidate_id))
        return
        
    # 3. Overwrite the org_ids array in Qdrant (atomic at the field level via set_payload)
    try:
        await qdrant_client.set_payload(
            collection_name="candidates",
            payload={"org_ids": org_ids},
            points=[point_id]
        )
        logger.info("sync_candidate_qdrant_orgs_success", candidate_id=str(candidate_id), org_ids=org_ids)
    except Exception as e:
        if "404" in str(e) or "Not found" in str(e):
            logger.warning("sync_candidate_qdrant_point_not_found_yet", candidate_id=str(candidate_id), point_id=point_id)
        else:
            logger.error("sync_candidate_qdrant_orgs_failed", candidate_id=str(candidate_id), error=str(e))
            raise

