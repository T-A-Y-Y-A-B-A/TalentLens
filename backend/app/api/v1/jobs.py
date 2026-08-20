from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission, get_current_candidate_optional
from app.models.identity import User
from app.models.candidate import Candidate
from app.models.recruitment import JobStatus
from app.schemas.recruitment import (
    JobCreate, JobUpdate, JobRead,
    PipelineStageCreate, PipelineStageRead,
    JobEnhanceRequest, JobEnhanceResponse,
    JobBoardResponse
)
from app.services.recruitment import (
    get_jobs, get_job, create_job, update_job, delete_job,
    replace_job_pipeline_stages, enhance_job_posting, get_job_board
)

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("", response_model=List[JobRead])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("jobs", "read"))
):
    return await get_jobs(db, current_user, status)

@router.get("/board", response_model=JobBoardResponse)
async def get_job_board_endpoint(
    work_type: Optional[str] = None,
    location: Optional[str] = None,
    salary_min: Optional[int] = None,
    sort_by_match: bool = False,
    limit: int = Query(20, le=100),
    offset: int = 0,
    current_candidate: Optional[Candidate] = Depends(get_current_candidate_optional),
    db: AsyncSession = Depends(get_db),
):
    candidate_id = current_candidate.id if current_candidate else None
    cards, total = await get_job_board(
        db,
        candidate_id=candidate_id,
        work_type=work_type,
        location=location,
        salary_min=salary_min,
        sort_by_match=sort_by_match,
        limit=limit,
        offset=offset
    )
    return JobBoardResponse(jobs=cards, total=total, limit=limit, offset=offset)

@router.get("/{job_id}", response_model=JobRead)
async def get_job_by_id(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_job(db, job_id, current_user)

@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_new_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_job(db, job, current_user)

@router.patch("/{job_id}", response_model=JobRead)
async def update_existing_job(
    job_id: UUID,
    job: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await update_job(db, job_id, job, current_user)

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("jobs", "delete"))
):
    await delete_job(db, job_id, current_user)

@router.put("/{job_id}/stages", response_model=List[PipelineStageRead])
async def update_pipeline_stages(
    job_id: UUID,
    stages: List[PipelineStageCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Replaces all pipeline stages for a job with the provided list.
    """
    return await replace_job_pipeline_stages(db, job_id, stages, current_user)

@router.post("/enhance", response_model=JobEnhanceResponse)
async def enhance_job_endpoint(
    request: JobEnhanceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Uses AI to transform rough job notes into a complete, structured job description.
    """
    return await enhance_job_posting(request)

