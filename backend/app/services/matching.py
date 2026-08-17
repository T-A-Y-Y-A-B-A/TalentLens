import hashlib
import json
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, Prefetch, FusionQuery, Fusion
import uuid
from pydantic import BaseModel, Field

from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.ai import AIMatchResult, AIUsageLog, JobMatch
from app.core.qdrant import qdrant_client
from app.ai.llm import call_llm
from app.ai.embeddings import embed_text

from app.core.config import settings
import redis.asyncio as redis
from fastembed import SparseTextEmbedding
from sentence_transformers import CrossEncoder

logger = structlog.get_logger()

sparse_model = None
cross_encoder = None

def get_sparse_model():
    global sparse_model
    if sparse_model is None:
        sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    return sparse_model

def get_cross_encoder():
    global cross_encoder
    if cross_encoder is None:
        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return cross_encoder

class MatchNarrative(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    reasoning: str
    interview_questions: List[str]

async def generate_sparse_embedding(text: str):
    result = list(sparse_model.embed([text]))[0]
    return {"indices": result.indices.tolist(), "values": result.values.tolist()}

def _calculate_ats_score(resume_data: ResumeParsedData, job: Job) -> float:
    # Lightweight ATS Score: Keyword intersection
    job_text = f"{job.title} {job.description} {job.requirements}".lower()
    if not resume_data.skills:
        return 0.0
    matched_skills = [skill for skill in resume_data.skills if skill.lower() in job_text]
    score = (len(matched_skills) / len(resume_data.skills)) * 100.0
    return round(score, 1)

async def match_single_candidate(
    db: AsyncSession,
    job: Job,
    candidate: Candidate,
    resume_data: ResumeParsedData,
    job_match: JobMatch,
    redis_client: redis.Redis
) -> Optional[AIMatchResult]:
    
    prompt_version = "matching_v2"
    
    start_time = datetime.utcnow()
    
    prompt = f"""
    You are an expert technical recruiter evaluating a candidate for a specific job.
    
    JOB REQUIREMENTS:
    Title: {job.title}
    Department: {job.department.name if job.department else 'N/A'}
    Description: {job.description}
    Requirements: {job.requirements}
    
    CANDIDATE PROFILE:
    Name: {resume_data.name if hasattr(resume_data, 'name') else 'Candidate'}
    Experience: {json.dumps([exp for exp in resume_data.experience])}
    Education: {json.dumps([edu for edu in resume_data.education])}
    
    KEYWORD MATCHING RESULTS (Deterministic):
    Matched Skills: {job_match.matched_skills}
    Missing Skills: {job_match.missing_skills}
    
    Analyze how well this candidate matches the job. Provide strengths, weaknesses, a final reasoning/recommendation, and 3 specific interview questions.
    
    IMPORTANT: Infer years of experience from job history entries. If the candidate falls short of the experience requirements, phrase it as an inferred weakness (e.g. "Resume does not clearly demonstrate 4+ years..."), not an asserted fact. Do not fabricate year counts.
    """
    
    try:
        llm_response = await call_llm(
            prompt=prompt,
            response_model=MatchNarrative,
            system_prompt="You are an expert AI recruiter matching resumes to jobs."
        )
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy import func
        
        stmt = pg_insert(AIMatchResult).values(
            org_id=job.org_id,
            job_id=job.id,
            candidate_id=candidate.id,
            strengths=llm_response.strengths,
            weaknesses=llm_response.weaknesses,
            recommendation=llm_response.reasoning,
            interview_questions=llm_response.interview_questions,
            prompt_version=prompt_version
        )
        
        stmt = stmt.on_conflict_do_update(
            constraint="uq_ai_match_result",
            set_={
                "strengths": stmt.excluded.strengths,
                "weaknesses": stmt.excluded.weaknesses,
                "recommendation": stmt.excluded.recommendation,
                "interview_questions": stmt.excluded.interview_questions,
                "updated_at": func.now()
            },
        )
        
        await db.execute(stmt)
        
        usage_log = AIUsageLog(
            org_id=job.org_id,
            endpoint="api:match_single_candidate",
            prompt_version=prompt_version,
            cache_hit=False,
            candidates_matched=1,
            latency_ms=latency_ms
        )
        db.add(usage_log)
        
        # Need to return the updated record
        result = await db.execute(select(AIMatchResult).where(AIMatchResult.job_id == job.id, AIMatchResult.candidate_id == candidate.id))
        return result.scalars().first()
        
    except Exception as e:
        logger.error("matching.llm_error", error=str(e), candidate_id=str(candidate.id))
        return None

async def run_job_matching_pipeline(job_id: str):
    # The job matching pipeline is now handled entirely via JobMatch (keyword upsert) 
    # and lazy narrative generation. We no longer write placeholder AIMatchResult rows.
    # We simply return empty list and let the frontend rely on JobMatch.
    return []

async def run_candidate_matching_pipeline(candidate_id: str, org_ids: List[str]):
    # Similarly, candidate matching pipeline is handled via keyword matches.
    return []
