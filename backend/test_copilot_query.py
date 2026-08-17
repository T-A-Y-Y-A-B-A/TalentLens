import asyncio
from app.core.database import AsyncSessionLocal
from app.services.copilot import query_copilot
from app.models.identity import User
from app.schemas.copilot import CopilotQueryRequest
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.org_id == 'd61b8890-897d-49ca-a0a3-e211481cc7a5', User.role == 'hr_manager').limit(1))).scalars().first()
        request = CopilotQueryRequest(query="bim")
        response = await query_copilot(session, request, user)
        for cand in response.results:
            if cand['name'] == 'sanat':
                print(f"Sanat's skills: {cand['skills']}")

if __name__ == "__main__":
    asyncio.run(main())
