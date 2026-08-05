from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User
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

@router.put("/{application_id}/stage", response_model=ApplicationRead)
async def move_application_stage_api(
    application_id: UUID,
    move_data: ApplicationStageMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await move_application_stage(db, application_id, move_data, current_user)
