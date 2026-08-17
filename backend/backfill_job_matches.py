import asyncio
import re
from uuid import UUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job, JobStatus
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.ai import JobMatch

MATCH_THRESHOLD = 20

def compute_keyword_match(candidate_skills: list[str], job_requirements: dict) -> dict:
    """
    Denominator = job's required_skills (locked decision).
    missing_skills = requirements the candidate does NOT cover.
    """
    required_skills = job_requirements.get("required_skills", []) if job_requirements else []
    normalized_requirements = {s.strip().lower() for s in required_skills if s and s.strip()}
    normalized_candidate_skills = {s.strip().lower() for s in (candidate_skills or []) if s and s.strip()}

    if not normalized_requirements:
        return {"match_pct": 0, "matched_skills": [], "missing_skills": []}

    matched, missing = set(), set()
    for req in normalized_requirements:
        req_pattern = r"\b" + re.escape(req) + r"\b"
        is_matched = any(
            re.search(req_pattern, cskill) or re.search(r"\b" + re.escape(cskill) + r"\b", req)
            for cskill in normalized_candidate_skills
        )
        (matched if is_matched else missing).add(req)

    match_pct = round((len(matched) / len(normalized_requirements)) * 100)
    return {"match_pct": match_pct, "matched_skills": sorted(matched), "missing_skills": sorted(missing)}


async def bulk_upsert_job_matches(session, rows: list[dict]):
    if not rows:
        return
    stmt = pg_insert(JobMatch).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_job_candidate_match",
        set_={
            "match_pct": stmt.excluded.match_pct,
            "matched_skills": stmt.excluded.matched_skills,
            "missing_skills": stmt.excluded.missing_skills,
            "updated_at": func.now()
        },
    )
    await session.execute(stmt)
    await session.commit()


async def run_backfill():
    async with AsyncSessionLocal() as session:
        print("Fetching all OPEN jobs...")
        jobs = (await session.execute(
            select(Job).where(Job.status == JobStatus.OPEN, Job.deleted_at.is_(None))
        )).scalars().all()
        
        print("Fetching candidates with skills (latest resume only)...")
        candidates_data = (await session.execute(
            select(Candidate, ResumeParsedData.skills)
            .join(Resume, Resume.candidate_id == Candidate.id)
            .join(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
            .where(ResumeParsedData.skills != None)
            .distinct(Candidate.id)
            .order_by(Candidate.id, Resume.created_at.desc())
        )).all()
        
        print(f"Found {len(jobs)} jobs and {len(candidates_data)} candidates with parsed skills.")
        
        rows = []
        for job in jobs:
            for candidate, skills in candidates_data:
                result = compute_keyword_match(skills, job.requirements)
                if result["match_pct"] >= MATCH_THRESHOLD:
                    import uuid
                    rows.append({
                        "id": uuid.uuid4(),
                        "job_id": job.id,
                        "candidate_id": candidate.id,
                        **{k: v for k, v in result.items()},
                    })
                    
        unique_rows = {}
        for row in rows:
            key = (row["job_id"], row["candidate_id"])
            if key not in unique_rows or row["match_pct"] > unique_rows[key]["match_pct"]:
                unique_rows[key] = row
                
        print(f"Upserting {len(unique_rows)} unique matching rows...")
        await bulk_upsert_job_matches(session, list(unique_rows.values()))
        print("Done!")

if __name__ == "__main__":
    asyncio.run(run_backfill())
