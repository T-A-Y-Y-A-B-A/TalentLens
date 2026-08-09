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
from app.models.ai import AIMatchResult, AIUsageLog
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

class CandidateMatchOutput(BaseModel):
    match_pct: float = Field(..., ge=0.0, le=100.0)
    missing_skills: List[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    interview_questions: List[str]

async def generate_sparse_embedding(text: str):
    result = list(sparse_model.embed([text]))[0]
    return {"indices": result.indices.tolist(), "values": result.values.tolist()}

def _compute_cache_key(prompt_version: str, job: Job, candidate: Candidate, resume_data: ResumeParsedData) -> str:
    key_string = f"{prompt_version}_{job.id}_{job.updated_at.timestamp()}_{candidate.id}_{resume_data.updated_at.timestamp()}"
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

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
    redis_client: redis.Redis
) -> Optional[AIMatchResult]:
    
    prompt_version = "matching_v1"
    cache_key = _compute_cache_key(prompt_version, job, candidate, resume_data)
    
    cached_result = await redis_client.get(f"match:{cache_key}")
    if cached_result:
        logger.info("matching.cache_hit", candidate_id=str(candidate.id))
        usage_log = AIUsageLog(
            org_id=job.org_id,
            endpoint="worker:match_single_candidate",
            prompt_version=prompt_version,
            cache_hit=True,
            candidates_matched=1
        )
        db.add(usage_log)
        db_result = await db.execute(select(AIMatchResult).where(AIMatchResult.cache_key == cache_key))
        return db_result.scalars().first()
    
    logger.info("matching.cache_miss", candidate_id=str(candidate.id))
    start_time = datetime.utcnow()
    
    ats_score = _calculate_ats_score(resume_data, job)
    
    prompt = f"""
    You are an expert technical recruiter evaluating a candidate for a specific job.
    
    JOB REQUIREMENTS:
    Title: {job.title}
    Department: {job.department.name if job.department else 'N/A'}
    Description: {job.description}
    Requirements: {job.requirements}
    
    CANDIDATE PROFILE:
    Name: {resume_data.name if hasattr(resume_data, 'name') else 'Candidate'}
    Skills: {', '.join(resume_data.skills)}
    Experience: {json.dumps([exp for exp in resume_data.experience])}
    Education: {json.dumps([edu for edu in resume_data.education])}
    
    Analyze how well this candidate matches the job. Provide the match percentage (0-100), missing skills, strengths, weaknesses, a final recommendation, and 3 specific interview questions.
    """
    
    try:
        llm_response = await call_llm(
            prompt=prompt,
            response_model=CandidateMatchOutput,
            system_prompt="You are an expert AI recruiter matching resumes to jobs."
        )
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Check if a lightweight result already exists
        existing_res = await db.execute(select(AIMatchResult).where(AIMatchResult.cache_key == cache_key))
        match_result = existing_res.scalars().first()
        
        if match_result:
            match_result.match_pct = llm_response.match_pct
            match_result.ats_score = ats_score
            match_result.missing_skills = llm_response.missing_skills
            match_result.strengths = llm_response.strengths
            match_result.weaknesses = llm_response.weaknesses
            match_result.recommendation = llm_response.recommendation
            match_result.interview_questions = llm_response.interview_questions
        else:
            match_result = AIMatchResult(
                org_id=job.org_id,
                job_id=job.id,
                candidate_id=candidate.id,
                match_pct=llm_response.match_pct,
                ats_score=ats_score,
                missing_skills=llm_response.missing_skills,
                strengths=llm_response.strengths,
                weaknesses=llm_response.weaknesses,
                recommendation=llm_response.recommendation,
                interview_questions=llm_response.interview_questions,
                prompt_version=prompt_version,
                cache_key=cache_key
            )
            db.add(match_result)
        
        usage_log = AIUsageLog(
            org_id=job.org_id,
            endpoint="worker:match_single_candidate",
            prompt_version=prompt_version,
            cache_hit=False,
            candidates_matched=1,
            latency_ms=latency_ms
        )
        db.add(usage_log)
        
        await db.commit()
        await db.refresh(match_result)
        
        await redis_client.setex(f"match:{cache_key}", 30 * 24 * 60 * 60, "true")
        
        return match_result
        
    except Exception as e:
        logger.error("matching.llm_error", error=str(e), candidate_id=str(candidate.id))
        await db.rollback()
        return None

