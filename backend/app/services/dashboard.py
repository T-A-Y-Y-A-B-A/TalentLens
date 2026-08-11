"""
Dashboard stats service — all queries org-scoped via Job.org_id.
Never uses a client-supplied org_id; caller must pass current_user.org_id.

Queries:
  active_jobs         : COUNT(jobs) WHERE status='open' AND org_id=?
  total_candidates    : COUNT(DISTINCT applications.candidate_id)
                        JOIN jobs ON applications.job_id = jobs.id
                        WHERE jobs.org_id = ?
  interviews_today    : COUNT(interviews)
                        JOIN applications -> jobs WHERE jobs.org_id = ?
                        AND interviews.scheduled_at LIKE '<today>%'
                        AND interviews.status != 'cancelled'
  new_applications_24h: COUNT(applications)
                        JOIN jobs WHERE jobs.org_id = ?
                        AND applications.applied_at >= (now - 24h) ISO string
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.interview import Interview
from app.models.recruitment import Job


async def get_dashboard_stats(db: AsyncSession, org_id: uuid.UUID) -> dict:
    # ------------------------------------------------------------------
    # 1. Active Jobs
    #    SELECT COUNT(*) FROM jobs WHERE org_id=? AND status='open'
    # ------------------------------------------------------------------
    active_jobs_res = await db.execute(
        select(func.count(Job.id)).where(
            Job.org_id == org_id,
            Job.status == "open",
        )
    )
    active_jobs: int = active_jobs_res.scalar_one()

    # ------------------------------------------------------------------
    # 2. Total Candidates
    #    SELECT COUNT(DISTINCT applications.candidate_id)
    #    FROM applications JOIN jobs ON applications.job_id = jobs.id
    #    WHERE jobs.org_id = ?
    #    (candidates have no direct org_id — scoped through Application→Job)
    # ------------------------------------------------------------------
    total_candidates_res = await db.execute(
        select(func.count(distinct(Application.candidate_id)))
        .join(Job, Application.job_id == Job.id)
        .where(Job.org_id == org_id)
    )
    total_candidates: int = total_candidates_res.scalar_one()

    # ------------------------------------------------------------------
    # 3. Interviews Today
    #    scheduled_at is stored as ISO string e.g. "2026-08-09T14:00:00Z"
    #    Match on the UTC date prefix "YYYY-MM-DD"
    #    JOIN applications -> jobs for org scoping
    #    Exclude cancelled interviews
    # ------------------------------------------------------------------
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    interviews_today_res = await db.execute(
        select(func.count(Interview.id))
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .where(
            Job.org_id == org_id,
            Interview.scheduled_at.like(f"{today_utc}%"),
            Interview.status != "cancelled",
        )
    )
    interviews_today: int = interviews_today_res.scalar_one()

    # ------------------------------------------------------------------
    # 4. New Applications in last 24 hours
    #    applied_at is stored as ISO string
    #    Compute threshold as ISO string and do a string comparison
    #    (ISO strings sort lexicographically for dates in the same TZ)
    # ------------------------------------------------------------------
    threshold_dt = datetime.now(timezone.utc) - timedelta(hours=24)
    threshold_str = threshold_dt.strftime("%Y-%m-%dT%H:%M:%S")
    new_applications_res = await db.execute(
        select(func.count(Application.id))
        .join(Job, Application.job_id == Job.id)
        .where(
            Job.org_id == org_id,
            Application.applied_at >= threshold_str,
        )
    )
    new_applications_24h: int = new_applications_res.scalar_one()

    return {
        "active_jobs": active_jobs,
        "total_candidates": total_candidates,
        "interviews_today": interviews_today,
        "new_applications_24h": new_applications_24h,
    }
