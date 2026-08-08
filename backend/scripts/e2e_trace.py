import asyncio
import os
import sys
import uuid
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.identity import User
from app.models.recruitment import Job, PipelineStage
from app.models.candidate import Candidate, CandidateEmbedding, Resume, ResumeParsedData, ParseStatus
from app.models.application import Application
from app.services.application import create_application
from app.schemas.application import ApplicationCreate
from app.core.qdrant import qdrant_client
from app.services.copilot import query_copilot
from app.schemas.copilot import CopilotQueryRequest, CopilotFilter
from app.services.candidate_visibility import sync_candidate_qdrant_orgs

async def main():
    print("Starting E2E Trace...")
    async with AsyncSessionLocal() as db:
        # 1. Setup a test User, Org, Job, and Candidate
        org_id_1 = str(uuid.uuid4())
        user_id = uuid.uuid4()
        
        # We need a user to pass to create_application
        user = User(id=user_id, email="trace@test.com", hashed_password="pw", org_id=org_id_1)
        # Assuming role enum handles this, but let's mock the role check or just save the user.
        # It's easier to just use an existing user from the database or create one properly.
        result = await db.execute(select(User).limit(1))
        real_user = result.scalars().first()
        if not real_user:
            print("No real user found.")
            return
            
        print(f"Using user: {real_user.email} from org {real_user.org_id}")
        org_id = real_user.org_id
        
        # Find or create a job
        job_result = await db.execute(select(Job).where(Job.org_id == org_id).limit(1))
        job = job_result.scalars().first()
        if not job:
            job = Job(id=uuid.uuid4(), title="Python Engineer", description="backend", org_id=org_id)
            db.add(job)
            stage = PipelineStage(id=uuid.uuid4(), job_id=job.id, name="Applied", order_index=0)
            db.add(stage)
            await db.commit()
            await db.refresh(job)
            print(f"Created new job {job.id}")
        else:
            print(f"Using existing job {job.id}")
            
        # Create a candidate
        candidate = Candidate(id=uuid.uuid4(), email=f"candidate_{uuid.uuid4()}@test.com", name="Python Dev", phone="123")
        db.add(candidate)
        
        resume = Resume(id=uuid.uuid4(), candidate_id=candidate.id, file_url="dummy.pdf", parse_status=ParseStatus.DONE)
        db.add(resume)
        
        parsed_data = ResumeParsedData(
            resume_id=resume.id,
            skills=["Python", "AWS", "FastAPI"],
            experience=[], education=[], certifications=[], projects=[]
        )
        db.add(parsed_data)
        
        point_id = str(uuid.uuid4())
        emb = CandidateEmbedding(candidate_id=candidate.id, qdrant_point_id=point_id, model_version="test")
        db.add(emb)
        await db.commit()
        
        # Insert a dummy point in Qdrant so it can be searched
        from app.ai.embeddings import embed_text
        dense = embed_text("Skills: Python, AWS, FastAPI")
        from qdrant_client.models import PointStruct
        await qdrant_client.upsert(
            collection_name="candidates",
            points=[
                PointStruct(
                    id=point_id,
                    vector={"dense": dense, "sparse": {"indices": [], "values": []}},
                    payload={"candidate_id": str(candidate.id), "skills": ["Python", "AWS"]}
                )
            ]
        )
        print(f"Created candidate {candidate.id} and Qdrant point {point_id}")
        
        # 2. Candidate applies to a job -> triggers create_application
        print("\n--- Step 1: Candidate Applies to Job ---")
        app_in = ApplicationCreate(candidate_id=candidate.id, job_id=job.id)
        # Mock role enforcement just for this script, or use a user with permissions.
        # We will manually do what create_application does to avoid strict permission checks failing if user is not hr_manager.
        # Actually create_application requires "applications" "manage". Let's bypass it by calling sync directly, 
        # or just trying it. We'll try create_application first.
        try:
            application = await create_application(db, app_in, real_user)
            print(f"Application created: {application.id}")
        except Exception as e:
            print(f"create_application failed (maybe permissions): {e}")
            print("Manually inserting application and calling sync...")
            application = Application(candidate_id=candidate.id, job_id=job.id, org_id=org_id, applied_at="2026-08-07T00:00:00Z")
            db.add(application)
            await db.commit()
            await db.refresh(application)
            await sync_candidate_qdrant_orgs(db, candidate.id)
            
        # 3. Confirm Qdrant payload updated
        print("\n--- Step 2: Confirm Qdrant payload updated ---")
        points = await qdrant_client.retrieve(collection_name="candidates", ids=[point_id])
        print("Payload from Qdrant:")
        print(json.dumps(points[0].payload, indent=2))
        if str(org_id) in points[0].payload.get("org_ids", []):
            print("SUCCESS: org_id was synced to Qdrant payload.")
        else:
            print("ERROR: org_id missing from Qdrant payload.")
            
        # 4. Copilot query against that org returning the candidate
        print("\n--- Step 3: Copilot query ---")
        req = CopilotQueryRequest(query="Find me Python and AWS developers")
        
        # Mock LLM for the trace
        import app.services.copilot
        original_call_llm = app.services.copilot.call_llm
        async def mock_call_llm(*args, **kwargs):
            return CopilotFilter(skills=["Python", "AWS"], keywords=[], certifications=[])
        app.services.copilot.call_llm = mock_call_llm
        
        try:
            response = await query_copilot(db, req, real_user)
        finally:
            app.services.copilot.call_llm = original_call_llm
            
        print(f"Query: {req.query}")
        print("Interpreted as:", response.interpreted_as.model_dump())
        
        found = False
        for res in response.results:
            if res["candidate_id"] == str(candidate.id):
                found = True
                print(f"SUCCESS: Found candidate {candidate.name} in results.")
                break
        if not found:
            print("ERROR: Did not find candidate in results. Results returned:", len(response.results))
            
if __name__ == "__main__":
    asyncio.run(main())
