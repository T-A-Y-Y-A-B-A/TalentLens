import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.recruitment import Department, Job, JobStatus, WorkType
from app.models.ai import JobMatch
from app.models.candidate import Candidate
from app.models.identity import Organization

@pytest.fixture
async def setup_candidates_and_jobs(async_client: AsyncClient, db_session: AsyncSession):
    # Register org
    resp = await async_client.post("/api/v1/auth/register", json={"email": "hr_board@example.com", "password": "Pass123!", "org_name": "Board Org"})
    org_id = resp.json()["org_id"]
    token_hr = (await async_client.post("/api/v1/auth/login", json={"email": "hr_board@example.com", "password": "Pass123!"})).json()["access_token"]
    headers_hr = {"Authorization": f"Bearer {token_hr}"}

    # Register candidate A
    email_cand_a = f"canda_{uuid.uuid4().hex[:8]}@example.com"
    await async_client.post("/api/v1/candidate-portal/register", json={"email": email_cand_a, "password": "Pass123!", "name": "Candidate A", "phone": "123"})
    token_cand_a = (await async_client.post("/api/v1/candidate-portal/login", json={"email": email_cand_a, "password": "Pass123!"})).json()["access_token"]
    
    # Register candidate B
    email_cand_b = f"candb_{uuid.uuid4().hex[:8]}@example.com"
    await async_client.post("/api/v1/candidate-portal/register", json={"email": email_cand_b, "password": "Pass123!", "name": "Candidate B", "phone": "123"})
    token_cand_b = (await async_client.post("/api/v1/candidate-portal/login", json={"email": email_cand_b, "password": "Pass123!"})).json()["access_token"]

    # Get candidates from db to get IDs
    result_a = await db_session.execute(select(Candidate).where(Candidate.email == email_cand_a))
    cand_a_id = result_a.scalars().first().id
    result_b = await db_session.execute(select(Candidate).where(Candidate.email == email_cand_b))
    cand_b_id = result_b.scalars().first().id

    # Create job
    resp = await async_client.post("/api/v1/jobs", json={
        "title": "Board Job",
        "description": "Desc",
        "work_type": "REMOTE",
        "salary_min": 100000,
        "salary_max": 150000,
    }, headers=headers_hr)
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Make job OPEN
    await async_client.patch(f"/api/v1/jobs/{job_id}", json={"status": "open"}, headers=headers_hr)

    # Create JobMatches directly in DB for testing
    match_a = JobMatch(job_id=job_id, candidate_id=cand_a_id, match_pct=85, matched_skills=["Python"], missing_skills=["Go"])
    match_b = JobMatch(job_id=job_id, candidate_id=cand_b_id, match_pct=95, matched_skills=["Python", "Go"], missing_skills=[])
    db_session.add_all([match_a, match_b])
    await db_session.commit()

    return {
        "headers_cand_a": {"Authorization": f"Bearer {token_cand_a}"},
        "headers_cand_b": {"Authorization": f"Bearer {token_cand_b}"},
        "job_id": job_id
    }

@pytest.mark.asyncio
async def test_job_board_isolation_candidate_a_b(async_client: AsyncClient, setup_candidates_and_jobs):
    """Ensure Candidate A does not see Candidate B's match score."""
    
    headers_cand_a = setup_candidates_and_jobs["headers_cand_a"]
    headers_cand_b = setup_candidates_and_jobs["headers_cand_b"]
    
    # Candidate A fetches board
    resp_a = await async_client.get("/api/v1/jobs/board", headers=headers_cand_a)
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert len(data_a["jobs"]) > 0
    job_a = data_a["jobs"][0]
    assert job_a["match_pct"] == 85

    # Candidate B fetches board
    resp_b = await async_client.get("/api/v1/jobs/board", headers=headers_cand_b)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert len(data_b["jobs"]) > 0
    job_b = data_b["jobs"][0]
    assert job_b["match_pct"] == 95

@pytest.mark.asyncio
async def test_job_board_unauthenticated(async_client: AsyncClient, setup_candidates_and_jobs):
    """Ensure unauthenticated users can fetch board but see null match scores."""
    resp = await async_client.get("/api/v1/jobs/board")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["jobs"]) > 0
    job = data["jobs"][0]
    assert job["match_pct"] is None

@pytest.mark.asyncio
async def test_job_creation_salary_validation(async_client: AsyncClient):
    """Ensure salary_max >= salary_min validation triggers on job creation."""
    # Register org for this test
    resp = await async_client.post("/api/v1/auth/register", json={"email": "hr_val@example.com", "password": "Pass123!", "org_name": "Val Org"})
    token_hr = (await async_client.post("/api/v1/auth/login", json={"email": "hr_val@example.com", "password": "Pass123!"})).json()["access_token"]
    headers_hr = {"Authorization": f"Bearer {token_hr}"}

    payload = {
        "title": "Board Job 2",
        "description": "Desc",
        "work_type": "REMOTE",
        "salary_min": 150000,
        "salary_max": 100000, # Invalid! min > max
    }
    
    resp = await async_client.post("/api/v1/jobs", json=payload, headers=headers_hr)
    assert resp.status_code == 422
    data = resp.json()
    assert "salary_max must be >= salary_min" in data["detail"][0]["msg"]
