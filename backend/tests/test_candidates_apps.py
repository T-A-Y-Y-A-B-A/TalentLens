import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity import User, UserRole
from app.models.recruitment import Department, Job, PipelineStage
from app.models.candidate import Candidate
from app.models.application import Application, ApplicationStageHistory

@pytest.fixture
async def setup_users(async_client: AsyncClient, db_session: AsyncSession):
    # Org A: HR Manager
    email_hr_a = f"hra_{uuid.uuid4().hex[:8]}@a.com"
    org_a = f"Org A {uuid.uuid4().hex[:6]}"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_hr_a, "password": "Pass123!", "org_name": org_a})
    
    # Org A: Recruiter
    email_rec_a = f"reca_{uuid.uuid4().hex[:8]}@a.com"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_rec_a, "password": "Pass123!", "org_name": f"Dummy Org {uuid.uuid4().hex[:6]}"})
    
    # Org A: Interviewer
    email_int_a = f"inta_{uuid.uuid4().hex[:8]}@a.com"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_int_a, "password": "Pass123!", "org_name": f"Dummy Org 2 {uuid.uuid4().hex[:6]}"})
    
    # Org B: HR Manager
    email_hr_b = f"hrb_{uuid.uuid4().hex[:8]}@b.com"
    org_b = f"Org B {uuid.uuid4().hex[:6]}"
    resp = await async_client.post("/api/v1/auth/register", json={"email": email_hr_b, "password": "Pass123!", "org_name": org_b})
    
    # Verify and set roles
    users = []
    for email, role in [(email_hr_a, UserRole.HR_MANAGER), (email_rec_a, UserRole.RECRUITER), (email_int_a, UserRole.INTERVIEWER), (email_hr_b, UserRole.HR_MANAGER)]:
        result = await db_session.execute(select(User).where(User.email == email))
        db_user = result.scalars().first()
        db_user.is_verified = True
        db_user.role = role
        users.append(db_user)
        
    # Put Recruiter A and Interviewer A in Org A
    users[1].org_id = users[0].org_id
    users[2].org_id = users[0].org_id
    
    await db_session.commit()
    
    async def login(email, pwd):
        resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        return resp.json()["access_token"]
        
    token_hr_a = await login(email_hr_a, "Pass123!")
    token_rec_a = await login(email_rec_a, "Pass123!")
    token_int_a = await login(email_int_a, "Pass123!")
    token_hr_b = await login(email_hr_b, "Pass123!")

    return {
        "hr_a": {"email": email_hr_a, "token": token_hr_a, "headers": {"Authorization": f"Bearer {token_hr_a}"}, "org_id": users[0].org_id, "id": users[0].id},
        "rec_a": {"email": email_rec_a, "token": token_rec_a, "headers": {"Authorization": f"Bearer {token_rec_a}"}, "org_id": users[1].org_id, "id": users[1].id},
        "int_a": {"email": email_int_a, "token": token_int_a, "headers": {"Authorization": f"Bearer {token_int_a}"}, "org_id": users[2].org_id, "id": users[2].id},
        "hr_b": {"email": email_hr_b, "token": token_hr_b, "headers": {"Authorization": f"Bearer {token_hr_b}"}, "org_id": users[3].org_id, "id": users[3].id}
    }


@pytest.fixture
async def setup_data(async_client: AsyncClient, setup_users):
    headers_hr_a = setup_users["hr_a"]["headers"]
    headers_hr_b = setup_users["hr_b"]["headers"]
    
    # Org A Job
    resp = await async_client.post("/api/v1/jobs", json={
        "title": "Software Engineer",
        "description": "Code things"
    }, headers=headers_hr_a)
    job_a_id = resp.json()["id"]
    stages_a = resp.json()["pipeline_stages"]
    
    # Org B Job
    resp = await async_client.post("/api/v1/jobs", json={
        "title": "Product Manager",
        "description": "Manage things"
    }, headers=headers_hr_b)
    job_b_id = resp.json()["id"]
    stages_b = resp.json()["pipeline_stages"]
    
    return {
        "job_a_id": job_a_id,
        "stages_a": sorted(stages_a, key=lambda s: s["order_index"]),
        "job_b_id": job_b_id,
        "stages_b": sorted(stages_b, key=lambda s: s["order_index"]),
    }

