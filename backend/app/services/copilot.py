import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from qdrant_client.http import models as qdrant_models
import structlog

from app.schemas.copilot import CopilotFilter, CopilotQueryRequest, CopilotQueryResponse
from app.ai.prompts.copilot_v1 import COPILOT_SYSTEM_PROMPT
from app.ai.llm import call_llm
from app.core.qdrant import qdrant_client
from app.ai.embeddings import embed_text
from app.models.identity import User
from app.models.candidate import Candidate, ResumeParsedData, Resume
from app.models.application import Application

from sqlalchemy import func, or_
import structlog

logger = structlog.get_logger()

async def get_exact_skill_matches(db: AsyncSession, parsed_filter: CopilotFilter) -> set[uuid.UUID]:
    """
    Direct Postgres check — catches literal/substring matches that
    Qdrant's semantic ranking might not surface in its top-K.
    """
    terms = []
    if parsed_filter.skills: terms.extend(parsed_filter.skills)
    if parsed_filter.keywords: terms.extend(parsed_filter.keywords)
    
    if not terms:
        return set()

    import sqlalchemy
    conditions = []
    for term in terms:
        # substring match against the skills array, case-insensitive
        conditions.append(
            func.cast(ResumeParsedData.skills, sqlalchemy.String).ilike(f'%{term}%')
        )

    stmt = select(Candidate.id).join(
        Resume, Resume.candidate_id == Candidate.id
    ).join(
        ResumeParsedData, ResumeParsedData.resume_id == Resume.id
    ).where(or_(*conditions))
    
    result = await db.execute(stmt)
    return {row[0] for row in result.all()}

def validate_candidate_against_filter(candidate_skills: list[str], parsed_filter: CopilotFilter) -> bool:
    """
    Final gate: confirms a candidate genuinely satisfies the parsed filter,
    regardless of which leg (Qdrant or exact-match) surfaced them.
    """
    normalized_skills = {s.lower() for s in (candidate_skills or [])}

    if parsed_filter.skills:
        if not any(
            any(req.lower() in skill for skill in normalized_skills)
            for req in parsed_filter.skills
        ):
            return False

    if parsed_filter.keywords:
        if not any(
            any(kw.lower() in skill for skill in normalized_skills)
            for kw in parsed_filter.keywords
        ):
            return False

    # extend with certifications, min_experience, location, etc. as those fields
    # already have structured data available on Candidate

    return True

