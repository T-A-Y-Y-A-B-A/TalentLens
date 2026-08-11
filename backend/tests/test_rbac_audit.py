import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.core.security import get_casbin_enforcer
from app.models.identity import User, UserRole
from app.models.recruitment import Job, Candidate, Application, Interview, Department

@pytest.mark.asyncio
async def test_casbin_inheritance_and_rules():
    enforcer = get_casbin_enforcer()
    # Test Casbin inheritance: hr_manager inherits from recruiter
    
    # Recruiter permissions on jobs
    assert enforcer.enforce("recruiter", "jobs", "read") == True
    assert enforcer.enforce("recruiter", "jobs", "create") == True
    assert enforcer.enforce("recruiter", "jobs", "update") == True
    assert enforcer.enforce("recruiter", "jobs", "delete") == False
    
    # HR Manager permissions on jobs
    assert enforcer.enforce("hr_manager", "jobs", "read") == True
    assert enforcer.enforce("hr_manager", "jobs", "create") == True
    assert enforcer.enforce("hr_manager", "jobs", "update") == True
    assert enforcer.enforce("hr_manager", "jobs", "manage") == True
    assert enforcer.enforce("hr_manager", "jobs", "delete") == True # delete might be part of manage, or explicitly defined? Wait, if they have 'manage' or 'delete'. Casbin usually needs explicit if not using wildcard, but let's test what policy we have.

@pytest.fixture
async def rbac_users(async_client: AsyncClient, db_session: AsyncSession):
    # Org A: HR Manager
    email_hr_a = f"hr_{uuid.uuid4().hex[:8]}@a.com"
    org_a = f"Org A {uuid.uuid4().hex[:6]}"
    await async_client.post("/api/v1/auth/register", json={"email": email_hr_a, "password": "Pass123!", "org_name": org_a})
    
    # Org A: Recruiter
    email_rec_a = f"rec_{uuid.uuid4().hex[:8]}@a.com"
    await async_client.post("/api/v1/auth/register", json={"email": email_rec_a, "password": "Pass123!", "org_name": f"Dummy Org {uuid.uuid4().hex[:6]}"})
    
    # Org A: Interviewer 1
    email_int_1 = f"int1_{uuid.uuid4().hex[:8]}@a.com"
    await async_client.post("/api/v1/auth/register", json={"email": email_int_1, "password": "Pass123!", "org_name": f"Dummy Org {uuid.uuid4().hex[:6]}"})

    # Org A: Interviewer 2
    email_int_2 = f"int2_{uuid.uuid4().hex[:8]}@a.com"
    await async_client.post("/api/v1/auth/register", json={"email": email_int_2, "password": "Pass123!", "org_name": f"Dummy Org {uuid.uuid4().hex[:6]}"})
    
    users = []
    roles = [UserRole.HR_MANAGER, UserRole.RECRUITER, UserRole.INTERVIEWER, UserRole.INTERVIEWER]
    emails = [email_hr_a, email_rec_a, email_int_1, email_int_2]
    
    for email, role in zip(emails, roles):
        result = await db_session.execute(select(User).where(User.email == email))
        db_user = result.scalars().first()
        db_user.is_verified = True
        db_user.role = role
        users.append(db_user)
        
    # Put everyone in Org A
    users[1].org_id = users[0].org_id
    users[2].org_id = users[0].org_id
    users[3].org_id = users[0].org_id
    
    await db_session.commit()
    
    async def login(email):
        resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": "Pass123!"})
        return resp.json()["access_token"]
        
    return {
        "hr_a": {"email": email_hr_a, "headers": {"Authorization": f"Bearer {await login(email_hr_a)}"}, "user": users[0]},
        "rec_a": {"email": email_rec_a, "headers": {"Authorization": f"Bearer {await login(email_rec_a)}"}, "user": users[1]},
        "int_1": {"email": email_int_1, "headers": {"Authorization": f"Bearer {await login(email_int_1)}"}, "user": users[2]},
        "int_2": {"email": email_int_2, "headers": {"Authorization": f"Bearer {await login(email_int_2)}"}, "user": users[3]}
    }

