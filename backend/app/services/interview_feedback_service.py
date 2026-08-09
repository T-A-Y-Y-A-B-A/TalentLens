"""
interview_feedback_service.py

Service layer for AI Interview Feedback (Module 9).

Flow:
  1. Fetch Interview, verify org_id via Job join → 404 if not found
  2. Casbin enforce: current user can `interviews, update`
  3. Pull grounding context: candidate resume skills + job description
  4. Compute cache key (prompt_version + hash of raw_notes)
  5. Check for existing feedback row — if cache_key matches, return without re-generating
  6. Call LLM (GROQ_MODEL_MATCH) via call_llm / instructor
  7. Upsert InterviewFeedback row
  8. Log AIUsageLog
"""

import hashlib
import time
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.identity import User
from app.models.interview import Interview, InterviewFeedback
from app.models.application import Application
from app.models.recruitment import Job
from app.models.candidate import Candidate, Resume, ResumeParsedData
from app.models.ai import AIUsageLog
from app.core.security import enforce_role
from app.core.exceptions import DomainException
from app.core.config import settings
from app.ai.llm import call_llm
from app.ai.prompts.interview_feedback_v1 import PROMPT_VERSION, FEEDBACK_SYSTEM_PROMPT

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# LLM output model
# ---------------------------------------------------------------------------

