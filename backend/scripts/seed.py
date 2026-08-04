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
    if settings.ENVIRONMENT == "production":
        print("Refusing to run seed script against production.")
        sys.exit(1)
        
    print(f"Running seed script in {settings.ENVIRONMENT} environment...")
    
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
