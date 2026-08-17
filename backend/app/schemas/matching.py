from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class JobMatchResponse(BaseModel):
    candidate_id: UUID
    match_pct: float
    missing_skills: List[str]
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    recommendation: Optional[str] = None
    interview_questions: Optional[List[str]] = None
