import re
from uuid import UUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.recruitment import Job, JobStatus
from app.models.candidate import Candidate
from app.models.ai import JobMatch

MATCH_THRESHOLD = 35


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


@celery_app.task(name="match_job_to_all_candidates")
def match_job_to_all_candidates(job_id: str):
    import asyncio
    asyncio.run(_match_job_to_all_candidates(job_id))


async def _match_job_to_all_candidates(job_id: str):
    from app.models.candidate import Resume, ResumeParsedData
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            job = await session.get(Job, UUID(job_id))
        if not job:
            return
        
        candidates_data = (await session.execute(
            select(Candidate, ResumeParsedData.skills)
            .join(Resume, Resume.candidate_id == Candidate.id)
            .join(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
            .where(ResumeParsedData.skills != None)
            .distinct(Candidate.id)
            .order_by(Candidate.id, Resume.created_at.desc())
        )).all()

        # Fetch existing JobMatch pairs for this job so pairs already
        # matched can be refreshed even if the new score drops below threshold.
        existing_candidate_ids = set(
            (await session.execute(
                select(JobMatch.candidate_id).where(JobMatch.job_id == job.id)
            )).scalars().all()
        )

        rows = []
        for candidate, skills in candidates_data:
            print(f"[DEBUG MATCH_JOB] Candidate ID: {candidate.id}, Skills passed in: {skills}")
            result = compute_keyword_match(skills, job.requirements)
            print(f"[DEBUG RESULT] Job ID: {job.id}, match_pct: {result['match_pct']}, matched: {result['matched_skills']}, missing: {result['missing_skills']}")
            has_existing_row = candidate.id in existing_candidate_ids
            if result["match_pct"] >= MATCH_THRESHOLD or has_existing_row:
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
        await bulk_upsert_job_matches(session, list(unique_rows.values()))
    finally:
        await engine_local.dispose()


@celery_app.task(name="match_candidate_to_all_jobs")
def match_candidate_to_all_jobs(candidate_id: str):
    import asyncio
    asyncio.run(_match_candidate_to_all_jobs(candidate_id))


async def _match_candidate_to_all_jobs(candidate_id: str):
    from app.models.candidate import Resume, ResumeParsedData
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    async_session = async_sessionmaker(engine_local, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            candidate_data = (await session.execute(
            select(Candidate, ResumeParsedData.skills)
            .join(Resume, Resume.candidate_id == Candidate.id)
            .join(ResumeParsedData, ResumeParsedData.resume_id == Resume.id)
            .where(Candidate.id == UUID(candidate_id))
            .where(ResumeParsedData.skills != None)
            .order_by(Resume.created_at.desc())
        )).first()
        
        if not candidate_data:
            return
            
        candidate, skills = candidate_data
        
        jobs = (await session.execute(
            select(Job).where(Job.status == JobStatus.OPEN, Job.deleted_at.is_(None))
        )).scalars().all()

        # Fetch existing JobMatch pairs for this candidate so we know which
        # pairs are allowed to be refreshed even when below threshold.
        existing_job_ids = set(
            (await session.execute(
                select(JobMatch.job_id).where(JobMatch.candidate_id == candidate.id)
            )).scalars().all()
        )

        rows = []
        for job in jobs:
            print(f"[DEBUG MATCH_CANDIDATE] Job ID: {job.id}, Skills passed in: {skills}")
            result = compute_keyword_match(skills, job.requirements)
            print(f"[DEBUG RESULT] Job ID: {job.id}, match_pct: {result['match_pct']}, matched: {result['matched_skills']}, missing: {result['missing_skills']}")
            has_existing_row = job.id in existing_job_ids
            if result["match_pct"] >= MATCH_THRESHOLD or has_existing_row:
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
        await bulk_upsert_job_matches(session, list(unique_rows.values()))
    finally:
        await engine_local.dispose()
