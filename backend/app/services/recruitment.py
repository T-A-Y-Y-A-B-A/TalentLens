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
    PipelineStageCreate, PipelineStageUpdate,
    JobEnhanceRequest, JobEnhanceResponse,
    JobBoardCard, JobBoardResponse
)
from app.core.security import enforce_role
from app.core.exceptions import DomainException
from app.ai.llm import call_llm
import structlog

logger = structlog.get_logger()

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


# --- Job AI Enhancement ---

async def enhance_job_posting(request: JobEnhanceRequest) -> JobEnhanceResponse:
    """
    Transforms rough unstructured job notes into a structured job description using AI.
    """
    system_prompt = (
        "You are an expert HR recruiter and talent acquisition specialist. "
        "Your task is to take rough unstructured notes about a job opening and generate a comprehensive, structured job posting. "
        "Extract or generate the following structured fields:\n"
        "- title: A concise, industry-standard job title\n"
        "- description: A clear, compelling overview of the role\n"
        "- salary_range: The salary or compensation range if mentioned/inferred, or null\n"
        "- company_description: A professional overview of the company culture and mission, or null\n"
        "- key_responsibilities: A list of key duties and responsibilities\n"
        "- expectations: A list of candidate qualifications, required skills, and expectations\n"
        "- benefits: A list of perks, benefits, and offerings, or null\n\n"
        "Ensure all output strictly adheres to the requested schema."
    )
    user_prompt = f"Please structure and enhance the following job notes into a complete job posting:\n\n{request.rough_notes}"
    
    try:
        response = await call_llm(
            prompt=user_prompt,
            response_model=JobEnhanceResponse,
            system_prompt=system_prompt,
            temperature=0.2,
        )
        return response
    except Exception as e:
        logger.error("job_enhancement_llm_error", error=str(e))
        raise DomainException(
            "ai_service_unavailable",
            f"AI job enhancement failed: {str(e)}",
            status_code=503,
        )

# --- Job Board ---

async def get_job_board(
    db: AsyncSession,
    candidate_id: UUID | None,
    work_type: Optional[str],
    location: Optional[str],
    salary_min: Optional[int],
    sort_by_match: bool,
    limit: int,
    offset: int
) -> tuple[List[JobBoardCard], int]:
    from sqlalchemy import func, and_
    from app.models.ai import JobMatch
    from app.models.identity import Organization
    
    count_stmt = select(func.count(Job.id)).where(Job.status == JobStatus.OPEN)
    
    stmt = (
        select(Job, JobMatch, Organization.name.label("org_name"))
        .join(Organization, Organization.id == Job.org_id)
        .outerjoin(
            JobMatch,
            and_(
                JobMatch.job_id == Job.id,
                JobMatch.candidate_id == candidate_id,
            )
        )
        .where(Job.status == JobStatus.OPEN)
    )
    
    if work_type:
        count_stmt = count_stmt.where(Job.work_type == work_type)
        stmt = stmt.where(Job.work_type == work_type)
    if location:
        count_stmt = count_stmt.where(Job.location.ilike(f"%{location}%"))
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))
    if salary_min:
        count_stmt = count_stmt.where(Job.salary_max >= salary_min)
        stmt = stmt.where(Job.salary_max >= salary_min)
        
    total_count = await db.scalar(count_stmt) or 0
    
    if sort_by_match and candidate_id:
        stmt = stmt.order_by(JobMatch.match_pct.desc().nulls_last())
    else:
        stmt = stmt.order_by(Job.created_at.desc())
        
    stmt = stmt.limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    cards = []
    for job, match, org_name in rows:
        cards.append(
            JobBoardCard(
                id=job.id,
                title=job.title,
                org_name=org_name,
                work_type=job.work_type.value if hasattr(job.work_type, 'value') else job.work_type,
                location=job.location or "Remote",
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                currency=job.currency,
                salary_period=job.salary_period,
                match_pct=match.match_pct if match else None,
                matched_skills=match.matched_skills if match else None,
                missing_skills=match.missing_skills if match else None,
                posted_at=job.created_at
            )
        )
        
    return cards, total_count