async def _execute_matching_pipeline(query_text: str, target_collection: str, org_ids: Optional[List[str]]) -> List[str]:
    # 1. Embed Query
    loop = asyncio.get_event_loop()
    dense_vector = await loop.run_in_executor(None, embed_text, query_text)
    
    def embed_sparse():
        model = get_sparse_model()
        return list(model.embed([query_text]))[0]
        
    sparse_dict = await loop.run_in_executor(None, embed_sparse)
    
    import qdrant_client as qc
    sparse_vector = qc.models.SparseVector(
        indices=sparse_dict.indices.tolist(),
        values=sparse_dict.values.tolist()
    )
    
    # 2. Setup Prefetch Filters
    filters = []
    if org_ids:
        # We only apply org_id filtering if the target collection items have an org_id (like Jobs)
        # For Candidates, they don't have org_id in their Qdrant payload, so we rely on SQL joins later,
        # but for Jobs, we MUST filter in Qdrant to ensure tenant isolation.
        if target_collection == "jobs":
            if len(org_ids) == 1:
                filters = [FieldCondition(key="org_id", match=MatchValue(value=str(org_ids[0])))]
            else:
                # Qdrant match_any
                filters = [FieldCondition(key="org_id", match=qc.models.MatchAny(any=[str(o) for o in org_ids]))]

    qdrant_filter = Filter(must=filters) if filters else None
    
    prefetch_dense = Prefetch(
        query=dense_vector,
        using="dense",
        limit=20,
        filter=qdrant_filter
    )
    prefetch_sparse = Prefetch(
        query=sparse_vector,
        using="sparse",
        limit=20,
        filter=qdrant_filter
    )
    
    # 3. Hybrid Search
    try:
        qdrant_res = await qdrant_client.query_points(
            collection_name=target_collection,
            prefetch=[prefetch_dense, prefetch_sparse],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=10,
            with_payload=True
        )
        # Extract the target ID (either candidate_id or job_id)
        id_key = "candidate_id" if target_collection == "candidates" else "job_id"
        return [p.payload[id_key] for p in qdrant_res.points if id_key in p.payload]
    except Exception as e:
        logger.error("matching.qdrant_error", error=str(e))
        return []

