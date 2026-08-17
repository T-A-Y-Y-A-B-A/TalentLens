import asyncio
from app.core.database import AsyncSessionLocal
from app.services.candidate_visibility import sync_candidate_qdrant_orgs
import uuid

async def main():
    async with AsyncSessionLocal() as db:
        candidate_id = uuid.UUID("002b4736-fec2-4ea8-8060-75f36077fe31")
        # abc-software.com org ID
        org_id = "898eb448-0a48-4d07-8a0f-e2bbb13072e5"
        await sync_candidate_qdrant_orgs(db, candidate_id, force_org_id=org_id)
        print(f"Force-synced {candidate_id} to org {org_id}")

if __name__ == "__main__":
    asyncio.run(main())
