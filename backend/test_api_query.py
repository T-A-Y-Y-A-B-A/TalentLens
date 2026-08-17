import sys
import os
sys.path.insert(0, os.getcwd())

import asyncio
from sqlalchemy import text, select, and_, func
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job, JobStatus
from app.models.ai import JobMatch
from app.models.identity import Organization
from sqlalchemy.orm import joinedload
from uuid import UUID

async def main():
    async with AsyncSessionLocal() as session:
        # Just use any candidate ID for testing
        candidate_id = "d29f41e3-6920-4174-b2c6-5f4ac02055c8" # from earlier, or just any UUID
        
        try:
            stmt = (
                select(Job, JobMatch.match_pct, JobMatch.matched_skills, JobMatch.missing_skills, Organization.name.label("organization_name"))
                .options(joinedload(Job.department))
                .outerjoin(
                    JobMatch,
                    and_(JobMatch.job_id == Job.id, JobMatch.candidate_id == UUID(candidate_id))
                )
                .join(Organization, Organization.id == Job.org_id)
                .where(Job.status == JobStatus.OPEN)
                .where(Job.deleted_at.is_(None))
                .order_by(func.coalesce(JobMatch.match_pct, 0).desc(), Job.created_at.desc())
            )
            
            result = await session.execute(stmt)
            rows = result.all()
            print(f"Query successful, found {len(rows)} rows.")
            
            for job, pct, matched, missing, org_name in rows:
                required_skills = (job.requirements or {}).get("required_skills", []) if isinstance(job.requirements, dict) else getattr(job.requirements, "required_skills", [])
                
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
