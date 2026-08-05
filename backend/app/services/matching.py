import hashlib
import json
import asyncio
from typing import List, Optional
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from qdrant_client.models import Prefetch, QueryRequest
import uuid
from pydantic import BaseModel, Field

from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.ai import AIMatchResult, AIUsageLog
from app.core.qdrant import qdrant_client
from app.ai.llm import call_llm
from app.ai.embeddings import embed_text

# Use Redis caching
from app.core.config import settings
import redis.asyncio as redis
from fastembed import SparseTextEmbedding
from sentence_transformers import CrossEncoder

logger = structlog.get_logger()

# Initialize models lazily
sparse_model = None
cross_encoder = None

def get_sparse_model():
    global sparse_model
    if sparse_model is None:
        sparse_model = SparseTextEmbedding()
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
    # fastembed is synchronous but yields generators, let's wrap it in an async-friendly way if needed, or just run it
    # sparse_model.embed returns a generator of SparseEmbedding
    # A SparseEmbedding has .indices and .values
    result = list(sparse_model.embed([text]))[0]
    return {"indices": result.indices.tolist(), "values": result.values.tolist()}

def _compute_cache_key(prompt_version: str, job: Job, candidate: Candidate, resume_data: ResumeParsedData) -> str:
    key_string = f"{prompt_version}_{job.id}_{job.updated_at.timestamp()}_{candidate.id}_{resume_data.updated_at.timestamp()}"
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

