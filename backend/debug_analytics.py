import asyncio
from app.core.database import AsyncSessionLocal
from app.services.analytics import get_dashboard_analytics
from app.models.identity import Organization
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        org = (await session.execute(select(Organization).limit(1))).scalars().first()
        if not org:
            print("No org")
            return
            
        print(f"Org ID: {org.id}")
        data = await get_dashboard_analytics(session, org.id)
        
        # Also let's print the intermediate lists manually
        from app.models.ai import JobMatch
        from app.models.recruitment import Job
        job_match_res = await session.execute(
            select(JobMatch).join(Job, JobMatch.job_id == Job.id).where(Job.org_id == org.id)
        )
        job_matches = job_match_res.scalars().all()
        high = [m for m in job_matches if m.match_pct >= 80]
        print(f"Total job matches: {len(job_matches)}")
        print(f"High matches (>=80): {len(high)}")
        
        print(f"Final AI Match Success Pct: {data.ai_match_success_pct}")

if __name__ == "__main__":
    asyncio.run(main())
