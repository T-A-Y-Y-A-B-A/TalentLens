from datetime import datetime, timezone
import json
from uuid import UUID

from app.models.ai import JobMatch
from app.models.recruitment import Job
from app.ai.llm import call_llm
from pydantic import BaseModel

class ExplanationResult(BaseModel):
    explanation: str

async def generate_match_explanation(job_match: JobMatch, job: Job) -> str:
    """
    Takes already-computed matched/missing skills — never re-runs matching.
    """
    prompt = f"""
    You are a career coach explaining a job match to a candidate.
    Matched skills: {json.dumps(job_match.matched_skills)}
    Missing skills: {json.dumps(job_match.missing_skills)}
    Match score: {job_match.match_pct}%
    Job title: {job.title}

    Write a short (2-3 sentence) encouraging but honest explanation of the fit,
    calling out what to highlight and what gap to address. Do not invent skills
    not in the lists above.
    """
    
    # We use a relatively low temperature for consistent explanation tone
    response = await call_llm(
        prompt=prompt,
        response_model=ExplanationResult,
        system_prompt="You are a helpful and concise career coach.",
        temperature=0.3
    )
    
    return response.explanation