@pytest.mark.asyncio
async def test_candidate_app_rbac(async_client: AsyncClient, setup_users, setup_data):
    headers_rec_a = setup_users["rec_a"]["headers"]
    headers_int_a = setup_users["int_a"]["headers"]
    
    # Interviewer cannot create candidate
    resp = await async_client.post("/api/v1/candidates", json={
        "email": "test@example.com",
        "name": "Test Candidate"
    }, headers=headers_int_a)
    assert resp.status_code == 403
    
    # Recruiter CAN create candidate
    resp = await async_client.post("/api/v1/candidates", json={
        "email": "recruiter_add@example.com",
        "name": "Recruiter Add"
    }, headers=headers_rec_a)
    assert resp.status_code == 201
    cand_id = resp.json()["id"]
    
    # Recruiter CAN create application
    resp = await async_client.post("/api/v1/applications", json={
        "candidate_id": cand_id,
        "job_id": setup_data["job_a_id"]
    }, headers=headers_rec_a)
    assert resp.status_code == 201
    
    # Interviewer CANNOT view applications
    resp = await async_client.get("/api/v1/applications", headers=headers_int_a)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_application_creation_and_move(async_client: AsyncClient, setup_users, setup_data, db_session: AsyncSession):
    headers_hr_a = setup_users["hr_a"]["headers"]
    
    # Create Candidate
    resp = await async_client.post("/api/v1/candidates", json={
        "email": "jane@example.com",
        "name": "Jane Doe"
    }, headers=headers_hr_a)
    cand_id = resp.json()["id"]
    
    # Create Application
    resp = await async_client.post("/api/v1/applications", json={
        "candidate_id": cand_id,
        "job_id": setup_data["job_a_id"]
    }, headers=headers_hr_a)
    assert resp.status_code == 201
    app_data = resp.json()
    app_id = app_data["id"]
    
    # Assert initial stage is the first stage (order_index == 0)
    first_stage = setup_data["stages_a"][0]
    assert app_data["current_stage_id"] == first_stage["id"]
    
    # Move Application Stage
    second_stage = setup_data["stages_a"][1]
    resp = await async_client.put(f"/api/v1/applications/{app_id}/stage", json={
        "to_stage_id": second_stage["id"],
        "notes": "Passed initial screening"
    }, headers=headers_hr_a)
    assert resp.status_code == 200
    assert resp.json()["current_stage_id"] == second_stage["id"]
    
    # Verify ApplicationStageHistory logs
    result = await db_session.execute(
        select(ApplicationStageHistory).where(ApplicationStageHistory.application_id == app_id).order_by(ApplicationStageHistory.moved_at)
    )
    history = result.scalars().all()
    
    assert len(history) == 2
    # First history entry from creation
    assert history[0].from_stage_id is None
    assert str(history[0].to_stage_id) == first_stage["id"]
    
    # Second history entry from move
    assert str(history[1].from_stage_id) == first_stage["id"]
    assert str(history[1].to_stage_id) == second_stage["id"]
    assert history[1].notes == "Passed initial screening"
    assert str(history[1].moved_by) == str(setup_users["hr_a"]["id"])


@pytest.mark.asyncio
async def test_cross_org_application_rejected(async_client: AsyncClient, setup_users, setup_data):
    headers_hr_a = setup_users["hr_a"]["headers"]
    headers_hr_b = setup_users["hr_b"]["headers"]
    
    # HR A creates a candidate
    resp = await async_client.post("/api/v1/candidates", json={
        "email": "bob@example.com",
        "name": "Bob Org A"
    }, headers=headers_hr_a)
    cand_id_a = resp.json()["id"]
    
    # HR B creates a candidate
    resp = await async_client.post("/api/v1/candidates", json={
        "email": "alice@example.com",
        "name": "Alice Org B"
    }, headers=headers_hr_b)
    cand_id_b = resp.json()["id"]
    
    # HR A tries to apply their candidate to HR B's job
    resp = await async_client.post("/api/v1/applications", json={
        "candidate_id": cand_id_a,
        "job_id": setup_data["job_b_id"]
    }, headers=headers_hr_a)
    assert resp.status_code == 404 # Job not found (due to org filter)
    
    # HR A tries to apply HR B's candidate to HR A's job
    resp = await async_client.post("/api/v1/applications", json={
        "candidate_id": cand_id_b,
        "job_id": setup_data["job_a_id"]
    }, headers=headers_hr_a)
    assert resp.status_code == 404 # Candidate not found (due to org filter)
    
    # HR A creates valid application
    resp = await async_client.post("/api/v1/applications", json={
        "candidate_id": cand_id_a,
        "job_id": setup_data["job_a_id"]
    }, headers=headers_hr_a)
    assert resp.status_code == 201
    app_id = resp.json()["id"]
    
    # HR A tries to move application to a stage belonging to Job B
    stage_b = setup_data["stages_b"][1]
    resp = await async_client.put(f"/api/v1/applications/{app_id}/stage", json={
        "to_stage_id": stage_b["id"],
        "notes": "Move to other org stage"
    }, headers=headers_hr_a)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_stage"
