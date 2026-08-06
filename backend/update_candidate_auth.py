import re

with open('app/api/v1/candidate_auth.py', 'r') as f:
    content = f.read()

# Replace get_public_jobs
old_get_jobs = """@router.get("/jobs", response_model=List[JobPublicRead])
async def get_public_jobs(db: AsyncSession = Depends(get_db)):
    # Global job board: returns all active jobs, joined with department
    from app.models.recruitment import JobStatus
    result = await db.execute(
        select(Job)
        .options(joinedload(Job.department))
        .where(Job.status == JobStatus.PUBLISHED)
        .where(Job.deleted_at.is_(None))
        .order_by(Job.created_at.desc())
    )
    return result.scalars().all()"""

new_get_jobs = """@router.get("/jobs")
async def get_candidate_jobs(
    org_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.models.recruitment import JobStatus, Job
    from app.models.ai import AIMatchResult
    from app.models.application import Application
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func
    
    # 1. Fetch authorized orgs for this candidate
    auth_orgs_res = await db.execute(select(Application.org_id).where(Application.candidate_id == current_candidate.id))
    auth_orgs = [row[0] for row in auth_orgs_res.all()]
    
    if org_id:
        if org_id not in auth_orgs:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Candidate not linked to this organization")
        target_orgs = [org_id]
    else:
        target_orgs = auth_orgs
        
    if not target_orgs:
        return []
        
    query = (
        select(Job, AIMatchResult)
        .options(joinedload(Job.department))
        .outerjoin(AIMatchResult, (AIMatchResult.job_id == Job.id) & (AIMatchResult.candidate_id == current_candidate.id))
        .where(Job.org_id.in_(target_orgs))
        .where(Job.status == JobStatus.OPEN)
        .where(Job.deleted_at.is_(None))
        .order_by(func.coalesce(AIMatchResult.match_pct, -1).desc(), Job.created_at.desc())
    )
    
    result = await db.execute(query)
    
    response = []
    for job, ai_match in result.all():
        job_dict = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "department": job.department,
            "created_at": job.created_at,
            "org_id": job.org_id,
        }
        if ai_match:
            job_dict["match_pct"] = ai_match.match_pct
            job_dict["ats_score"] = ai_match.ats_score
            job_dict["strengths"] = ai_match.strengths
            job_dict["weaknesses"] = ai_match.weaknesses
            job_dict["missing_skills"] = ai_match.missing_skills
        response.append(job_dict)
        
    return response

class AnalyzeRequest(BaseModel):
    org_id: Optional[UUID] = None

@router.post("/me/analyze")
async def trigger_analysis(
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.models.application import Application
    auth_orgs_res = await db.execute(select(Application.org_id).where(Application.candidate_id == current_candidate.id))
    auth_orgs = [row[0] for row in auth_orgs_res.all()]
    
    if payload.org_id:
        if payload.org_id not in auth_orgs:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Candidate not linked to this organization")
        target_orgs = [str(payload.org_id)]
    else:
        target_orgs = [str(o) for o in auth_orgs]
        
    if not target_orgs:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Candidate has no linked organizations")
        
    from app.workers.tasks.matching_candidate import match_jobs_for_candidate
    task = match_jobs_for_candidate.delay(str(current_candidate.id), target_orgs)
    
    return {"task_id": task.id}

@router.get("/me/analyze/status/{task_id}")
async def get_analysis_status(
    task_id: str,
    current_candidate: Candidate = Depends(get_current_candidate)
):
    from app.workers.celery_app import celery_app
    res = celery_app.AsyncResult(task_id)
    return {"status": res.status, "ready": res.ready()}
"""

if old_get_jobs in content:
    content = content.replace(old_get_jobs, new_get_jobs)
else:
    print("Could not find old_get_jobs exactly. Trying regex.")
    # More flexible replacement
    pattern = re.compile(r'@router\.get\("/jobs", response_model=List\[JobPublicRead\]\).*?return result\.scalars\(\)\.all\(\)', re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(new_get_jobs, content)
    else:
        print("Still could not find old_get_jobs.")

with open('app/api/v1/candidate_auth.py', 'w') as f:
    f.write(content)
