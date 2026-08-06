import asyncio
import structlog
from app.workers.celery_app import celery_app
from typing import List

logger = structlog.get_logger()

@celery_app.task(name="tasks.match_jobs_for_candidate")
def match_jobs_for_candidate(candidate_id: str, org_ids: List[str]):
    """
    Celery task entrypoint for matching a candidate against all open jobs in specified orgs.
    """
    from app.services.matching import run_candidate_matching_pipeline
    from app.core.database import engine
    logger.info("start_match_jobs_for_candidate", candidate_id=candidate_id, org_ids=org_ids)
    
    async def wrapper():
        try:
            await run_candidate_matching_pipeline(candidate_id, org_ids)
            logger.info("success_match_jobs_for_candidate", candidate_id=candidate_id)
        except Exception as e:
            logger.error("error_match_jobs_for_candidate", error=str(e), candidate_id=candidate_id)
            raise
        finally:
            await engine.dispose()
            
    asyncio.run(wrapper())