@pytest.mark.asyncio
async def test_recruiter_cannot_delete_job(async_client: AsyncClient, rbac_users):
    # HR creates a job
    resp = await async_client.post("/api/v1/departments", json={"name": "Engineering"}, headers=rbac_users["hr_a"]["headers"])
    dept_id = resp.json()["id"]
    
    resp = await async_client.post("/api/v1/jobs", json={"title": "SWE", "description": "Dev", "department_id": dept_id}, headers=rbac_users["hr_a"]["headers"])
    job_id = resp.json()["id"]
    
    # Recruiter tries to delete the job
    resp = await async_client.delete(f"/api/v1/jobs/{job_id}", headers=rbac_users["rec_a"]["headers"])
    assert resp.status_code == 403
    
    # HR can delete the job
    resp = await async_client.delete(f"/api/v1/jobs/{job_id}", headers=rbac_users["hr_a"]["headers"])
    assert resp.status_code == 204

@pytest.mark.asyncio
async def test_interviewer_access_to_interview_and_candidate(async_client: AsyncClient, db_session: AsyncSession, rbac_users):
    # HR creates a job, candidate, application, and interview for int_1
    hr_headers = rbac_users["hr_a"]["headers"]
    
    resp = await async_client.post("/api/v1/jobs", json={"title": "SWE", "description": "Dev"}, headers=hr_headers)
    job_id = resp.json()["id"]
    
    # We will manually create candidate and interview in DB since some endpoints might be mocked or complex
    # Let's create it directly via DB to simplify setup
    candidate_1 = Candidate(
        org_id=rbac_users["hr_a"]["user"].org_id,
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        resume_text="Good dev"
    )
    db_session.add(candidate_1)
    await db_session.flush()
    
    candidate_2 = Candidate(
        org_id=rbac_users["hr_a"]["user"].org_id,
        first_name="Bob",
        last_name="Jones",
        email="bob@example.com",
        resume_text="Great dev"
    )
    db_session.add(candidate_2)
    await db_session.flush()
    
    app_1 = Application(
        candidate_id=candidate_1.id,
        job_id=job_id,
        stage="Interview"
    )
    db_session.add(app_1)
    
    app_2 = Application(
        candidate_id=candidate_2.id,
        job_id=job_id,
        stage="Interview"
    )
    db_session.add(app_2)
    await db_session.flush()
    
    interview_1 = Interview(
        application_id=app_1.id,
        interviewer_id=rbac_users["int_1"]["user"].id,
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        duration_minutes=60,
        meeting_link="http://zoom.us/j/123",
        status="scheduled"
    )
    db_session.add(interview_1)
    
    interview_2 = Interview(
        application_id=app_2.id,
        interviewer_id=rbac_users["int_2"]["user"].id,
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        duration_minutes=60,
        meeting_link="http://zoom.us/j/456",
        status="scheduled"
    )
    db_session.add(interview_2)
    await db_session.commit()
    
    # int_1 tries to access interview_1
    resp = await async_client.get(f"/api/v1/interviews/{interview_1.id}", headers=rbac_users["int_1"]["headers"])
    assert resp.status_code == 200
    
    # int_1 tries to access interview_2
    resp = await async_client.get(f"/api/v1/interviews/{interview_2.id}", headers=rbac_users["int_1"]["headers"])
    assert resp.status_code == 403
    
    # int_1 tries to access candidate_1
    resp = await async_client.get(f"/api/v1/candidates/{candidate_1.id}", headers=rbac_users["int_1"]["headers"])
    assert resp.status_code == 200
    
    # int_1 tries to access candidate_2
    resp = await async_client.get(f"/api/v1/candidates/{candidate_2.id}", headers=rbac_users["int_1"]["headers"])
    assert resp.status_code == 403
