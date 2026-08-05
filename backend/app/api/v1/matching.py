from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
import uuid

from app.core.dependencies import get_current_user, get_db
from app.models.identity import User
from app.models.recruitment import Job
from app.models.ai import AIMatchResult
from app.workers.tasks.matching import match_candidates_task

from app.core.rate_limit import limiter
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter(prefix="/jobs", tags=["matching"])

@router.post("/{job_id}/match", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def trigger_job_matching(
    request: Request,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the asynchronous AI matching pipeline for a specific job.
    Rate limited to 5 requests per minute per organization (IP in local dev).
    """
    # Verify job access (tenant isolation)
    result = await db.execute(select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
        
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # Store processing status
    await redis_client.setex(f"job_match_status:{job_id}", 3600, "processing")
    await redis_client.aclose()
    
    # Trigger celery task
    match_candidates_task.delay(str(job_id))
    
    return {"status": "processing", "job_id": str(job_id)}

@router.get("/{job_id}/matches")
async def get_job_matches(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the status and results of the job matching pipeline.
    """
    # Verify job access (tenant isolation)
    result = await db.execute(select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
        
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    pipeline_status = await redis_client.get(f"job_match_status:{job_id}")
    await redis_client.aclose()
    
    if pipeline_status == "processing":
        return {"status": "processing", "results": []}
        
    # Fetch results from DB
    res = await db.execute(
        select(AIMatchResult)
        .where(AIMatchResult.job_id == job_id)
        .order_by(AIMatchResult.match_pct.desc())
    )
    matches = res.scalars().all()
    
    # If no results and status isn't processing, it could be not_started or zero-matches
    if not matches:
        if pipeline_status == "done":
            # Explicitly done but 0 matches
            return {
                "status": "done",
                "results": [],
                "message": "No candidates found matching the criteria. Try lowering the experience requirement or relaxing strict filters."
            }
        else:
            return {"status": "not_started", "results": []}
            
    # Serialize matches
    results_list = [
        {
            "candidate_id": str(m.candidate_id),
            "match_pct": m.match_pct,
            "missing_skills": m.missing_skills,
            "strengths": m.strengths,
            "weaknesses": m.weaknesses,
            "recommendation": m.recommendation,
            "interview_questions": m.interview_questions
        }
        for m in matches
    ]
    
    return {"status": "done", "results": results_list}
