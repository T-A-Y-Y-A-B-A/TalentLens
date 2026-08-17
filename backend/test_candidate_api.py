import asyncio
from app.core.database import AsyncSessionLocal
from app.services.candidate import get_candidate
from app.models.identity import User
from sqlalchemy import select
import uuid

async def main():
    async with AsyncSessionLocal() as session:
        # Get the first user (assume it's the one we're logged in as)
        user = (await session.execute(select(User).limit(1))).scalars().first()
        print(f"Current User Role: {user.role.value}, Org: {user.org_id}")
        
        cand_id = uuid.UUID('7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4')
        try:
            cand = await get_candidate(session, cand_id, user)
            print(f"Success! Candidate Name: {cand.name}")
        except Exception as e:
            print(f"Failed get_candidate: {e}")
            
        from app.services.candidate import get_resume_by_id
        # Let's see if the candidate has a resume
        cand_db = (await session.execute(select(Candidate).where(Candidate.id == cand_id))).scalars().first()
        from app.models.candidate import Candidate, Resume
        resumes = (await session.execute(select(Resume).where(Resume.candidate_id == cand_id))).scalars().all()
        for r in resumes:
            try:
                res = await get_resume_by_id(session, cand_id, r.id, user)
                print(f"Success! Resume ID: {res.id}")
            except Exception as e:
                print(f"Failed get_resume_by_id: {e}")

if __name__ == "__main__":
    asyncio.run(main())
