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
        
    from sqlalchemy import and_
    from app.models.ai import JobMatch, AIMatchResult
    from app.schemas.matching import JobMatchResponse

    # Fetch results from DB using outer join
    stmt = (
        select(JobMatch, AIMatchResult)
        .outerjoin(
            AIMatchResult,
            and_(
                AIMatchResult.job_id == JobMatch.job_id,
                AIMatchResult.candidate_id == JobMatch.candidate_id,
            ),
        )
        .where(JobMatch.job_id == job_id)
        .where(JobMatch.composite_score >= 35)
        .order_by(JobMatch.composite_score.desc())
    )
    rows = (await db.execute(stmt)).all()
    
    # If no results and status isn't processing, it could be not_started or zero-matches
    if not rows:
        if pipeline_status == "done":
            # Explicitly done but 0 matches
            return {
                "status": "done",
                "results": [],
                "message": "No candidates found matching the criteria. Try lowering the experience requirement or relaxing strict filters."
            }
        else:
            return {"status": "not_started", "results": []}
            
    # Serialize matches using JobMatchResponse
    results_list = []
    for job_match, ai_result in rows:
        results_list.append(JobMatchResponse(
            candidate_id=job_match.candidate_id,
            composite_score=job_match.composite_score,
            flags=job_match.flags,
            missing_skills=job_match.missing_skills,
            strengths=ai_result.strengths if ai_result else None,
            weaknesses=ai_result.weaknesses if ai_result else None,
            recommendation=ai_result.recommendation if ai_result else None,
            interview_questions=ai_result.interview_questions if ai_result else None,
        ).model_dump(mode='json'))
    
    return {"status": "done", "results": results_list}

@router.post("/{job_id}/matches/{candidate_id}/reason")
@limiter.limit("10/minute")
async def generate_on_demand_reasoning(
    request: Request,
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates AI reasoning (strengths, weaknesses, etc.) for a specific candidate match on-demand.
    """
    # 1. Verify job access (tenant isolation)
    from sqlalchemy.orm import joinedload
    result = await db.execute(select(Job).options(joinedload(Job.department)).where(Job.id == job_id, Job.org_id == current_user.org_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
        
    # 2. Look up JobMatch row. If missing -> 404
    from app.models.ai import JobMatch, AIMatchResult
    job_match_res = await db.execute(
        select(JobMatch).where(JobMatch.job_id == job_id, JobMatch.candidate_id == candidate_id)
    )
    job_match = job_match_res.scalars().first()
    if not job_match:
        raise HTTPException(status_code=404, detail="Job match not found")

    # 3. Look up AIMatchResult row and check cache validity
    ai_result_res = await db.execute(
        select(AIMatchResult).where(AIMatchResult.job_id == job_id, AIMatchResult.candidate_id == candidate_id)
    )
    ai_result = ai_result_res.scalars().first()
    
    # If exists AND updated_at >= JobMatch.updated_at -> return cached narrative
    if ai_result and ai_result.updated_at and job_match.updated_at:
        ai_tz = ai_result.updated_at.replace(tzinfo=None)
        jm_tz = job_match.updated_at.replace(tzinfo=None)
        if ai_tz >= jm_tz:
            return {
                "candidate_id": str(job_match.candidate_id),
                "composite_score": job_match.composite_score,
                "flags": job_match.flags,
                "missing_skills": job_match.missing_skills,
                "strengths": ai_result.strengths,
                "weaknesses": ai_result.weaknesses,
                "recommendation": ai_result.recommendation,
                "interview_questions": ai_result.interview_questions
            }
        
    # 4. Fetch candidate
    from app.models.candidate import Candidate
    c_res = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = c_res.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # 5. Fetch parsed resume
    from app.models.candidate import Resume, ResumeParsedData
    r_res = await db.execute(
        select(ResumeParsedData)
        .join(Resume, ResumeParsedData.resume_id == Resume.id)
        .where(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
    )
    parsed_resume = r_res.scalars().first()
    if not parsed_resume:
        raise HTTPException(status_code=400, detail="Candidate resume not parsed yet")
        
    # 6. Generate fresh reasoning
    from app.services.matching import match_single_candidate
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    try:
        new_ai_result = await match_single_candidate(db, job, candidate, parsed_resume, job_match, redis_client)
        if not new_ai_result:
            raise HTTPException(status_code=500, detail="Failed to generate AI reasoning")
            
        await db.commit()
        await db.refresh(new_ai_result)
        
        return {
            "candidate_id": str(job_match.candidate_id),
            "composite_score": job_match.composite_score,
            "flags": job_match.flags,
            "missing_skills": job_match.missing_skills,
            "strengths": new_ai_result.strengths,
            "weaknesses": new_ai_result.weaknesses,
            "recommendation": new_ai_result.recommendation,
            "interview_questions": new_ai_result.interview_questions
        }
    finally:
        await redis_client.aclose()
