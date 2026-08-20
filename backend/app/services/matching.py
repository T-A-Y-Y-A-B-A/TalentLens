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

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def get_cross_encoder():
    global cross_encoder
    if cross_encoder is None:
        cross_encoder = CrossEncoder('cross-encoder/stsb-distilroberta-base')
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
    return []

async def run_candidate_matching_pipeline(candidate_id: str, org_ids: List[str]):
    return []

async def compute_msgc_score(
    db: AsyncSession,
    job: Job,
    candidate: Candidate,
    resume_data: ResumeParsedData
) -> dict:
    """
    Computes Multi-Signal Gated Composite Score (MSGC).
    Returns dict for JobMatch fields:
    {
        "skill_overlap_pct": float,
        "experience_semantic_pct": float,
        "years_fit": float,
        "composite_score": float,
        "flags": list[str]
    }
    """
    from app.services.matching import get_cross_encoder, get_sparse_model
    import numpy as np
    import asyncio
    import math

    # ----------------------------------------------------
    # Phase 4a: Skill Overlap (Dense Semantic Match)
    # ----------------------------------------------------
    candidate_skills = resume_data.skills or []
    req_skills = (job.requirements or {}).get("required_skills", []) if isinstance(job.requirements, dict) else getattr(job.requirements, "required_skills", [])
    
    skill_overlap_pct = 0.0
    if req_skills and candidate_skills:
        cand_skills_text = " ".join(candidate_skills)
        req_skills_text = " ".join(req_skills)
        
        loop = asyncio.get_event_loop()
        dense_c = await loop.run_in_executor(None, embed_text, cand_skills_text)
        dense_r = await loop.run_in_executor(None, embed_text, req_skills_text)
        
        # Dense similarity only
        n_c_d = np.linalg.norm(dense_c)
        n_r_d = np.linalg.norm(dense_r)
        c_sim = np.dot(dense_c, dense_r) / (n_c_d * n_r_d) if n_c_d and n_r_d else 0
        
        skill_overlap_pct = max(0.0, min(100.0, c_sim * 100))
    elif not req_skills:
        skill_overlap_pct = 100.0
        
    # ----------------------------------------------------
    # Phase 4b: Years of Experience Check
    # ----------------------------------------------------
    flags = []
    years_fit = 1.0
    
    min_years = 0.0
    if isinstance(job.requirements, dict):
        min_years = float(job.requirements.get("min_years_experience", 0.0))
        
    total_years = resume_data.total_years_experience
    
    if total_years is None:
        flags.append("years_unverified")
        years_fit = 1.0 # Do not penalize if unknown dates
    else:
        if min_years > 0:
            years_fit = min(1.0, total_years / min_years)
            if total_years < min_years:
                flags.append("below_min_experience")
        else:
            years_fit = 1.0
            
    # ----------------------------------------------------
    # Phase 4c: Semantic Experience Validator (Cross-Encoder)
    # ----------------------------------------------------
    exp_bullets = []
    if resume_data and resume_data.experience:
        for ex in resume_data.experience:
            if isinstance(ex, dict):
                bullets = ex.get("description")
                if isinstance(bullets, list):
                    exp_bullets.extend(bullets)
                elif isinstance(bullets, str):
                    exp_bullets.append(bullets)
    exp_text = " ".join(exp_bullets).strip()
    
    def get_section_text(sections):
        if not sections: return ""
        if isinstance(sections, list): return " ".join(sections)
        if isinstance(sections, dict):
            return " ".join(sections.get("required_skills", []))
        return str(sections)
        
    resp_text = get_section_text(job.key_responsibilities)
    exp_req_text = get_section_text(job.expectations)
    job_target_text = f"{resp_text} {exp_req_text}".strip()
    
    experience_semantic_pct = 0.0
    flags = []
    
    if exp_text and job_target_text:
        cross_encoder = get_cross_encoder()
        loop = asyncio.get_event_loop()
        score = await loop.run_in_executor(None, cross_encoder.predict, [job_target_text, exp_text])
        val = float(score[0] if isinstance(score, (list, np.ndarray)) else score)
        # STSB models output normalized scores (0 to 1), scale to 0-100%
        experience_semantic_pct = max(0.0, min(100.0, val * 100.0))
    elif not job_target_text:
        # DO NOT default to 100 on absent JD sections. Flag and neutral/exclude.
        flags.append("incomplete_jd_data")
        # We will set it to 0.0 but handle it in the formula by omitting the experience weight
        experience_semantic_pct = 0.0
        
    # ----------------------------------------------------
    # Title Relevance Check
    # ----------------------------------------------------
    exp_titles = []
    if resume_data and resume_data.experience:
        for ex in resume_data.experience:
            if isinstance(ex, dict) and ex.get("title"):
                exp_titles.append(ex.get("title"))
    
    title_relevance_pct = 0.0
    if exp_titles and job.title:
        cand_titles_text = " ".join(exp_titles)
        loop = asyncio.get_event_loop()
        dense_t_c = await loop.run_in_executor(None, embed_text, cand_titles_text)
        dense_t_j = await loop.run_in_executor(None, embed_text, job.title)
        
        n_tc = np.linalg.norm(dense_t_c)
        n_tj = np.linalg.norm(dense_t_j)
        t_sim = np.dot(dense_t_c, dense_t_j) / (n_tc * n_tj) if n_tc and n_tj else 0
        title_relevance_pct = max(0.0, min(100.0, t_sim * 100))
        # Debug printing for verification script
        print(f"[DEBUG] cand_titles: {cand_titles_text} | t_sim: {t_sim}")
        
    if "incomplete_jd_data" in flags:
        # If JD is incomplete, base it entirely on skill overlap
        real_experience_pct = 0.0
        gate_cap = 100.0 
        raw_composite = skill_overlap_pct
    else:
        # Spec math:
        real_experience_pct = experience_semantic_pct * 0.6 + title_relevance_pct * 0.4
        
        # Tiered Gate Cap per spec
        if real_experience_pct < 35:
            gate_cap = 45.0
        elif real_experience_pct < 55:
            gate_cap = 70.0
        else:
            gate_cap = 100.0
            
        raw_composite = (skill_overlap_pct * 0.35) + (real_experience_pct * 0.65)
        
    if "years_unverified" in flags and "incomplete_jd_data" not in flags:
        pass # Handle unverified years? User just said don't penalize.
        
    composite = min(raw_composite, gate_cap) * years_fit
    
    if real_experience_pct < 55 and "incomplete_jd_data" not in flags:
        flags.append("low_relevant_experience")
        
    # Temporary debug print for verification script
    print(f"[DEBUG] raw_composite: {raw_composite}, real_experience_pct: {real_experience_pct}, gate_cap: {gate_cap}")
    
    return {
        "skill_overlap_pct": float(skill_overlap_pct),
        "experience_semantic_pct": float(experience_semantic_pct),
        "title_relevance_pct": float(title_relevance_pct),
        "years_fit": float(years_fit),
        "composite_score": float(composite),
        "flags": flags
    }