class InterviewFeedbackOutput(BaseModel):
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str = Field(
        ...,
        description="One of: Strong Hire, Hire, No Hire, Strong No Hire"
    )
    overall_score: float = Field(..., ge=0.0, le=10.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_cache_key(raw_notes: str) -> str:
    key_string = f"{PROMPT_VERSION}:{raw_notes}"
    return hashlib.sha256(key_string.encode("utf-8")).hexdigest()


async def _get_interview_with_org_check(
    db: AsyncSession,
    interview_id: uuid.UUID,
    org_id: uuid.UUID,
) -> Interview:
    """
    Fetch Interview verifying it belongs to the user's org via Job.org_id join.
    Returns 404 (not 403) if not found — consistent with platform isolation pattern.
    """
    result = await db.execute(
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(
            joinedload(Interview.application).joinedload(Application.job),
            joinedload(Interview.application).joinedload(Application.candidate),
        )
        .where(Interview.id == interview_id)
        .where(Job.org_id == org_id)
    )
    interview = result.scalars().first()
    if not interview:
        raise DomainException("interview_not_found", "Interview not found", status_code=404)
    return interview


async def _get_grounding_context(
    db: AsyncSession,
    interview: Interview,
) -> dict:
    """
    Pulls candidate resume skills/experience and job description for LLM grounding.
    Returns empty strings gracefully if data is not yet available.
    """
    candidate: Candidate = interview.application.candidate
    job: Job = interview.application.job

    # Try to load the candidate's latest parsed resume data
    resume_skills: List[str] = []
    resume_experience_summary: str = ""

    parsed_res = await db.execute(
        select(ResumeParsedData)
        .join(Resume, ResumeParsedData.resume_id == Resume.id)
        .where(Resume.candidate_id == candidate.id)
        .order_by(Resume.created_at.desc())
        .limit(1)
    )
    parsed_data = parsed_res.scalars().first()
    if parsed_data:
        resume_skills = parsed_data.skills or []
        experience_list = parsed_data.experience or []
        if experience_list:
            first_exp = experience_list[0] if isinstance(experience_list[0], dict) else {}
            resume_experience_summary = (
                f"{first_exp.get('title', '')} at {first_exp.get('company', '')} "
                f"({first_exp.get('duration', '')})"
            ).strip()

    return {
        "candidate_name": candidate.name,
        "job_title": job.title,
        "job_description": (job.description or "")[:1000],  # cap to avoid token explosion
        "resume_skills": resume_skills,
        "resume_experience_summary": resume_experience_summary,
    }


def _build_user_prompt(raw_notes: str, context: dict) -> str:
    skills_str = ", ".join(context["resume_skills"]) if context["resume_skills"] else "Not available"
    return f"""
## Interview Details
- Candidate: {context["candidate_name"]}
- Role: {context["job_title"]}
- Candidate's stated skills (from resume): {skills_str}
- Most recent experience: {context["resume_experience_summary"] or "Not available"}

## Job Description (excerpt)
{context["job_description"] or "Not provided"}

## Interviewer's Raw Notes
{raw_notes}

Based ONLY on the above, produce the structured evaluation JSON.
""".strip()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def submit_feedback(
    db: AsyncSession,
    interview_id: uuid.UUID,
    raw_notes: str,
    current_user: User,
) -> InterviewFeedback:
    """
    Submit interview feedback with AI analysis.
    Upserts the InterviewFeedback row — subsequent calls with changed notes re-generate.
    """
    # 1. Org check (404-not-403)
    interview = await _get_interview_with_org_check(db, interview_id, current_user.org_id)

    # 2. Casbin RBAC at service layer — consistent with platform pattern
    enforce_role(current_user.role.value, "interviews", "update")

    logger.info(
        "interview_feedback_submission_started",
        interview_id=str(interview_id),
        org_id=str(current_user.org_id),
        user_id=str(current_user.id),
    )

    # 3. Check for existing row (upsert pattern)
    existing_res = await db.execute(
        select(InterviewFeedback).where(InterviewFeedback.interview_id == interview_id)
    )
    existing = existing_res.scalars().first()

    # 4. Cache key — prompt_version + hash of notes
    cache_key = _compute_cache_key(raw_notes)

    # 5. Return cached result if notes haven't changed
    if existing and existing.raw_notes == raw_notes:
        logger.info(
            "interview_feedback_cache_hit",
            interview_id=str(interview_id),
            cache_key=cache_key,
        )
        return existing

    # 6. Pull grounding context
    context = await _get_grounding_context(db, interview)
    user_prompt = _build_user_prompt(raw_notes, context)

    # 7. Call LLM
    start_ms = time.time() * 1000
    try:
        llm_result: InterviewFeedbackOutput = await call_llm(
            prompt=user_prompt,
            response_model=InterviewFeedbackOutput,
            model=settings.GROQ_MODEL_MATCH,
            system_prompt=FEEDBACK_SYSTEM_PROMPT,
            temperature=0.1,
        )
    except Exception as e:
        logger.error(
            "interview_feedback_llm_error",
            interview_id=str(interview_id),
            error=str(e),
        )
        raise DomainException(
            "llm_unavailable",
            "AI feedback generation failed. Please try again.",
            status_code=503,
        ) from e

    latency_ms = time.time() * 1000 - start_ms

    # 8. Upsert
    if existing:
        existing.raw_notes = raw_notes
        existing.ai_summary = llm_result.summary
        existing.ai_strengths = llm_result.strengths
        existing.ai_weaknesses = llm_result.weaknesses
        existing.ai_recommendation = llm_result.recommendation
        existing.overall_score = llm_result.overall_score
        existing.submitted_by = current_user.id
        feedback_row = existing
    else:
        feedback_row = InterviewFeedback(
            interview_id=interview_id,
            org_id=current_user.org_id,
            submitted_by=current_user.id,
            raw_notes=raw_notes,
            ai_summary=llm_result.summary,
            ai_strengths=llm_result.strengths,
            ai_weaknesses=llm_result.weaknesses,
            ai_recommendation=llm_result.recommendation,
            overall_score=llm_result.overall_score,
        )
        db.add(feedback_row)

    # 9. Log AIUsageLog — consistent with matching/copilot pattern
    usage_log = AIUsageLog(
        org_id=current_user.org_id,
        user_id=current_user.id,
        endpoint="interview_feedback",
        prompt_version=PROMPT_VERSION,
        cache_hit=False,
        candidates_matched=0,
        latency_ms=round(latency_ms, 2),
    )
    db.add(usage_log)

    await db.commit()
    await db.refresh(feedback_row)

    logger.info(
        "interview_feedback_submission_success",
        interview_id=str(interview_id),
        recommendation=llm_result.recommendation,
        overall_score=llm_result.overall_score,
    )

    return feedback_row


async def get_feedback(
    db: AsyncSession,
    interview_id: uuid.UUID,
    current_user: User,
) -> Optional[InterviewFeedback]:
    """
    Fetch existing feedback for an interview. Returns None if not yet generated.
    """
    # Org check (404-not-403)
    await _get_interview_with_org_check(db, interview_id, current_user.org_id)

    # Casbin: interviewer can read, hr_manager/recruiter can manage (which includes read via policy)
    enforce_role(current_user.role.value, "interviews", "read")

    result = await db.execute(
        select(InterviewFeedback)
        .where(InterviewFeedback.interview_id == interview_id)
        .where(InterviewFeedback.org_id == current_user.org_id)
    )
    return result.scalars().first()
