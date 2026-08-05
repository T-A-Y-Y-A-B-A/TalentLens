from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateRead
from app.services.candidate import create_candidate, get_candidates, get_candidate, update_candidate

router = APIRouter(prefix="/candidates", tags=["candidates"])

@router.post("", response_model=CandidateRead, status_code=201)
async def create_candidate_api(
    candidate_in: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_candidate(db, candidate_in, current_user)

@router.get("", response_model=List[CandidateRead])
async def list_candidates_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_candidates(db, current_user)

@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate_api(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_candidate(db, candidate_id, current_user)

@router.patch("/{candidate_id}", response_model=CandidateRead)
async def update_candidate_api(
    candidate_id: UUID,
    candidate_in: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await update_candidate(db, candidate_id, candidate_in, current_user)
