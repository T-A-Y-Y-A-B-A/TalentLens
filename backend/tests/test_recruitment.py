import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity import User, UserRole
from app.models.recruitment import Department, Job

@pytest.fixture
async def setup_users(async_client: AsyncClient, db_session: AsyncSession):
    # Org A: HR Manager
    email_hr_a = f"hra_{uuid.uuid4().hex[:8]}@a.com"
    org_a = f"Org A {uuid.uuid4().hex[:6]}"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_hr_a, "password": "Pass123!", "org_name": org_a})
    hr_a_data = resp.json()
    
    # Org A: Recruiter
    email_rec_a = f"reca_{uuid.uuid4().hex[:8]}@a.com"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_rec_a, "password": "Pass123!", "org_name": f"Dummy Org {uuid.uuid4().hex[:6]}"})
    rec_a_data = resp.json()
    
    # Org B: HR Manager
    email_hr_b = f"hrb_{uuid.uuid4().hex[:8]}@b.com"
    org_b = f"Org B {uuid.uuid4().hex[:6]}"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_hr_b, "password": "Pass123!", "org_name": org_b})
    hr_b_data = resp.json()
    
    # Org A: Interviewer
    email_int_a = f"inta_{uuid.uuid4().hex[:8]}@a.com"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_int_a, "password": "Pass123!", "org_name": f"Dummy Org {uuid.uuid4().hex[:6]}"})
    int_a_data = resp.json()
    
    # Verify and set roles
    users = []
    for email, role in [(email_hr_a, UserRole.HR_MANAGER), (email_rec_a, UserRole.RECRUITER), (email_hr_b, UserRole.HR_MANAGER), (email_int_a, UserRole.INTERVIEWER)]:
        result = await db_session.execute(select(User).where(User.email == email))
        db_user = result.scalars().first()
        db_user.is_verified = True
        db_user.role = role
        users.append(db_user)
        
    # Put Recruiter A and Interviewer A in Org A
    users[1].org_id = users[0].org_id
    users[3].org_id = users[0].org_id
    
    await db_session.commit()
    
    async def login(email, pwd):
        resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        return resp.json()["access_token"]
        
    token_hr_a = await login(email_hr_a, "Pass123!")
    token_rec_a = await login(email_rec_a, "Pass123!")
    token_hr_b = await login(email_hr_b, "Pass123!")
    token_int_a = await login(email_int_a, "Pass123!")

    return {
        "hr_a": {"email": email_hr_a, "token": token_hr_a, "headers": {"Authorization": f"Bearer {token_hr_a}"}, "org_id": users[0].org_id},
        "rec_a": {"email": email_rec_a, "token": token_rec_a, "headers": {"Authorization": f"Bearer {token_rec_a}"}, "org_id": users[1].org_id},
        "hr_b": {"email": email_hr_b, "token": token_hr_b, "headers": {"Authorization": f"Bearer {token_hr_b}"}, "org_id": users[2].org_id},
        "int_a": {"email": email_int_a, "token": token_int_a, "headers": {"Authorization": f"Bearer {token_int_a}"}, "org_id": users[3].org_id}
    }


@pytest.mark.asyncio
async def test_rbac_recruiter_blocked(async_client: AsyncClient, setup_users):
    headers_rec_a = setup_users["rec_a"]["headers"]
    
    resp = await async_client.post("/api/v1/departments", json={"name": "Engineering"}, headers=headers_rec_a)
    assert resp.status_code == 403
    
    resp = await async_client.post("/api/v1/jobs", json={"title": "SWE", "description": "Dev"}, headers=headers_rec_a)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_job_creation_seeds_pipeline(async_client: AsyncClient, setup_users):
    headers_hr_a = setup_users["hr_a"]["headers"]
    
    # Create dept
    resp = await async_client.post("/api/v1/departments", json={"name": "Engineering"}, headers=headers_hr_a)
    assert resp.status_code == 201
    dept_a_id = resp.json()["id"]
    
    # Create job
    resp = await async_client.post("/api/v1/jobs", json={
        "title": "Senior Engineer",
        "description": "Code things",
        "department_id": dept_a_id
    }, headers=headers_hr_a)
    assert resp.status_code == 201
    job_a_data = resp.json()
    
    # Verify default pipeline stages populated correctly
    stages = job_a_data.get("pipeline_stages", [])
    assert len(stages) == 6
    assert stages[0]["name"] == "Applied"
    assert stages[0]["order_index"] == 0
    assert stages[1]["name"] == "Screening"
    assert stages[1]["order_index"] == 1


