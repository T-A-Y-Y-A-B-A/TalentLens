import asyncio
from app.core.database import AsyncSessionLocal
from app.services.candidate import get_candidate
from app.models.identity import User
from sqlalchemy import select
import uuid

async def main():
    async with AsyncSessionLocal() as session:
        # Get the user that ran Copilot (org d61b8890-897d-49ca-a0a3-e211481cc7a5)
        user = (await session.execute(select(User).where(User.org_id == 'd61b8890-897d-49ca-a0a3-e211481cc7a5', User.role == 'hr_manager').limit(1))).scalars().first()
        print(f"Current User Role: {user.role.value}, Org: {user.org_id}")
        
        cand_id = uuid.UUID('7bdfe08b-55e1-4caf-8bee-c7d9757c4bf4')
        try:
            cand = await get_candidate(session, cand_id, user)
            print(f"Success! Candidate Name: {cand.name}")
        except Exception as e:
            print(f"Failed get_candidate: {e}")

if __name__ == "__main__":
    asyncio.run(main())
