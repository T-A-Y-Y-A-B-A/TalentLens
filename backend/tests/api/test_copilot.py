import pytest
from httpx import AsyncClient
import uuid
from app.main import app
from app.core.security import create_access_token
from app.models.identity import User
from app.models.recruitment import Job
from app.models.candidate import Candidate, Resume, ResumeParsedData, CandidateEmbedding, ParseStatus
from app.models.application import Application
from app.services.candidate_visibility import sync_candidate_qdrant_orgs
from app.core.qdrant import qdrant_client
from qdrant_client.models import PointStruct

@pytest.fixture
async def seeded_data(db_session):
    from app.models.identity import Organization
    
    # Org A and Org B
    org_a_id = uuid.uuid4()
    org_b_id = uuid.uuid4()
    
    org_a = Organization(id=org_a_id, name="Org A", slug=f"org-a-{uuid.uuid4()}")
    org_b = Organization(id=org_b_id, name="Org B", slug=f"org-b-{uuid.uuid4()}")
    db_session.add(org_a)
    db_session.add(org_b)
    await db_session.flush()
    
    # Users
    user_a = User(id=uuid.uuid4(), email="hr_a@test.com", hashed_password="pw", role="hr_manager", org_id=org_a_id)
    user_b = User(id=uuid.uuid4(), email="hr_b@test.com", hashed_password="pw", role="hr_manager", org_id=org_b_id)
    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.flush()
    
    # Jobs
    job_a = Job(id=uuid.uuid4(), title="Python Engineer", description="desc", org_id=org_a_id)
    job_b = Job(id=uuid.uuid4(), title="Python Engineer", description="desc", org_id=org_b_id)
    db_session.add(job_a)
    db_session.add(job_b)
    await db_session.flush()
    
    # Candidate A (applied to Org A)
    cand_a = Candidate(id=uuid.uuid4(), email="a@test.com", name="Candidate A")
    db_session.add(cand_a)
    app_a = Application(id=uuid.uuid4(), candidate_id=cand_a.id, job_id=job_a.id, org_id=org_a_id, applied_at="2026-08-07T00:00:00Z")
    db_session.add(app_a)
    resume_a = Resume(id=uuid.uuid4(), candidate_id=cand_a.id, file_url="url", parse_status=ParseStatus.DONE)
    db_session.add(resume_a)
    parsed_a = ResumeParsedData(id=uuid.uuid4(), resume_id=resume_a.id, skills=["Python", "AWS"])
    db_session.add(parsed_a)
    emb_a = CandidateEmbedding(candidate_id=cand_a.id, qdrant_point_id=str(uuid.uuid4()), model_version="1")
    db_session.add(emb_a)
    
    # Candidate B (applied to Org B)
    cand_b = Candidate(id=uuid.uuid4(), email="b@test.com", name="Candidate B")
    db_session.add(cand_b)
    app_b = Application(id=uuid.uuid4(), candidate_id=cand_b.id, job_id=job_b.id, org_id=org_b_id, applied_at="2026-08-07T00:00:00Z")
    db_session.add(app_b)
    resume_b = Resume(id=uuid.uuid4(), candidate_id=cand_b.id, file_url="url", parse_status=ParseStatus.DONE)
    db_session.add(resume_b)
    parsed_b = ResumeParsedData(id=uuid.uuid4(), resume_id=resume_b.id, skills=["Python", "AWS"])
    db_session.add(parsed_b)
    emb_b = CandidateEmbedding(candidate_id=cand_b.id, qdrant_point_id=str(uuid.uuid4()), model_version="1")
    db_session.add(emb_b)
    
    await db_session.commit()
    
    # Sync Qdrant (which will look at db and sync)
    # We must insert dummy points first so it can update the payload
    # In real app, resume parsing inserts the point first, then sync_candidate_qdrant_orgs updates the payload.
    from app.ai.embeddings import embed_text
    dense = embed_text("Skills: Python, AWS")
    
    await qdrant_client.upsert(
        collection_name="candidates",
        points=[
            PointStruct(
                id=emb_a.qdrant_point_id,
                vector={"dense": dense, "sparse": {"indices": [], "values": []}},
                payload={"candidate_id": str(cand_a.id), "skills": ["Python", "AWS"]}
            ),
            PointStruct(
                id=emb_b.qdrant_point_id,
                vector={"dense": dense, "sparse": {"indices": [], "values": []}},
                payload={"candidate_id": str(cand_b.id), "skills": ["Python", "AWS"]}
            )
        ]
    )
    
    await sync_candidate_qdrant_orgs(db_session, cand_a.id)
    await sync_candidate_qdrant_orgs(db_session, cand_b.id)
    
    return {
        "user_a": user_a,
        "user_b": user_b,
        "job_a": job_a,
        "cand_a": cand_a,
        "cand_b": cand_b
    }

@pytest.fixture
def mock_llm(monkeypatch):
    from app.schemas.copilot import CopilotFilter
    async def mock_call_llm(*args, **kwargs):
        # Check if job_id is in query string to mimic parsing
        job_id = None
        if "job_id=" in kwargs.get("prompt", ""):
            job_id_str = kwargs["prompt"].split("job_id=")[1]
            job_id = uuid.UUID(job_id_str)
        return CopilotFilter(
            skills=["Python", "AWS"],
            keywords=[],
            certifications=[],
            location="New York",
            job_id=job_id
        )
    monkeypatch.setattr("app.services.copilot.call_llm", mock_call_llm)

@pytest.mark.asyncio
async def test_copilot_isolation(async_client: AsyncClient, db_session, seeded_data, mock_llm):
    user_a = seeded_data["user_a"]
    cand_a = seeded_data["cand_a"]
    cand_b = seeded_data["cand_b"]
    
    token = create_access_token(subject=str(user_a.id), additional_claims={"role": "hr_manager", "org_id": str(user_a.org_id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Query for Python engineers (should only return from org A, even if org B has them)
    response = await async_client.post(
        "/api/v1/copilot/query",
        json={"query": "Find me backend engineers with Python and AWS experience."},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "interpreted_as" in data
    assert "results" in data
    
    results = data["results"]
    assert len(results) == 1
    assert results[0]["candidate_id"] == str(cand_a.id)
    # Ensure Candidate B is completely isolated
    assert not any(r["candidate_id"] == str(cand_b.id) for r in results)

@pytest.mark.asyncio
async def test_copilot_job_scoping(async_client: AsyncClient, db_session, seeded_data, mock_llm):
    user_a = seeded_data["user_a"]
    job_a = seeded_data["job_a"]
    cand_a = seeded_data["cand_a"]
    
    token = create_access_token(subject=str(user_a.id), additional_claims={"role": "hr_manager", "org_id": str(user_a.org_id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.post(
        "/api/v1/copilot/query",
        json={"query": f"Find candidates job_id={str(job_a.id)}", "job_id": str(job_a.id)},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["interpreted_as"]["job_id"] == str(job_a.id)
    assert len(data["results"]) == 1
    assert data["results"][0]["candidate_id"] == str(cand_a.id)
