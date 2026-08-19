from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.identity import User
from app.models.recruitment import Department, Job, PipelineStage, JobStatus
from app.schemas.recruitment import (
    DepartmentCreate, DepartmentUpdate,
    JobCreate, JobUpdate,
    PipelineStageCreate, PipelineStageUpdate
)
from app.core.security import enforce_role
from app.core.exceptions import DomainException

# --- Default Pipeline Stages ---
DEFAULT_PIPELINE_STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]


async def get_departments(db: AsyncSession, current_user: User) -> List[Department]:
    enforce_role(current_user.role.value, "departments", "read")
    result = await db.execute(
        select(Department)
        .where(Department.org_id == current_user.org_id)
        .where(Department.deleted_at.is_(None))
    )
    return list(result.scalars().all())


async def create_department(db: AsyncSession, obj_in: DepartmentCreate, current_user: User) -> Department:
    enforce_role(current_user.role.value, "departments", "manage")
    
    db_obj = Department(
        name=obj_in.name,
        org_id=current_user.org_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_department(db: AsyncSession, dept_id: UUID, obj_in: DepartmentUpdate, current_user: User) -> Department:
    enforce_role(current_user.role.value, "departments", "manage")
    
    result = await db.execute(
        select(Department)
        .where(Department.id == dept_id)
        .where(Department.org_id == current_user.org_id)
        .where(Department.deleted_at.is_(None))
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("department_not_found", "Department not found", status_code=404)
        
    if obj_in.name is not None:
        db_obj.name = obj_in.name
        
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_department(db: AsyncSession, dept_id: UUID, current_user: User):
    """
    Soft deletes a department.
    All jobs associated with this department will have their department_id set to NULL (detached).
    """
    enforce_role(current_user.role.value, "departments", "manage")
    
    result = await db.execute(
        select(Department)
        .where(Department.id == dept_id)
        .where(Department.org_id == current_user.org_id)
        .where(Department.deleted_at.is_(None))
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("department_not_found", "Department not found", status_code=404)
        
    # Soft delete department
    db_obj.deleted_at = datetime.utcnow()
    
    # Detach jobs from this department
    await db.execute(
        update(Job)
        .where(Job.department_id == dept_id)
        .where(Job.org_id == current_user.org_id)
        .values(department_id=None)
    )
    
    await db.commit()


# --- Jobs ---


async def get_jobs(db: AsyncSession, current_user: User, status: Optional[JobStatus] = None) -> List[Job]:
    enforce_role(current_user.role.value, "jobs", "read")
    
    from sqlalchemy.orm import selectinload
    query = (
        select(Job)
        .options(selectinload(Job.pipeline_stages))
        .where(Job.org_id == current_user.org_id)
        .where(Job.deleted_at.is_(None))
    )
    if status:
        query = query.where(Job.status == status)
        
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_job(db: AsyncSession, job_id: UUID, current_user: User) -> Job:
    enforce_role(current_user.role.value, "jobs", "read")
    
    # Explicitly join pipeline stages to ensure they are loaded if accessed
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.pipeline_stages))
        .where(Job.id == job_id)
        .where(Job.org_id == current_user.org_id)
        .where(Job.deleted_at.is_(None))
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("job_not_found", "Job not found", status_code=404)
        
    return db_obj


async def create_job(db: AsyncSession, obj_in: JobCreate, current_user: User) -> Job:
    enforce_role(current_user.role.value, "jobs", "create")
    
    if obj_in.department_id:
        dept = await db.execute(
            select(Department)
            .where(Department.id == obj_in.department_id)
            .where(Department.org_id == current_user.org_id)
            .where(Department.deleted_at.is_(None))
        )
        if not dept.scalars().first():
            raise DomainException("department_not_found", "Department not found", status_code=404)

    db_obj = Job(
        title=obj_in.title,
        description=obj_in.description,
        requirements=obj_in.requirements.model_dump() if hasattr(obj_in.requirements, "model_dump") else obj_in.requirements,
        work_type=obj_in.work_type,
        status=obj_in.status,
        department_id=obj_in.department_id,
        location=obj_in.location,
        salary_range=obj_in.salary_range,
        company_description=obj_in.company_description,
        key_responsibilities=obj_in.key_responsibilities,
        expectations=obj_in.expectations,
        benefits=obj_in.benefits,
        created_by=current_user.id,
        org_id=current_user.org_id
    )
    db.add(db_obj)
    await db.flush()  # To get db_obj.id generated
    
    # Auto-populate default pipeline stages
    for index, stage_name in enumerate(DEFAULT_PIPELINE_STAGES):
        stage = PipelineStage(
            job_id=db_obj.id,
            name=stage_name,
            order_index=index
        )
        db.add(stage)
        
    await db.commit()
    
    # Reload with pipeline stages to prevent MissingGreenlet error on serialization
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.pipeline_stages))
        .where(Job.id == db_obj.id)
    )
    final_job = result.scalars().first()
    
    from app.workers.tasks.keyword_matching import match_job_to_all_candidates
    match_job_to_all_candidates.delay(str(final_job.id))
    
    return final_job


async def update_job(db: AsyncSession, job_id: UUID, obj_in: JobUpdate, current_user: User) -> Job:
    enforce_role(current_user.role.value, "jobs", "update")
    
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.org_id == current_user.org_id)
        .where(Job.deleted_at.is_(None))
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("job_not_found", "Job not found", status_code=404)
        
    if obj_in.department_id:
        dept = await db.execute(
            select(Department)
            .where(Department.id == obj_in.department_id)
            .where(Department.org_id == current_user.org_id)
            .where(Department.deleted_at.is_(None))
        )
        if not dept.scalars().first():
            raise DomainException("department_not_found", "Department not found", status_code=404)

    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    await db.commit()
    
    # Reload with pipeline stages
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.pipeline_stages))
        .where(Job.id == db_obj.id)
    )
    final_job = result.scalars().first()
    
    from app.workers.tasks.keyword_matching import match_job_to_all_candidates
    match_job_to_all_candidates.delay(str(final_job.id))
    
    return final_job


async def delete_job(db: AsyncSession, job_id: UUID, current_user: User):
    enforce_role(current_user.role.value, "jobs", "delete")
    
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.org_id == current_user.org_id)
        .where(Job.deleted_at.is_(None))
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("job_not_found", "Job not found", status_code=404)
        
    db_obj.deleted_at = datetime.utcnow()
    await db.commit()


# --- Pipeline Stages ---

async def replace_job_pipeline_stages(db: AsyncSession, job_id: UUID, stages_in: List[PipelineStageCreate], current_user: User) -> List[PipelineStage]:
    """
    Replaces all pipeline stages for a given job with the provided stages list.
    """
    enforce_role(current_user.role.value, "jobs", "manage")
    
    # Verify job exists and user has access
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.org_id == current_user.org_id)
        .where(Job.deleted_at.is_(None))
    )
    job = result.scalars().first()
    if not job:
        raise DomainException("job_not_found", "Job not found", status_code=404)
        
    # Delete existing stages
    from sqlalchemy import delete
    await db.execute(
        delete(PipelineStage)
        .where(PipelineStage.job_id == job_id)
    )
    
    # Add new stages
    new_stages = []
    for stage_in in stages_in:
        stage = PipelineStage(
            job_id=job_id,
            name=stage_in.name,
            order_index=stage_in.order_index
        )
        db.add(stage)
        new_stages.append(stage)
        
    await db.commit()
    
    # Refresh newly added stages to get their IDs
    for stage in new_stages:
        await db.refresh(stage)
        
    return new_stages