@pytest.mark.asyncio
async def test_tenant_isolation_jobs(async_client: AsyncClient, setup_users):
    headers_hr_a = setup_users["hr_a"]["headers"]
    headers_hr_b = setup_users["hr_b"]["headers"]
    headers_rec_a = setup_users["rec_a"]["headers"]
    
    # HR A creates job
    resp_a = await async_client.post("/api/v1/jobs", json={"title": "Job A", "description": "Desc A"}, headers=headers_hr_a)
    job_a_id = resp_a.json()["id"]

    # HR B creates job
    resp_b = await async_client.post("/api/v1/jobs", json={"title": "Job B", "description": "Desc B"}, headers=headers_hr_b)
    job_b_id = resp_b.json()["id"]
    
    # HR A lists jobs, should only see Job A
    resp = await async_client.get("/api/v1/jobs", headers=headers_hr_a)
    jobs_a = resp.json()
    assert len(jobs_a) == 1
    assert jobs_a[0]["id"] == job_a_id
    
    # HR A tries to get Job B by ID -> 404 Not Found
    resp = await async_client.get(f"/api/v1/jobs/{job_b_id}", headers=headers_hr_a)
    assert resp.status_code == 404
    
    # Recruiter A can read Job A
    resp = await async_client.get(f"/api/v1/jobs/{job_a_id}", headers=headers_rec_a)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_department_delete_detaches_jobs(async_client: AsyncClient, setup_users, db_session: AsyncSession):
    headers_hr_a = setup_users["hr_a"]["headers"]
    
    # Create dept
    resp = await async_client.post("/api/v1/departments", json={"name": "Sales"}, headers=headers_hr_a)
    dept_a_id = resp.json()["id"]
    
    # Create job in dept
    resp = await async_client.post("/api/v1/jobs", json={
        "title": "Sales Rep",
        "description": "Sell things",
        "department_id": dept_a_id
    }, headers=headers_hr_a)
    job_a_id = resp.json()["id"]
    
    # Delete Department A
    resp = await async_client.delete(f"/api/v1/departments/{dept_a_id}", headers=headers_hr_a)
    assert resp.status_code == 204
    
    # Check department is no longer listed (soft deleted from API view)
    resp = await async_client.get("/api/v1/departments", headers=headers_hr_a)
    assert len(resp.json()) == 0
    
    # Check job still exists but department_id is null
    resp = await async_client.get(f"/api/v1/jobs/{job_a_id}", headers=headers_hr_a)
    job_after_delete = resp.json()
    assert job_after_delete["department_id"] is None
    
    # Check database raw state for soft delete
    result = await db_session.execute(select(Department).where(Department.id == dept_a_id))
    db_dept = result.scalars().first()
    assert db_dept.deleted_at is not None


