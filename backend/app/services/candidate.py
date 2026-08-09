from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.candidate import Candidate
from app.models.identity import User
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.core.security import enforce_role
from app.core.exceptions import DomainException
from fastapi import UploadFile
import os
import aiofiles
from app.models.candidate import Resume, ParseStatus
from app.workers.tasks.resume_parser import parse_resume

async def create_candidate(db: AsyncSession, obj_in: CandidateCreate, current_user: User) -> Candidate:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    profile = dict(obj_in.profile) if obj_in.profile else {}
    profile["created_org_id"] = str(current_user.org_id)
    
    db_obj = Candidate(
        email=obj_in.email,
        name=obj_in.name,
        phone=obj_in.phone,
        source=obj_in.source,
        profile=profile,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_candidates(db: AsyncSession, current_user: User) -> List[Candidate]:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    from app.models.application import Application
    result = await db.execute(
        select(Candidate).distinct()
        .options(selectinload(Candidate.resumes))
        .join(Application, Application.candidate_id == Candidate.id)
        .where(Application.org_id == current_user.org_id)
    )
    return result.scalars().all()

async def get_candidate(db: AsyncSession, candidate_id: UUID, current_user: User) -> Candidate:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    from app.models.application import Application
    result = await db.execute(
        select(Candidate)
        .options(selectinload(Candidate.resumes))
        .where(Candidate.id == candidate_id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("candidate_not_found", "Candidate not found", status_code=404)
        
    # Check org isolation: if candidate has applications or created_org_id, verify match
    app_res = await db.execute(
        select(Application.org_id).where(Application.candidate_id == candidate_id)
    )
    org_ids = [str(row) for row in app_res.scalars().all()]
    if db_obj.profile and isinstance(db_obj.profile, dict) and "created_org_id" in db_obj.profile:
        org_ids.append(str(db_obj.profile["created_org_id"]))
        
    if org_ids and str(current_user.org_id) not in org_ids:
        raise DomainException("candidate_not_found", "Candidate not found", status_code=404)
        
    return db_obj



async def update_candidate(db: AsyncSession, candidate_id: UUID, obj_in: CandidateUpdate, current_user: User) -> Candidate:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    db_obj = await get_candidate(db, candidate_id, current_user)
    
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def upload_resume(db: AsyncSession, candidate_id: UUID, file: UploadFile, current_user: User) -> Resume:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    candidate = await get_candidate(db, candidate_id, current_user)
    
    # Store locally for now
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    import uuid
    safe_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        
    # We store the absolute path or a relative path. For this MVP, absolute is easiest for Celery
    # But plan says relative path saved to DB.
    # We will save relative to CWD.
    rel_path = os.path.join("uploads", safe_filename)
        
    # Enforce one resume per candidate: delete old resumes
    await db.execute(delete(Resume).where(Resume.candidate_id == candidate.id))
    await db.commit()
    
    db_obj = Resume(
        candidate_id=candidate.id,
        file_url=rel_path,
        parse_status=ParseStatus.PENDING
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    # Trigger Celery Task
    parse_resume.delay(str(db_obj.id))
    
    return db_obj

async def get_resume_by_id(db: AsyncSession, candidate_id: UUID, resume_id: UUID, current_user: User) -> Resume:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    # Verify candidate first (checks tenant isolation)
    candidate = await get_candidate(db, candidate_id, current_user)
    
    result = await db.execute(
        select(Resume)
        .where(Resume.id == resume_id)
        .where(Resume.candidate_id == candidate.id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("resume_not_found", "Resume not found", status_code=404)
        
    return db_obj
