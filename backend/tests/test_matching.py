import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import asyncio

from app.models.ai import AIMatchResult, AIUsageLog
from app.models.recruitment import Job
from app.models.identity import User
from app.services.matching import _compute_cache_key, run_job_matching_pipeline
from app.models.candidate import Candidate, ResumeParsedData
from datetime import datetime, timedelta

from sentence_transformers import CrossEncoder

@pytest.fixture
async def setup_users(async_client: AsyncClient, db_session: AsyncSession):
    # Org A: HR Manager
    email_hr_a = f"hra_{uuid.uuid4().hex[:8]}@a.com"
    org_a = f"Org A {uuid.uuid4().hex[:6]}"
    await async_client.post("/api/v1/auth/register", json={"email": email_hr_a, "password": "Pass123!", "org_name": org_a})
    
    # Org B: HR Manager
    email_hr_b = f"hrb_{uuid.uuid4().hex[:8]}@b.com"
    org_b = f"Org B {uuid.uuid4().hex[:6]}"
    await async_client.post("/api/v1/auth/register", json={"email": email_hr_b, "password": "Pass123!", "org_name": org_b})
    
    users = []
    for email in [email_hr_a, email_hr_b]:
        result = await db_session.execute(select(User).where(User.email == email))
        db_user = result.scalars().first()
        db_user.is_verified = True
        users.append(db_user)
        
    await db_session.commit()
    
    # Create Departments
    from app.models.recruitment import Department
    dept_a = Department(id=uuid.uuid4(), org_id=users[0].org_id, name="Eng A")
    dept_b = Department(id=uuid.uuid4(), org_id=users[1].org_id, name="Eng B")
    db_session.add(dept_a)
    db_session.add(dept_b)
    await db_session.commit()

    # Org A Job
    job_a = Job(id=uuid.uuid4(), org_id=users[0].org_id, title="Job A", description="Desc", requirements="Reqs", department_id=dept_a.id)
    db_session.add(job_a)
    
    # Org B Job
    job_b = Job(id=uuid.uuid4(), org_id=users[1].org_id, title="Job B", description="Desc", requirements="Reqs", department_id=dept_b.id)
    db_session.add(job_b)
    
    await db_session.commit()

    return {
        "org_a_hr": users[0],
        "org_b_hr": users[1]
    }

@pytest.fixture
async def setup_candidate_data():
    return None

@pytest.mark.asyncio
async def test_matching_tenant_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    setup_users,
    setup_candidate_data
):
    """
    Test that an HR Manager in Org A cannot trigger or view match results for Org B's job.
    """
    org_a_hr = setup_users["org_a_hr"]
    org_b_hr = setup_users["org_b_hr"]
    
    # Get a job in Org B
    result = await db_session.execute(select(Job).where(Job.org_id == org_b_hr.org_id))
    org_b_job = result.scalars().first()
    assert org_b_job is not None
    
    # Login as Org A HR
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": org_a_hr.email, "password": "Pass123!"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Attempt to trigger match on Org B's job
    resp = await async_client.post(f"/api/v1/jobs/{org_b_job.id}/match", headers=headers)
    assert resp.status_code == 404 # Isolated via DB query
    
    # Attempt to view match results on Org B's job
    resp = await async_client.get(f"/api/v1/jobs/{org_b_job.id}/matches", headers=headers)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_matching_rate_limit(
    async_client: AsyncClient,
    db_session: AsyncSession,
    setup_users
):
    """
    Hit the POST /match API >5 times in a minute and assert a 429 Too Many Requests response.
    """
    # Get a job in Org A
    org_a_hr = setup_users["org_a_hr"]
    result = await db_session.execute(select(Job).where(Job.org_id == org_a_hr.org_id))
    job = result.scalars().first()
    
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": org_a_hr.email, "password": "Pass123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    # Re-enable rate limiting just for this test
    from app.main import app
    app.state.limiter.enabled = True
    
    # Make 5 requests (should succeed/202)
    for _ in range(5):
        resp = await async_client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
        assert resp.status_code == 202
        await asyncio.sleep(0.1)
        
    # The 6th request should be rate limited (429)
    resp = await async_client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert resp.status_code == 429
    assert "Rate limit exceeded" in str(resp.json()) or "RateLimit" in str(resp.json())

def test_cache_invalidation():
    """
    Assert that altering job.updated_at generates a new cache key.
    """
    job = Job(id=uuid.uuid4(), updated_at=datetime.utcnow())
    candidate = Candidate(id=uuid.uuid4())
    resume = ResumeParsedData(updated_at=datetime.utcnow())
    
    key1 = _compute_cache_key("v1", job, candidate, resume)
    
    # Alter job updated_at
    job.updated_at = job.updated_at + timedelta(minutes=5)
    key2 = _compute_cache_key("v1", job, candidate, resume)
    
    assert key1 != key2

@pytest.mark.asyncio
async def test_zero_matches_fallback(
    async_client: AsyncClient,
    db_session: AsyncSession,
    setup_users
):
    """
    Force a zero-result search by setting redis pipeline_status="done" but having no AIMatchResults.
    """
    org_a_hr = setup_users["org_a_hr"]
    result = await db_session.execute(select(Job).where(Job.org_id == org_a_hr.org_id))
    job = result.scalars().first()
    
    # Manually set redis to "done"
    import redis
    from app.core.config import settings
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.setex(f"job_match_status:{job.id}", 60, "done")
    
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": org_a_hr.email, "password": "Pass123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    resp = await async_client.get(f"/api/v1/jobs/{job.id}/matches", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert len(data["results"]) == 0
    assert "No candidates found" in data["message"]

def test_cross_encoder_reranking():
    """
    Feed candidates where the naive vector similarity is inverted compared to context relevance,
    and assert that cross-encoder successfully reorders them.
    """
    encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    job_context = "Senior Python Developer with strong backend experience, focusing on FastAPI, Postgres, and vector databases."
    
    # Bad naive match (lots of overlapping words but entirely wrong context)
    bad_context = "Backend developer working with Node.js and MongoDB. Has developed python scripts to scrape postgres databases occasionally."
    
    # Good naive match (actually has the specific skills in the right context)
    good_context = "Senior Backend Engineer. Expert in Python, FastAPI, and Postgres. Experienced in building scalable systems and integrating vector databases like Qdrant."
    
    scores = encoder.predict([
        (job_context, bad_context),
        (job_context, good_context)
    ])
    
    # The good context should score higher
    assert scores[1] > scores[0]
