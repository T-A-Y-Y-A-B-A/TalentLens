import asyncio
import uuid
from httpx import AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.identity import Organization, User
from app.models.recruitment import Job, JobStatus, PipelineStage
from app.models.candidate import Candidate
from app.models.application import Application
from app.core.security import get_password_hash, create_access_token
import os

os.environ["TESTING"] = "1"

async def setup_test_data():
    async with AsyncSessionLocal() as db:
        # Create Org A
        org_a = Organization(name=f"Org A {uuid.uuid4()}", slug=f"org-a-{uuid.uuid4()}")
        db.add(org_a)
        
        # Create Org B
        org_b = Organization(name=f"Org B {uuid.uuid4()}", slug=f"org-b-{uuid.uuid4()}")
        db.add(org_b)
        await db.commit()
        await db.refresh(org_a)
        await db.refresh(org_b)
        
        # Create Job A in Org A
        job_a = Job(
            title="Software Engineer A",
            description="A job",
            requirements="Python",
            status=JobStatus.OPEN,
            org_id=org_a.id,
            created_by=None
        )
        db.add(job_a)
        
        # Create Job B in Org B
        job_b = Job(
            title="Software Engineer B",
            description="B job",
            requirements="Java",
            status=JobStatus.OPEN,
            org_id=org_b.id,
            created_by=None
        )
        db.add(job_b)
        
        # Create Candidate
        candidate = Candidate(
            name="Test Candidate",
            email=f"test{uuid.uuid4()}@example.com",
            hashed_password=get_password_hash("password")
        )
        db.add(candidate)
        await db.commit()
        await db.refresh(candidate)
        await db.refresh(job_a)
        await db.refresh(job_b)
        
        # Link Candidate to Org A via Application
        app_a = Application(
            candidate_id=candidate.id,
            job_id=job_a.id,
            org_id=org_a.id,
            status="active"
        )
        db.add(app_a)
        await db.commit()
        
        return org_a, org_b, candidate

async def run_test():
    org_a, org_b, candidate = await setup_test_data()
    
    # Generate token for candidate
    token = create_access_token(subject=candidate.id, additional_claims={"role": "candidate"})
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test 1: Accessing Org B's jobs should be 403
        print(f"Testing GET /jobs for Org B ({org_b.id})...")
        res = await client.get(f"/api/v1/candidate-portal/jobs?org_id={org_b.id}", headers=headers)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 403:
            print("SUCCESS: 403 Forbidden correctly returned for unauthorized org.")
        else:
            print(f"FAIL: Expected 403, got {res.status_code}. Response: {res.text}")
            
        # Test 2: Accessing Org A's jobs should be 200
        print(f"Testing GET /jobs for Org A ({org_a.id})...")
        res = await client.get(f"/api/v1/candidate-portal/jobs?org_id={org_a.id}", headers=headers)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            print("SUCCESS: 200 OK returned for authorized org.")
        else:
            print(f"FAIL: Expected 200, got {res.status_code}. Response: {res.text}")
            
        # Test 3: Analyzing against Org B should be 403
        print(f"Testing POST /me/analyze for Org B...")
        res = await client.post("/api/v1/candidate-portal/me/analyze", json={"org_id": str(org_b.id)}, headers=headers)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 403:
            print("SUCCESS: 403 Forbidden correctly returned for unauthorized org analyze.")
        else:
            print(f"FAIL: Expected 403, got {res.status_code}. Response: {res.text}")

if __name__ == "__main__":
    asyncio.run(run_test())
