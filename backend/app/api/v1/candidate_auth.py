from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
import os
import aiofiles

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_candidate
from app.models.candidate import Candidate, Resume, ParseStatus
from app.models.identity import Organization
from app.models.application import Application
from app.models.recruitment import Job, PipelineStage
from app.schemas.auth import Token
from app.schemas.candidate import CandidateRead, ResumeRead
from app.schemas.application import ApplicationRead, ApplicationWithDetailsRead
from app.schemas.recruitment import JobPublicRead
from datetime import datetime, timezone

class OrganizationPublicRead(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: Optional[str] = None
    model_config = {"from_attributes": True}

router = APIRouter(prefix="/candidate-portal", tags=["candidate-portal"])

class CandidateRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    bio: Optional[str] = None

class CandidateLogin(BaseModel):
    email: EmailStr
    password: str

class CandidateApply(BaseModel):
    job_id: UUID
    name: Optional[str] = None
    phone: str
    education: List[Dict[str, Any]]
    certifications: Optional[List[Dict[str, Any]]] = None
    work_experience: Optional[List[Dict[str, Any]]] = None

    @field_validator("education")
    @classmethod
    def education_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one education entry is required")
        return v

    @field_validator("phone")
    @classmethod
    def phone_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("Phone number is required")
        return v

class CandidateProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

@router.post("/register", response_model=Token)
async def register_candidate(payload: CandidateRegister, db: AsyncSession = Depends(get_db)):
    # Check if candidate already exists globally
    result = await db.execute(
        select(Candidate)
        .where(Candidate.email == payload.email)
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Candidate already registered with this email")
        
    profile_data = {}
    if payload.bio:
        profile_data["bio"] = payload.bio

    candidate = Candidate(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        source="portal",
        profile=profile_data,
        hashed_password=get_password_hash(payload.password)
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    
    # Issue candidate-scoped JWT
    access_token = create_access_token(subject=candidate.id, additional_claims={"role": "candidate"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login_candidate(payload: CandidateLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Candidate)
        .where(Candidate.email == payload.email)
    )
    candidate = result.scalars().first()
    if not candidate or not candidate.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not verify_password(payload.password, candidate.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Issue candidate-scoped JWT
    access_token = create_access_token(subject=candidate.id, additional_claims={"role": "candidate"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/apply", response_model=ApplicationRead)
async def apply_to_job(
    payload: CandidateApply,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    # Verify job exists
    job_result = await db.execute(
        select(Job)
        .where(Job.id == payload.job_id)
    )
    job = job_result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Check if candidate has a resume
    from app.models.candidate import Resume
    resume_exists = await db.execute(select(Resume).where(Resume.candidate_id == current_candidate.id))
    if not resume_exists.scalars().first():
        raise HTTPException(status_code=400, detail="Resume is required to apply")

    # Check if already applied
    existing_result = await db.execute(
        select(Application)
        .where(Application.candidate_id == current_candidate.id)
        .where(Application.job_id == payload.job_id)
    )
    if existing_result.scalars().first():
        raise HTTPException(status_code=400, detail="You have already applied to this job")
        
    # Get first pipeline stage
    stage_result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.job_id == payload.job_id)
        .order_by(PipelineStage.order_index)
        .limit(1)
    )
    first_stage = stage_result.scalars().first()
    
    app_obj = Application(
        org_id=job.org_id,
        candidate_id=current_candidate.id,
        job_id=payload.job_id,
        current_stage_id=first_stage.id if first_stage else None,
        status="active",
        applied_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(app_obj)
    
    # Update candidate profile data
    if payload.name:
        current_candidate.name = payload.name
    if payload.phone:
        current_candidate.phone = payload.phone
        
    profile_data = dict(current_candidate.profile) if current_candidate.profile else {}
    if payload.education is not None:
        profile_data["education"] = payload.education
    if payload.certifications is not None:
        profile_data["certifications"] = payload.certifications
    if payload.work_experience is not None:
        profile_data["work_experience"] = payload.work_experience
        
    current_candidate.profile = profile_data
    
    await db.commit()
    await db.refresh(app_obj)
    
    if first_stage:
        from app.models.application import ApplicationStageHistory
        history = ApplicationStageHistory(
            application_id=app_obj.id,
            from_stage_id=None,
            to_stage_id=first_stage.id,
            moved_by=None,
            moved_at=datetime.now(timezone.utc).isoformat(),
            notes="Candidate applied via portal."
        )
        db.add(history)
        await db.commit()
        
    from app.workers.tasks.matching import match_candidates_task
    match_candidates_task.delay(str(payload.job_id))
        
    # CRITICAL FIX: Ensure Qdrant is updated with the new org_id so Copilot can find them
    from app.services.candidate_visibility import sync_candidate_qdrant_orgs
    await sync_candidate_qdrant_orgs(db, current_candidate.id)
        
    return app_obj

@router.get("/me", response_model=CandidateRead)
async def get_candidate_me(
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.models.candidate import ResumeParsedData, Resume
    result = await db.execute(
        select(Resume, ResumeParsedData)
        .outerjoin(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
        .where(Resume.candidate_id == current_candidate.id)
        .order_by(Resume.created_at.desc())
    )
    row = result.first()
    resume = row[0] if row else None
    parsed_data = row[1] if row else None
    
    # We use from_attributes, so we can just attach it to the Pydantic schema dynamically
    # or to the SQLAlchemy object. Easiest is to construct the dict and parse it.
    candidate_dict = {
        "id": current_candidate.id,
        "email": current_candidate.email,
        "name": current_candidate.name,
        "phone": current_candidate.phone,
        "source": current_candidate.source,
        "profile": current_candidate.profile,
        "created_at": current_candidate.created_at,
        "updated_at": current_candidate.updated_at,
        "parsed_data": parsed_data,
        "resume": resume
    }
    return candidate_dict

@router.patch("/profile", response_model=CandidateRead)
async def update_candidate_profile(
    payload: CandidateProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    if payload.name is not None:
        current_candidate.name = payload.name
    if payload.phone is not None:
        current_candidate.phone = payload.phone
    if payload.bio is not None:
        # Avoid overriding the entire profile dict if it has other fields
        profile = dict(current_candidate.profile) if current_candidate.profile else {}
        profile["bio"] = payload.bio
        current_candidate.profile = profile

    await db.commit()
    await db.refresh(current_candidate)
    return current_candidate

@router.post("/resume", response_model=ResumeRead, status_code=202)
async def upload_candidate_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    MAX_SIZE = 5 * 1024 * 1024
    # Check header first for fast-fail
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Payload Too Large: File size exceeds the 5MB limit.")
        
    from app.core.storage import get_s3_client, ensure_bucket_exists
    import uuid
    import io

    bucket_name = "resumes"
    ensure_bucket_exists(bucket_name)
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    safe_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Read in chunks to enforce hard cap against spoofed headers
    size = 0
    content_buffer = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_SIZE:
            raise HTTPException(status_code=413, detail="Payload Too Large: File size exceeds the 5MB limit.")
        content_buffer.extend(chunk)
        
    content = bytes(content_buffer)
    s3 = get_s3_client()
    s3.upload_fileobj(io.BytesIO(content), bucket_name, safe_filename)
        
    # We store the s3:// bucket URI style in the db
    file_url = f"s3://{bucket_name}/{safe_filename}"
        
    db_obj = Resume(
        candidate_id=current_candidate.id,
        file_url=file_url,
        parse_status=ParseStatus.PENDING
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    from app.workers.tasks.resume_parser import parse_resume
    parse_resume.delay(str(db_obj.id))
    
    return db_obj

@router.get("/resume/download")
async def download_candidate_resume(
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.core.storage import get_s3_client
    from fastapi.responses import StreamingResponse, FileResponse
    import os
    
    # Get active resume
    result = await db.execute(
        select(Resume)
        .where(Resume.candidate_id == current_candidate.id)
        .order_by(Resume.created_at.desc())
    )
    resume = result.scalars().first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found")
        
    if resume.file_url.startswith("s3://"):
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
            raise HTTPException(status_code=404, detail="File not found in storage")
    else:
        file_path = os.path.abspath(resume.file_url)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="The physical resume file was not found.")
        return FileResponse(file_path, filename=os.path.basename(file_path))

@router.get("/applications", response_model=List[ApplicationWithDetailsRead])
async def get_candidate_applications(
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.models.recruitment import Job, PipelineStage
    
    result = await db.execute(
        select(Application, Job.title, PipelineStage.name)
        .join(Job, Application.job_id == Job.id)
        .outerjoin(PipelineStage, Application.current_stage_id == PipelineStage.id)
        .where(Application.candidate_id == current_candidate.id)
        .order_by(Application.applied_at.desc())
    )
    
    applications = []
    for app_obj, job_title, stage_name in result.all():
        app_dict = {
            "id": app_obj.id,
            "candidate_id": app_obj.candidate_id,
            "job_id": app_obj.job_id,
            "current_stage_id": app_obj.current_stage_id,
            "status": app_obj.status,
            "applied_at": app_obj.applied_at,
            "org_id": app_obj.org_id,
            "created_at": app_obj.created_at,
            "updated_at": app_obj.updated_at,
            "job_title": job_title,
            "stage_name": stage_name
        }
        applications.append(app_dict)
        
    return applications

@router.get("/organizations", response_model=List[OrganizationPublicRead])
async def get_candidate_organizations(
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    result = await db.execute(select(Organization))
    return result.scalars().all()

@router.get("/jobs")
async def get_candidate_jobs(
    org_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.models.recruitment import JobStatus, Job
    from app.models.ai import JobMatch
    from app.models.candidate import Resume, ResumeParsedData
    from sqlalchemy.orm import joinedload
    
    # Check if candidate has skills (resume parsed)
    skills_res = await db.execute(
        select(ResumeParsedData.skills)
        .join(Resume, ResumeParsedData.resume_id == Resume.id)
        .where(Resume.candidate_id == current_candidate.id)
        .order_by(Resume.created_at.desc())
    )
    skills = skills_res.scalars().first()
    
    if not skills:
        return {
            "status": "resume_required",
            "message": "Upload your resume first to see matched jobs.",
            "jobs": []
        }

    # Verify org exists if org_id is provided
    if org_id:
        org_res = await db.execute(select(Organization).where(Organization.id == org_id))
        if not org_res.scalars().first():
            raise HTTPException(status_code=404, detail="Organization not found")
        
    from sqlalchemy import and_, func
    stmt = (
        select(Job, JobMatch.composite_score, JobMatch.matched_skills, JobMatch.missing_skills, Organization.name.label("organization_name"))
        .options(joinedload(Job.department))
        .join(Organization, Organization.id == Job.org_id)
        .join(
            JobMatch,
            and_(
                JobMatch.job_id == Job.id, 
                JobMatch.candidate_id == current_candidate.id,
                JobMatch.composite_score >= 35
            )
        )
        .where(Job.status == JobStatus.OPEN)
        .where(Job.deleted_at.is_(None))
        .order_by(func.coalesce(JobMatch.composite_score, 0).desc(), Job.created_at.desc())
    )
    
    if org_id:
        stmt = stmt.where(Job.org_id == org_id)
        
    result = await db.execute(stmt)
    rows = result.all()
    
    jobs_response = []
    for job, pct, matched, missing, org_name in rows:
        required_skills = (job.requirements or {}).get("required_skills", []) if isinstance(job.requirements, dict) else getattr(job.requirements, "required_skills", [])
        
        job_dict = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "department": {"name": job.department.name} if job.department else None,
            "organization_name": org_name,
            "work_type": job.work_type,
            "created_at": job.created_at,
            "org_id": job.org_id,
            "match_pct": pct,
            "matched_skills": matched if matched is not None else [],
            "missing_skills": missing if missing is not None else required_skills,
        }
        jobs_response.append(job_dict)
        
    return {
        "status": "ok",
        "jobs": jobs_response
    }

@router.get("/jobs/{job_id}/match-explanation")
async def get_match_explanation(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.models.ai import JobMatch
    from app.models.recruitment import Job
    from sqlalchemy.orm import joinedload
    
    result = await db.execute(
        select(JobMatch)
        .options(joinedload(JobMatch.job))
        .where(JobMatch.job_id == job_id)
        .where(JobMatch.candidate_id == current_candidate.id)
    )
    job_match = result.scalars().first()
    
    if not job_match:
        raise HTTPException(status_code=404, detail="No match found")
        
    # Cache Invalidation: if explanation exists AND it was generated after the last update to the match row
    if job_match.ai_explanation and job_match.ai_explanation_generated_at:
        # We need to account for timezone aware vs naive
        # SQLAlchemy stores them as naive UTC in this app (datetime.utcnow)
        if job_match.ai_explanation_generated_at >= job_match.updated_at:
            return {"explanation": job_match.ai_explanation, "cached": True}
            
    from app.workers.tasks.match_explanation import generate_match_explanation
    
    explanation = await generate_match_explanation(job_match, job_match.job)
    
    job_match.ai_explanation = explanation
    job_match.ai_explanation_generated_at = datetime.utcnow()
    await db.commit()
    
    return {"explanation": explanation, "cached": False}

class AnalyzeRequest(BaseModel):
    org_id: UUID

@router.post("/me/analyze")
async def trigger_analysis(
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    # Verify org exists
    org_res = await db.execute(select(Organization).where(Organization.id == payload.org_id))
    if not org_res.scalars().first():
        raise HTTPException(status_code=404, detail="Organization not found")
        
    from app.workers.tasks.matching_candidate import match_jobs_for_candidate
    task = match_jobs_for_candidate.delay(str(current_candidate.id), [str(payload.org_id)])
    
    return {"task_id": task.id}

@router.get("/me/analyze/status/{task_id}")
async def get_analysis_status(
    task_id: str,
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.workers.celery_app import celery_app
    res = celery_app.AsyncResult(task_id)
    return {"status": res.status, "ready": res.ready()}
@router.get("/oauth/google/login")
async def google_login(request: Request):
    from app.core.config import settings
    from app.api.v1.auth import oauth
    import json
    import base64
    
    origin = request.query_params.get("from", "/portal/dashboard")
    state_data = json.dumps({"from": origin})
    state = base64.urlsafe_b64encode(state_data.encode()).decode().rstrip('=')
    
    redirect_uri = settings.GOOGLE_CANDIDATE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)

@router.get("/oauth/google/callback")
async def google_auth(request: Request, code: str, state: str, db: AsyncSession = Depends(get_db)):
    from app.core.config import settings
    from app.models.identity import User
    from app.core.security import create_access_token
    import json
    import base64
    import httpx
    
    origin = "/portal/dashboard"
    try:
        padded_state = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(padded_state))
        origin = state_data.get("from", "/portal/dashboard")
    except Exception:
        pass

    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_CANDIDATE_REDIRECT_URI
            })
            token_resp.raise_for_status()
            token_data = token_resp.json()
            
            userinfo_resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={
                "Authorization": f"Bearer {token_data['access_token']}"
            })
            userinfo_resp.raise_for_status()
            user_info = userinfo_resp.json()
            
        if not user_info or 'email' not in user_info:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
            
        email = user_info['email']
        first_name = user_info.get('given_name', 'Candidate')
        last_name = user_info.get('family_name', '')
        full_name = f"{first_name} {last_name}".strip()
        oauth_id = user_info.get('sub')
        
        # Security: Prevent HR users from logging in via Candidate portal
        staff_result = await db.execute(select(User).where(User.email == email))
        if staff_result.scalars().first():
            raise HTTPException(status_code=403, detail="Email is registered as HR. You cannot access the Candidate portal with this account.")
            
        result = await db.execute(select(Candidate).where(Candidate.email == email))
        candidate = result.scalars().first()
        
        if not candidate:
            candidate = Candidate(
                name=full_name,
                email=email,
                source="google_oauth",
                profile={"google_id": oauth_id},
                hashed_password=None
            )
            db.add(candidate)
            await db.commit()
            await db.refresh(candidate)
            
        access_token = create_access_token(subject=candidate.id, additional_claims={"role": "candidate"})
        
        from fastapi.responses import RedirectResponse
        frontend_url = f"{settings.FRONTEND_URL}{origin}?auth=success&token={access_token}&uid={candidate.id}"
        return RedirectResponse(url=frontend_url)
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_candidate_account(
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    """
    Candidate soft-deletes their own account.

    - Sets Candidate.deleted_at = now().
    - Cascades: all non-terminal Applications (not withdrawn/rejected/hired)
      are set to status='withdrawn'.
    - Both mutations are committed in one transaction.

    After a 204 the frontend MUST clear the JWT and redirect to /portal/login.
    The token is now invalid because the candidate is soft-deleted; any subsequent
    request using the old token will fail with 401 (get_current_candidate checks
    the Candidate row exists and is not soft-deleted).
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == current_candidate.id)
        .where(Candidate.deleted_at.is_(None))
    )
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Account not found")

    now = datetime.now(timezone.utc)
    candidate.deleted_at = now

    # Cascade: withdraw all non-terminal applications
    terminal_statuses = ("withdrawn", "rejected", "hired")
    await db.execute(
        update(Application)
        .where(Application.candidate_id == current_candidate.id)
        .where(Application.status.notin_(terminal_statuses))
        .values(status="withdrawn")
    )

    # Single commit covers both candidate soft-delete and application cascade
    await db.commit()