async def compute_candidate_embeddings(db: AsyncSession, candidate: Candidate, resume_data: ResumeParsedData, collection_name: str = "candidates"):
    """Embed candidate experience and titles separately. Called once per resume parse."""
    import hashlib
    import uuid
    import asyncio
    from sqlalchemy import select
    from qdrant_client.models import PointStruct
    from app.models.candidate import CandidateEmbedding
    from app.ai.embeddings import embed_text
    from app.core.qdrant import qdrant_client
    
    # Extract experience bullets and titles
    exp_bullets = []
    exp_titles = []
    
    if resume_data and resume_data.experience:
        for job in resume_data.experience:
            if isinstance(job, dict):
                title = job.get("title")
                if title: exp_titles.append(title)
                bullets = job.get("description")
                if isinstance(bullets, list):
                    exp_bullets.extend(bullets)
                elif isinstance(bullets, str):
                    exp_bullets.append(bullets)
                
    exp_text = " ".join(exp_bullets).strip()
    titles_text = " ".join(exp_titles).strip()
    
    hash_input = f"{exp_text}|{titles_text}".encode('utf-8')
    current_hash = hashlib.sha256(hash_input).hexdigest()
    
    result = await db.execute(select(CandidateEmbedding).where(CandidateEmbedding.candidate_id == candidate.id))
    existing_emb = result.scalars().first()
    
    if existing_emb and existing_emb.section_hash == current_hash:
        return existing_emb

    loop = asyncio.get_event_loop()
    
    experience_vec = await loop.run_in_executor(None, embed_text, exp_text) if exp_text else None
    titles_vec = await loop.run_in_executor(None, embed_text, titles_text) if titles_text else None

    point_id = existing_emb.qdrant_point_id if existing_emb else str(uuid.uuid4())
    vectors = {}
    if experience_vec: vectors["experience_vec"] = experience_vec
    if titles_vec: vectors["titles_vec"] = titles_vec
    
    # Optional dense text representation
    dense_text = f"{candidate.name} {titles_text} {exp_text}".strip()
    dense_vec = await loop.run_in_executor(None, embed_text, dense_text)
    vectors["dense"] = dense_vec
        
    await qdrant_client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=point_id,
                vector=vectors,
                payload={"candidate_id": str(candidate.id)}
            )
        ]
    )
        
    if existing_emb:
        existing_emb.section_hash = current_hash
        existing_emb.model_version = "BAAI/bge-small-en-v1.5"
    else:
        existing_emb = CandidateEmbedding(
            candidate_id=candidate.id,
            qdrant_point_id=point_id,
            model_version="BAAI/bge-small-en-v1.5",
            section_hash=current_hash
        )
        db.add(existing_emb)
    
    await db.commit()
    await db.refresh(existing_emb)
    return existing_emb

