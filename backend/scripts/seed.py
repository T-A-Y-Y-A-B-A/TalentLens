import asyncio
import sys
import os

# Ensure the app context is available
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.services.auth import register_user
from app.models.identity import UserRole
from app.core.security import get_password_hash

async def seed_data():
    print("Running seed script...")
    
    # 1. Truncate tables (using raw SQL)
    async with engine.begin() as conn:
        print("Truncating existing tenant data...")
        await conn.execute(text("""
            TRUNCATE TABLE 
            audit_logs, notifications, interview_feedback, interviews, ai_usage_logs, ai_match_results, 
            application_stage_history, applications, candidate_embeddings, resume_parsed_data, resumes, 
            candidates, job_embeddings, pipeline_stages, jobs, departments, 
            email_verifications, password_resets, refresh_tokens, users, organizations 
            RESTART IDENTITY CASCADE;
        """))
        
    async with AsyncSessionLocal() as db:
        # We need to manually create users directly or use auth service.
        # It's cleaner to create them directly here to inject specific roles.
        from app.models.identity import Organization, User
        from app.models.recruitment import Job, Department, JobStatus
        from app.models.candidate import Candidate, Resume, ParseStatus
        import uuid
        
        orgs_data = [
            {"name": "DigitalSofts", "slug": "digitalsofts"},
            {"name": "ABC Software", "slug": "abc-software"},
            {"name": "XYZ Bank", "slug": "xyz-bank"}
        ]
        
        credentials = []
        dev_password = "DevPass123!"
        hashed_pw = get_password_hash(dev_password)
        
        for idx, org_dict in enumerate(orgs_data):
            org = Organization(name=org_dict["name"], slug=org_dict["slug"])
            db.add(org)
            await db.flush()
            
            # Create HR Manager
            hr_user = User(
                email=f"hr@{org_dict['slug']}.com",
                hashed_password=hashed_pw,
                organization=org,
                role=UserRole.HR_MANAGER,
                is_verified=True
            )
            
            # Create Recruiter
            rec_user = User(
                email=f"recruiter@{org_dict['slug']}.com",
                hashed_password=hashed_pw,
                organization=org,
                role=UserRole.RECRUITER,
                is_verified=True
            )
            
            db.add(hr_user)
            db.add(rec_user)
            await db.flush()
            
            # Create a Department
            dept = Department(name="Engineering", org_id=org.id)
            db.add(dept)
            await db.flush()
            
            # Create a Job
            job = Job(
                department_id=dept.id,
                title=f"Software Engineer - {org.name}",
                description="We are looking for a great software engineer.",
                status=JobStatus.OPEN,
                created_by=hr_user.id,
                org_id=org.id
            )
            db.add(job)
            await db.flush()

            # Create pipeline stages for the job
            from app.models.recruitment import PipelineStage
            stages = ["Sourced", "Applied", "Interviewing", "Offered", "Hired"]
            first_stage = None
            for idx, stage_name in enumerate(stages):
                stage = PipelineStage(
                    job_id=job.id,
                    name=stage_name,
                    order_index=idx
                )
                db.add(stage)
                if idx == 0:
                    first_stage = stage
            
            await db.flush()
            
            # Create a Candidate
            candidate = Candidate(
                email=f"candidate_{idx}@example.com",
                name=f"Demo Candidate {idx}",
                source="portal"
            )
            db.add(candidate)
            await db.flush()
            
            # Create an Application to link Candidate to Job/Org
            from app.models.application import Application
            from datetime import datetime, timezone
            application = Application(
                org_id=org.id,
                candidate_id=candidate.id,
                job_id=job.id,
                current_stage_id=first_stage.id if first_stage else None,
                status="active",
                applied_at=datetime.now(timezone.utc).isoformat()
            )
            db.add(application)
            await db.flush()
            
            # Create a Resume
            resume = Resume(
                candidate_id=candidate.id,
                file_url=f"s3://fake-bucket/resume_{idx}.pdf",
                parse_status=ParseStatus.PENDING
            )
            db.add(resume)
            
            credentials.append(f"Org: {org.name} | HR: {hr_user.email} / {dev_password}")
            credentials.append(f"Org: {org.name} | Recruiter: {rec_user.email} / {dev_password}")
            
        await db.commit()

        
        print("\n=== Seed Data Created Successfully ===")
        print("You can log in with the following credentials:")
        for cred in credentials:
            print(cred)
        print("======================================\n")

if __name__ == "__main__":
    asyncio.run(seed_data())