async def run_job_matching_pipeline(job_id: str):
    from sqlalchemy.orm import joinedload
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).options(joinedload(Job.department)).where(Job.id == job_id))
        job = result.scalars().first()
        if not job:
            return
            
        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        job_text = f"{job.title} {job.description} {job.requirements}"
        
        # SQL Isolation: only match candidates who have applied to this specific job
        from app.models.application import Application
        c_res = await db.execute(
            select(Candidate).distinct()
            .join(Application, Application.candidate_id == Candidate.id)
            .where(Application.job_id == job.id)
        )
        candidates = {str(c.id): c for c in c_res.scalars().all()}
        
        if not candidates:
            return []
            
        valid_candidate_ids = list(candidates.keys())
        r_res = await db.execute(select(ResumeParsedData)
                                 .join(Resume, ResumeParsedData.resume_id == Resume.id)
                                 .where(Resume.candidate_id.in_(valid_candidate_ids)))
        
        parsed_resumes = {}
        for r in r_res.scalars().all():
            r_c_id = await db.scalar(select(Resume.candidate_id).where(Resume.id == r.resume_id))
            parsed_resumes[str(r_c_id)] = r
            
        # Cross-Encoder
        pairs = []
        c_list = []
        for pid in valid_candidate_ids:
            if pid in parsed_resumes:
                c_list.append(pid)
                r_data = parsed_resumes[pid]
                c_text = f"{' '.join(r_data.skills)} {r_data.experience}"
                pairs.append((job_text, c_text))
                
        if pairs:
            loop = asyncio.get_event_loop()
            model = get_cross_encoder()
            scores = await loop.run_in_executor(None, model.predict, pairs)
            scored_candidates = sorted(zip(c_list, scores), key=lambda x: x[1], reverse=True)
            # Fetch all candidates, top 5 get LLM reasoning, rest get lightweight match result
            final_ids = [x[0] for x in scored_candidates]
            
            # Normalize scores roughly to 0-100 range for display
            min_score = min(scores) if scores else 0
            max_score = max(scores) if scores else 1
            if max_score == min_score:
                normalized_scores = {cid: 80.0 for cid in c_list}
            else:
                normalized_scores = {
                    c_list[i]: round(((scores[i] - min_score) / (max_score - min_score)) * 40 + 55, 1) 
                    for i in range(len(c_list))
                }
        else:
            final_ids = []
            normalized_scores = {}
            
        results = []
        for i, cid in enumerate(final_ids):
            if i < 5:
                # Top 5: run deep LLM reasoning
                res = await match_single_candidate(db, job, candidates[cid], parsed_resumes[cid], redis_client)
                if res:
                    results.append(res)
            else:
                # Ranks 6+: Lightweight result, no LLM call
                ats_score = _calculate_ats_score(parsed_resumes[cid], job)
                prompt_version = "matching_v1"
                cache_key = _compute_cache_key(prompt_version, job, candidates[cid], parsed_resumes[cid])
                
                # Check DB first
                db_result = await db.execute(select(AIMatchResult).where(AIMatchResult.cache_key == cache_key))
                res = db_result.scalars().first()
                
                if not res:
                    # Create placeholder MatchResult without LLM fields
                    res = AIMatchResult(
                        org_id=job.org_id,
                        job_id=job.id,
                        candidate_id=candidates[cid].id,
                        match_pct=normalized_scores.get(cid, 60.0),
                        ats_score=ats_score,
                        missing_skills=[],
                        strengths=[],
                        weaknesses=[],
                        recommendation="",
                        interview_questions=[],
                        prompt_version=prompt_version,
                        cache_key=cache_key
                    )
                    db.add(res)
                    await db.commit()
                    await db.refresh(res)
                
                results.append(res)
                
        await redis_client.aclose()
        return results

async def run_candidate_matching_pipeline(candidate_id: str, org_ids: List[str]):
    async with AsyncSessionLocal() as db:
        c_res = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = c_res.scalars().first()
        if not candidate:
            return
            
        r_res = await db.execute(
            select(ResumeParsedData)
            .join(Resume, ResumeParsedData.resume_id == Resume.id)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.created_at.desc())
        )
        resume_data = r_res.scalars().first()
        if not resume_data:
            return
            
        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        resume_text = f"{' '.join(resume_data.skills)} {resume_data.experience}"
        
        # Qdrant filtering by org_ids guarantees tenant isolation
        job_ids = await _execute_matching_pipeline(resume_text, "jobs", org_ids)
        
        if not job_ids:
            return []
            
        # Fetch Jobs (SQL validation just in case)
        from app.models.recruitment import JobStatus
        j_res = await db.execute(
            select(Job)
            .where(Job.id.in_(job_ids))
            .where(Job.org_id.in_(org_ids))
            .where(Job.status == JobStatus.OPEN)
        )
        jobs = {str(j.id): j for j in j_res.scalars().all()}
        
        if not jobs:
            return []
            
        # Cross-Encoder
        pairs = []
        j_list = []
        for jid in jobs:
            j_list.append(jid)
            job = jobs[jid]
            j_text = f"{job.title} {job.description} {job.requirements}"
            pairs.append((resume_text, j_text))
            
        if pairs:
            loop = asyncio.get_event_loop()
            model = get_cross_encoder()
            scores = await loop.run_in_executor(None, model.predict, pairs)
            scored_jobs = sorted(zip(j_list, scores), key=lambda x: x[1], reverse=True)
            final_ids = [x[0] for x in scored_jobs[:5]]
        else:
            final_ids = []
            
        results = []
        for jid in final_ids:
            res = await match_single_candidate(db, jobs[jid], candidate, resume_data, redis_client)
            if res:
                results.append(res)
                
        await redis_client.aclose()
        return results