async def compute_job_embeddings(db: AsyncSession, job: Job, collection_name: str = "jobs"):
    """Embed each structured JD section separately. Called once per job create/edit, not per match."""
    import hashlib
    import uuid
    import asyncio
    from sqlalchemy import select
    from qdrant_client.models import PointStruct
    from app.models.recruitment import JobEmbedding
    from app.ai.embeddings import embed_text
    from app.core.qdrant import qdrant_client
    
    def get_section_text(sections):
        if not sections: return ""
        if isinstance(sections, list): return " ".join(sections)
        if isinstance(sections, dict):
            return " ".join(sections.get("required_skills", []))
        return str(sections)
    
    resp_text = get_section_text(job.key_responsibilities)
    req_text = get_section_text(job.requirements)
    exp_text = get_section_text(job.expectations)
    
    hash_input = f"{resp_text}|{req_text}|{exp_text}".encode('utf-8')
    current_hash = hashlib.sha256(hash_input).hexdigest()
    
    result = await db.execute(select(JobEmbedding).where(JobEmbedding.job_id == job.id))
    existing_emb = result.scalars().first()
    
    if existing_emb and existing_emb.section_hash == current_hash:
        return existing_emb

    loop = asyncio.get_event_loop()
    
    responsibilities_vec = await loop.run_in_executor(None, embed_text, resp_text) if resp_text else None
    requirements_vec = await loop.run_in_executor(None, embed_text, req_text) if req_text else None
    expectations_vec = await loop.run_in_executor(None, embed_text, exp_text) if exp_text else None

    point_id = existing_emb.qdrant_point_id if existing_emb else str(uuid.uuid4())
    vectors = {}
    if responsibilities_vec: vectors["responsibilities_vec"] = responsibilities_vec
    if requirements_vec: vectors["requirements_vec"] = requirements_vec
    if expectations_vec: vectors["expectations_vec"] = expectations_vec
    
    jd_text = f"{job.title} {job.description} {resp_text} {req_text}"
    dense_vec = await loop.run_in_executor(None, embed_text, jd_text)
    vectors["dense"] = dense_vec
        
    await qdrant_client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=point_id,
                vector=vectors,
                payload={"job_id": str(job.id), "org_id": str(job.org_id)}
            )
        ]
    )
        
    if existing_emb:
        existing_emb.section_hash = current_hash
        existing_emb.model_version = "BAAI/bge-small-en-v1.5"
    else:
        existing_emb = JobEmbedding(
            job_id=job.id,
            qdrant_point_id=point_id,
            model_version="BAAI/bge-small-en-v1.5",
            section_hash=current_hash
        )
        db.add(existing_emb)
    
    await db.commit()
    await db.refresh(existing_emb)
    return existing_emb