@pytest.mark.asyncio
async def test_pipeline_stage_reorder(async_client: AsyncClient, setup_users):
    headers_hr_a = setup_users["hr_a"]["headers"]
    
    # Create job
    resp = await async_client.post("/api/v1/jobs", json={
        "title": "Pipeline Test Job",
        "description": "Code things"
    }, headers=headers_hr_a)
    job_a_id = resp.json()["id"]
    
    # PUT new custom stages
    custom_stages = [
        {"name": "Screening", "order_index": 0},
        {"name": "Technical Assessment", "order_index": 1},
        {"name": "Final Interview", "order_index": 2},
        {"name": "Offer", "order_index": 3}
    ]
    resp = await async_client.put(f"/api/v1/jobs/{job_a_id}/stages", json=custom_stages, headers=headers_hr_a)
    assert resp.status_code == 200
    
    # GET job and assert new order is applied properly
    resp = await async_client.get(f"/api/v1/jobs/{job_a_id}", headers=headers_hr_a)
    job_data = resp.json()
    stages = job_data.get("pipeline_stages", [])
    assert len(stages) == 4
    
    # Sort them just in case API return order isn't guaranteed by the DB, 
    # though usually we want to assert the values match
    stages = sorted(stages, key=lambda s: s["order_index"])
    assert stages[0]["name"] == "Screening"
    assert stages[0]["order_index"] == 0
    assert stages[1]["name"] == "Technical Assessment"
    assert stages[1]["order_index"] == 1
    assert stages[2]["name"] == "Final Interview"
    assert stages[2]["order_index"] == 2
    assert stages[3]["name"] == "Offer"
    assert stages[3]["order_index"] == 3


@pytest.mark.asyncio
async def test_rbac_interviewer_blocked_from_jobs(async_client: AsyncClient, setup_users):
    headers_int_a = setup_users["int_a"]["headers"]
    
    # Interviewer tries to list jobs
    resp = await async_client.get("/api/v1/jobs", headers=headers_int_a)
    assert resp.status_code == 403
    
    # Interviewer tries to get departments
    resp = await async_client.get("/api/v1/departments", headers=headers_int_a)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_job_detailed_fields_crud(async_client: AsyncClient, setup_users):
    headers_hr_a = setup_users["hr_a"]["headers"]
    
    payload = {
        "title": "Lead Software Engineer",
        "description": "Lead engineering team",
        "location": "San Francisco, CA",
        "work_type": "HYBRID",
        "salary_range": "$160k - $190k / yr",
        "company_description": "A high-growth AI startup revolutionizing recruitment.",
        "key_responsibilities": [
            "Architect and build microservices",
            "Mentor junior engineers",
            "Lead sprint planning"
        ],
        "expectations": [
            "5+ years of Python/FastAPI",
            "Experience with distributed systems"
        ],
        "benefits": [
            "Comprehensive health/dental/vision",
            "Unlimited PTO",
            "401(k) matching"
        ]
    }
    
    resp = await async_client.post("/api/v1/jobs", json=payload, headers=headers_hr_a)
    assert resp.status_code == 201
    job_data = resp.json()
    assert job_data["salary_range"] == "$160k - $190k / yr"
    assert job_data["company_description"] == "A high-growth AI startup revolutionizing recruitment."
    assert job_data["key_responsibilities"] == payload["key_responsibilities"]
    assert job_data["expectations"] == payload["expectations"]
    assert job_data["benefits"] == payload["benefits"]
    
    job_id = job_data["id"]
    
    resp_get = await async_client.get(f"/api/v1/jobs/{job_id}", headers=headers_hr_a)
    assert resp_get.status_code == 200
    fetched = resp_get.json()
    assert fetched["salary_range"] == "$160k - $190k / yr"
    assert fetched["company_description"] == "A high-growth AI startup revolutionizing recruitment."
    assert fetched["key_responsibilities"] == payload["key_responsibilities"]
    assert fetched["expectations"] == payload["expectations"]
    assert fetched["benefits"] == payload["benefits"]
    
    update_payload = {
        "salary_range": "$170k - $200k / yr",
        "benefits": ["Remote work stipend", "Unlimited PTO"]
    }
    resp_patch = await async_client.patch(f"/api/v1/jobs/{job_id}", json=update_payload, headers=headers_hr_a)
    assert resp_patch.status_code == 200
    updated = resp_patch.json()
    assert updated["salary_range"] == "$170k - $200k / yr"
    assert updated["benefits"] == ["Remote work stipend", "Unlimited PTO"]
    assert updated["company_description"] == "A high-growth AI startup revolutionizing recruitment."