async def query_copilot(db: AsyncSession, request: CopilotQueryRequest, current_user: User) -> CopilotQueryResponse:
    # 1. Parse natural language into structured CopilotFilter
    logger.info("copilot_query_started", org_id=str(current_user.org_id))
    
    parsed_filter: CopilotFilter = await call_llm(
        prompt=request.query,
        response_model=CopilotFilter,
        system_prompt=COPILOT_SYSTEM_PROMPT
    )
    
    # Merge job_id from request if the LLM didn't pick it up or if it was provided as default
    if request.job_id and not parsed_filter.job_id:
        parsed_filter.job_id = request.job_id

    # DEBUG LOG 1: LLM Extraction
    logger.info("copilot_debug_stage1_llm_extraction", parsed_filter=parsed_filter.model_dump())

    # 2. Construct Qdrant Query String
    search_components = []
    if parsed_filter.skills:
        search_components.append(f"Skills: {', '.join(parsed_filter.skills)}")
    if parsed_filter.keywords:
        search_components.append(f"Keywords: {', '.join(parsed_filter.keywords)}")
    if parsed_filter.certifications:
        search_components.append(f"Certifications: {', '.join(parsed_filter.certifications)}")
    if parsed_filter.location:
        search_components.append(f"Location: {parsed_filter.location}")
    if parsed_filter.seniority_level:
        search_components.append(f"Seniority: {parsed_filter.seniority_level}")
    if parsed_filter.education_level:
        search_components.append(f"Education: {parsed_filter.education_level}")
        
    search_text = " ".join(search_components)
    candidate_ids = []
    
    if search_text.strip():
        # Hit Qdrant first with the generated string
        dense_vector = embed_text(search_text)
        
        # CRITICAL: Org Isolation Filter
        org_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="org_ids",
                    match=qdrant_models.MatchValue(value=str(current_user.org_id))
                )
            ]
        )
        
        search_result = await qdrant_client.query_points(
            collection_name="candidates",
            query=dense_vector,
            using="dense",
            query_filter=org_filter,
            limit=50,
            score_threshold=0.75  # Filter out low-relevance semantic matches
        )
        
        for point in search_result.points:
            if "candidate_id" in point.payload:
                candidate_ids.append(uuid.UUID(point.payload["candidate_id"]))
                
        # DEBUG LOG 2: Qdrant Search Results
        qdrant_hits_debug = [
            {
                "candidate_id": point.payload.get("candidate_id"), 
                "score": point.score, 
                "org_ids": point.payload.get("org_ids")
            } 
            for point in search_result.points
        ]
        logger.info("copilot_debug_stage2_qdrant_search", 
                    org_filter_applied=str(current_user.org_id), 
                    total_hits=len(qdrant_hits_debug),
                    hits=qdrant_hits_debug)
                    
        logger.info("qdrant_search_completed", hits=len(candidate_ids))
    else:
        logger.info("skipping_qdrant_search", reason="No semantic terms extracted")
        
    # NEW: Get exact skill matches from Postgres
    exact_ids = await get_exact_skill_matches(db, parsed_filter)
    
    # Combine Qdrant semantic matches and Postgres exact matches
    combined_ids = set(candidate_ids) | exact_ids

    # 3. Postgres Filter (Intersection)
    sql_query = select(Candidate, ResumeParsedData, Application).distinct(Candidate.id).join(
        Application, Application.candidate_id == Candidate.id
    ).outerjoin(
        Resume, Resume.candidate_id == Candidate.id
    ).outerjoin(
        ResumeParsedData, ResumeParsedData.resume_id == Resume.id
    ).where(
        Application.org_id == current_user.org_id
    ).order_by(
        Candidate.id, Resume.created_at.desc()
    )
    
    # Apply combined semantic & exact ID filter if any search terms were provided
    if search_text.strip():
        if combined_ids:
            sql_query = sql_query.where(Candidate.id.in_(combined_ids))
        else:
            # Search was performed but yielded zero matches; force empty result
            sql_query = sql_query.where(Candidate.id == uuid.UUID('00000000-0000-0000-0000-000000000000'))
        
    if parsed_filter.job_id:
        sql_query = sql_query.where(Application.job_id == parsed_filter.job_id)
        
    if parsed_filter.exclude_stages:
        # A simple exclusion (assuming status or stage names can be matched roughly)
        # Note: In a real app this would join PipelineStage and match names
        # We will use application.status as a proxy if it matches
        sql_query = sql_query.where(Application.status.notin_(parsed_filter.exclude_stages))
        
    db_result = await db.execute(sql_query)
    rows = db_result.all()
    
    # DEBUG LOG 3: Postgres Filtering
    postgres_out = [str(cand.id) for cand, _, _ in rows]
    logger.info("copilot_debug_stage3_postgres_filter", 
                qdrant_ids=[str(x) for x in candidate_ids],
                exact_ids=[str(x) for x in exact_ids],
                ids_coming_out=postgres_out,
                job_id_filter=parsed_filter.job_id,
                exclude_stages_filter=parsed_filter.exclude_stages)
    
    # Format results
    results = []
    for cand, parsed_data, app in rows:
        candidate_skills = parsed_data.skills if parsed_data else []
        candidate_experience = parsed_data.experience if parsed_data else []
        
        # Apply the final validation gate
        if not validate_candidate_against_filter(candidate_skills, parsed_filter):
            continue
            
        results.append({
            "candidate_id": str(cand.id),
            "name": cand.name,
            "email": cand.email,
            "application_id": str(app.id),
            "job_id": str(app.job_id),
            "status": app.status,
            "skills": candidate_skills,
            "experience": candidate_experience
        })
        
    return CopilotQueryResponse(
        interpreted_as=parsed_filter,
        results=results
    )
