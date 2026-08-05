from app.workers.celery_app import celery_app
from app.services.matching import run_job_matching_pipeline
import asyncio
import structlog

logger = structlog.get_logger()

@celery_app.task(name="match_candidates_task", bind=True, max_retries=3)
def match_candidates_task(self, job_id: str):
    logger.info("matching.task_started", job_id=job_id)
    
    # Run the async pipeline in the sync celery task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        results = loop.run_until_complete(run_job_matching_pipeline(job_id))
        
        # Mark as done in Redis
        import redis
        from app.core.config import settings
        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.setex(f"job_match_status:{job_id}", 3600, "done")
        
        logger.info("matching.task_completed", job_id=job_id, matched_count=len(results))
        return [str(r.id) for r in results] if results else []
    except Exception as exc:
        logger.error("matching.task_failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