async def match_single_candidate(
    db: AsyncSession,
    job: Job,
    candidate: Candidate,
    resume_data: ResumeParsedData,
    redis_client: redis.Redis
) -> Optional[AIMatchResult]:
    
    prompt_version = "matching_v1"
    cache_key = _compute_cache_key(prompt_version, job, candidate, resume_data)
    
    # Check cache
    cached_result = await redis_client.get(f"match:{cache_key}")
    if cached_result:
        logger.info("matching.cache_hit", candidate_id=str(candidate.id))
        
        # Log usage
        usage_log = AIUsageLog(
            org_id=job.org_id,
            endpoint="worker:match_single_candidate",
            prompt_version=prompt_version,
            cache_hit=True,
            candidates_matched=1
        )
        db.add(usage_log)
        
        # We need to return an AIMatchResult. Let's create an ephemeral one or fetch it from DB if it exists.
        # But wait, we should fetch from DB if we want the actual ORM object. 
        # Alternatively, the DB *is* our persistent store, so if it's in Redis, it's in DB.
        db_result = await db.execute(select(AIMatchResult).where(AIMatchResult.cache_key == cache_key))
        return db_result.scalars().first()
    
    # Cache Miss -> Execute LLM
    logger.info("matching.cache_miss", candidate_id=str(candidate.id))
    start_time = datetime.utcnow()
    
    prompt = f"""
    You are an expert technical recruiter evaluating a candidate for a specific job.
    
    JOB REQUIREMENTS:
    Title: {job.title}
    Department: {job.department.name}
    Description: {job.description}
    Requirements: {job.requirements}
    
    CANDIDATE PROFILE:
    Name: {resume_data.name}
    Skills: {', '.join(resume_data.skills)}
    Experience: {json.dumps([exp for exp in resume_data.experience])}
    Education: {json.dumps([edu for edu in resume_data.education])}
    
    Analyze how well this candidate matches the job. Provide the match percentage (0-100), missing skills, strengths, weaknesses, a final recommendation, and 3 specific interview questions.
    """
    
    try:
        # LLM Call
        llm_response = await call_llm(
            prompt=prompt,
            response_model=CandidateMatchOutput,
            system_prompt="You are an expert AI recruiter matching resumes to jobs."
        )
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Save to DB
        match_result = AIMatchResult(
            org_id=job.org_id,
            job_id=job.id,
            candidate_id=candidate.id,
            match_pct=llm_response.match_pct,
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
        
        # Cache the success
        await redis_client.setex(f"match:{cache_key}", 30 * 24 * 60 * 60, "true") # 30 days
        
        return match_result
        
    except Exception as e:
        logger.error("matching.llm_error", error=str(e), candidate_id=str(candidate.id))
        await db.rollback()
        return None

async def run_job_matching_pipeline(job_id: str):
    """
    Core pipeline: Hybrid Search -> Cross-Encoder -> LLM matching -> Store.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalars().first()
        if not job:
            return
            
        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        # 1. Combine Job context
        job_text = f"{job.title} {job.description} {job.requirements}"
        
        # 2. Generate Dense and Sparse vectors
        # Running dense model in async executor to not block if needed, but embed_text is synchronous? 
        # Wait, embed_text is synchronous.
        loop = asyncio.get_event_loop()
        dense_vector = await loop.run_in_executor(None, embed_text, job_text)
        
        def embed_sparse():
            model = get_sparse_model()
            return list(model.embed([job_text]))[0]
            
        sparse_dict = await loop.run_in_executor(None, embed_sparse)
        sparse_vector = qdrant_client.models.SparseVector(
            indices=sparse_dict.indices.tolist(),
            values=sparse_dict.values.tolist()
        )
        
        # 3. Hybrid Search in Qdrant (Pre-filtered by org_id)
        # Using Query API which allows combining dense and sparse using RRF natively, or we can issue a search_batch.
        # Qdrant client 1.9.0 supports query_points.
        try:
            from qdrant_client.models import Prefetch
            
            # Since we want to fuse sparse and dense, we use `prefetch` in Qdrant Query API.
            # Prefetch allows executing multiple sub-queries and fusing them.
            prefetch_dense = Prefetch(
                query=dense_vector,
                using="dense",
                limit=20
            )
            prefetch_sparse = Prefetch(
                query=sparse_vector,
                using="sparse",
                limit=20
            )
            
            filter_org = Filter(
                must=[
                    FieldCondition(
                        key="org_id",
                        match=MatchValue(value=str(job.org_id))
                    )
                ]
            )
            
            qdrant_res = await qdrant_client.query_points(
                collection_name="candidates",
                prefetch=[prefetch_dense, prefetch_sparse],
                query=qdrant_client.models.FusionQuery(fusion=qdrant_client.models.Fusion.RRF),
                query_filter=filter_org,
                limit=10,
                with_payload=True
            )
            points = qdrant_res.points
        except Exception as e:
            logger.error("matching.qdrant_error", error=str(e))
            points = []

        if not points:
            # Handle zero matches
            logger.info("matching.zero_candidates", job_id=job_id)
            usage = AIUsageLog(
                org_id=job.org_id,
                endpoint="worker:match_single_candidate",
                prompt_version="matching_v1",
                candidates_matched=0
            )
            db.add(usage)
            await db.commit()
            return []
            
        candidate_ids = [p.payload["candidate_id"] for p in points if "candidate_id" in p.payload]
        if not candidate_ids:
            return []
            
        # Fetch candidate data
        c_res = await db.execute(select(Candidate).where(Candidate.id.in_(candidate_ids)))
        candidates = {str(c.id): c for c in c_res.scalars().all()}
        
        r_res = await db.execute(select(ResumeParsedData).where(ResumeParsedData.candidate_id.in_(candidate_ids)))
        parsed_resumes = {str(r.candidate_id): r for r in r_res.scalars().all()}
        
        # 4. Cross-Encoder Reranking
        pairs = []
        c_list = []
        for pid in candidate_ids:
            if pid in parsed_resumes:
                c_list.append(pid)
                r_data = parsed_resumes[pid]
                c_text = f"{r_data.name} {' '.join(r_data.skills)} {r_data.experience}"
                pairs.append((job_text, c_text))
                
        if pairs:
            model = get_cross_encoder()
            scores = await loop.run_in_executor(None, model.predict, pairs)
            # Sort c_list by scores descending
            scored_candidates = sorted(zip(c_list, scores), key=lambda x: x[1], reverse=True)
            # Take top 5 after reranking
            final_ids = [x[0] for x in scored_candidates[:5]]
        else:
            final_ids = []
            
        # 5. LLM Explanation & Cache/DB saving
        results = []
        for cid in final_ids:
            res = await match_single_candidate(db, job, candidates[cid], parsed_resumes[cid], redis_client)
            if res:
                results.append(res)
                
        await redis_client.aclose()
        return results
