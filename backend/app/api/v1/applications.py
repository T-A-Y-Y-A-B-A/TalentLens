from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User
from app.models.application import Application
from app.models.ai import AIMatchResult
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationStageMove
from app.services.application import create_application, get_applications, get_application, move_application_stage

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application_api(
    app_in: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_application(db, app_in, current_user)

@router.get("", response_model=List[ApplicationRead])
async def list_applications_api(
    job_id: Optional[UUID] = Query(None),
    candidate_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_applications(db, current_user, job_id, candidate_id)

@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application_api(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_application(db, application_id, current_user)

@router.patch("/{application_id}/stage", response_model=ApplicationRead)
async def move_application_stage_api(
    application_id: UUID,
    move_data: ApplicationStageMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await move_application_stage(db, application_id, move_data, current_user)

@router.get("/{application_id}/match-result")
async def get_application_match_result(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the AI match result for a specific application.
    Looks up the application's candidate_id and job_id, then queries
    ai_match_results for the corresponding entry.
    """
    # Verify the application belongs to the current user's org
    app_result = await db.execute(
        select(Application)
        .where(Application.id == application_id)
        .where(Application.org_id == current_user.org_id)
    )
    application = app_result.scalars().first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Query the match result for this candidate + job combination
    match_result = await db.execute(
        select(AIMatchResult)
        .where(AIMatchResult.candidate_id == application.candidate_id)
        .where(AIMatchResult.job_id == application.job_id)
    )
    match = match_result.scalars().first()
    if not match:
        return None

    return {
        "candidate_id": str(match.candidate_id),
        "job_id": str(match.job_id),
        "match_pct": match.match_pct,
        "missing_skills": match.missing_skills,
        "strengths": match.strengths,
        "weaknesses": match.weaknesses,
        "recommendation": match.recommendation,
        "interview_questions": match.interview_questions
    }

