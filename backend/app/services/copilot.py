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

logger = structlog.get_logger()

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
            limit=50
        )
        
        for point in search_result.points:
            if "candidate_id" in point.payload:
                candidate_ids.append(uuid.UUID(point.payload["candidate_id"]))
                
        logger.info("qdrant_search_completed", hits=len(candidate_ids))
    else:
        logger.info("skipping_qdrant_search", reason="No semantic terms extracted")
        
    # 3. Postgres Filter (Intersection)
    sql_query = select(Candidate, ResumeParsedData, Application).distinct(Candidate.id).join(
        Application, Application.candidate_id == Candidate.id
    ).outerjoin(
        Resume, Resume.candidate_id == Candidate.id
    ).outerjoin(
        ResumeParsedData, ResumeParsedData.resume_id == Resume.id
    ).where(
        Application.org_id == current_user.org_id
    )
    
    if candidate_ids:
        sql_query = sql_query.where(Candidate.id.in_(candidate_ids))
        
    if parsed_filter.job_id:
        sql_query = sql_query.where(Application.job_id == parsed_filter.job_id)
        
    if parsed_filter.exclude_stages:
        # A simple exclusion (assuming status or stage names can be matched roughly)
        # Note: In a real app this would join PipelineStage and match names
        # We will use application.status as a proxy if it matches
        sql_query = sql_query.where(Application.status.notin_(parsed_filter.exclude_stages))
        
    db_result = await db.execute(sql_query)
    rows = db_result.all()
    
    # Format results
    results = []
    for cand, parsed_data, app in rows:
        # Python-side filtering for min_experience_years if needed, but for simplicity we return the hit
        # and let the frontend render it.
        results.append({
            "candidate_id": str(cand.id),
            "name": cand.name,
            "email": cand.email,
            "application_id": str(app.id),
            "job_id": str(app.job_id),
            "status": app.status,
            "skills": parsed_data.skills if parsed_data else [],
            "experience": parsed_data.experience if parsed_data else []
        })
        
    return CopilotQueryResponse(
        interpreted_as=parsed_filter,
        results=results
    )
