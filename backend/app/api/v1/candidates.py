from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.models.identity import User
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateRead, ResumeRead
from app.services.candidate import create_candidate, get_candidates, get_candidate, update_candidate, get_resume_by_id, upload_resume

router = APIRouter(prefix="/candidates", tags=["candidates"])

@router.post("", response_model=CandidateRead, status_code=201)
async def create_candidate_api(
    candidate_in: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("candidates", "manage"))
):
    return await create_candidate(db, candidate_in, current_user)

@router.get("", response_model=List[CandidateRead])
async def list_candidates_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("candidates", "read"))
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

@router.post("/{candidate_id}/resume", response_model=ResumeRead, status_code=202)
async def upload_resume_api(
    candidate_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.candidate import upload_resume
    return await upload_resume(db, candidate_id, file, current_user)

@router.get("/{candidate_id}/resume/{resume_id}/download")
async def download_resume_api(
    candidate_id: UUID,
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.candidate import get_resume_by_id
    from fastapi.responses import FileResponse, StreamingResponse
    import os
    
    resume = await get_resume_by_id(db, candidate_id, resume_id, current_user)
    
    if resume.file_url.startswith("s3://"):
        from app.core.storage import get_s3_client
        bucket_name, object_name = resume.file_url.replace("s3://", "").split("/", 1)
        s3 = get_s3_client()
        try:
            obj = s3.get_object(Bucket=bucket_name, Key=object_name)
            return StreamingResponse(
                obj["Body"].iter_chunks(),
                media_type=obj.get("ContentType", "application/pdf"),
                headers={"Content-Disposition": f'inline; filename="{object_name}"'}
            )
        except Exception as e:
            from app.core.exceptions import DomainException
            raise DomainException("file_not_found", "File not found in storage", status_code=404)
    else:
        file_path = os.path.abspath(resume.file_url)
        if not os.path.exists(file_path):
            from app.core.exceptions import DomainException
            raise DomainException("file_not_found", "The physical resume file was not found.", status_code=404)
        return FileResponse(file_path, filename=os.path.basename(file_path))

@router.get("/{candidate_id}/resume/{resume_id}/parsed")
async def get_parsed_data_api(
    candidate_id: UUID,
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.candidate import get_resume_by_id
    from app.models.candidate import ResumeParsedData
    from sqlalchemy import select
    
    await get_resume_by_id(db, candidate_id, resume_id, current_user)
    
    result = await db.execute(
        select(ResumeParsedData).where(ResumeParsedData.resume_id == resume_id)
    )
    return result.scalars().first()
