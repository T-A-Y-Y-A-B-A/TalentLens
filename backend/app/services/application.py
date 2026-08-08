from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.models.application import Application, ApplicationStageHistory
from app.models.recruitment import Job, PipelineStage
from app.models.identity import User
from app.schemas.application import ApplicationCreate, ApplicationStageMove
from app.core.security import enforce_role
from app.core.exceptions import DomainException
from app.services.candidate import get_candidate

async def create_application(db: AsyncSession, obj_in: ApplicationCreate, current_user: User) -> Application:
    enforce_role(current_user.role.value, "applications", "manage")
    
    # Verify candidate exists and belongs to org
    candidate = await get_candidate(db, obj_in.candidate_id, current_user)
    
    # Verify job exists and belongs to org
    job_result = await db.execute(
        select(Job)
        .where(Job.id == obj_in.job_id)
        .where(Job.org_id == current_user.org_id)
        .where(Job.deleted_at.is_(None))
    )
    job = job_result.scalars().first()
    if not job:
        raise DomainException("job_not_found", "Job not found", status_code=404)
        
    # Check if application already exists for this candidate + job
    existing_result = await db.execute(
        select(Application)
        .where(Application.candidate_id == obj_in.candidate_id)
        .where(Application.job_id == obj_in.job_id)
        .where(Application.org_id == current_user.org_id)
    )
    if existing_result.scalars().first():
        raise DomainException("application_exists", "Candidate has already applied to this job", status_code=400)
    
    # Get the first pipeline stage for this job (order_index == 0)
    stage_result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.job_id == obj_in.job_id)
        .order_by(PipelineStage.order_index)
        .limit(1)
    )
    first_stage = stage_result.scalars().first()
    first_stage_id = first_stage.id if first_stage else None
    
    now_iso = datetime.now(timezone.utc).isoformat()
    
    db_obj = Application(
        org_id=current_user.org_id,
        candidate_id=obj_in.candidate_id,
        job_id=obj_in.job_id,
        current_stage_id=first_stage_id,
        status="active",
        applied_at=now_iso
    )
    db.add(db_obj)
    await db.commit() # Commit to generate the application ID
    await db.refresh(db_obj)
    
    if first_stage_id:
        history = ApplicationStageHistory(
            application_id=db_obj.id,
            from_stage_id=None,
            to_stage_id=first_stage_id,
            moved_by=current_user.id,
            moved_at=now_iso,
            notes="Initial application created."
        )
        db.add(history)
        await db.commit()
        
    from app.services.candidate_visibility import sync_candidate_qdrant_orgs
    await sync_candidate_qdrant_orgs(db, db_obj.candidate_id)
        
    return db_obj

async def get_applications(db: AsyncSession, current_user: User, job_id: Optional[UUID] = None, candidate_id: Optional[UUID] = None) -> List[Application]:
    enforce_role(current_user.role.value, "applications", "manage")
    
    query = select(Application).where(Application.org_id == current_user.org_id)
    
    if job_id:
        query = query.where(Application.job_id == job_id)
    if candidate_id:
        query = query.where(Application.candidate_id == candidate_id)
        
    result = await db.execute(query)
    return result.scalars().all()

async def get_application(db: AsyncSession, application_id: UUID, current_user: User) -> Application:
    enforce_role(current_user.role.value, "applications", "manage")
    
    result = await db.execute(
        select(Application)
        .where(Application.id == application_id)
        .where(Application.org_id == current_user.org_id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("application_not_found", "Application not found", status_code=404)
        
    return db_obj

async def move_application_stage(db: AsyncSession, application_id: UUID, move_data: ApplicationStageMove, current_user: User) -> Application:
    enforce_role(current_user.role.value, "applications", "manage")
    
    application = await get_application(db, application_id, current_user)
    
    # Verify the target stage belongs to the job
    stage_result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.id == move_data.to_stage_id)
        .where(PipelineStage.job_id == application.job_id)
    )
    target_stage = stage_result.scalars().first()
    if not target_stage:
        raise DomainException("invalid_stage", "Target stage does not belong to this job", status_code=400)
        
    if application.current_stage_id == move_data.to_stage_id:
        raise DomainException("same_stage", "Application is already in this stage", status_code=400)
        
    old_stage_id = application.current_stage_id
    application.current_stage_id = move_data.to_stage_id
    
    now_iso = datetime.now(timezone.utc).isoformat()
    
    history = ApplicationStageHistory(
        application_id=application.id,
        from_stage_id=old_stage_id,
        to_stage_id=move_data.to_stage_id,
        moved_by=current_user.id,
        moved_at=now_iso,
        notes=move_data.notes
    )
    
    db.add(history)
    await db.commit()
    await db.refresh(application)
    
    return application
