import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class InterviewBase(BaseModel):
    application_id: uuid.UUID
    interviewer_id: uuid.UUID
    scheduled_at: str
    duration_minutes: int
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "scheduled"


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    scheduled_at: Optional[str] = None
    duration_minutes: Optional[int] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class InterviewRead(InterviewBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# --- Interview Feedback ---

class FeedbackSubmit(BaseModel):
    """Request body for POST /interviews/{id}/feedback"""
    raw_notes: str


class FeedbackRead(BaseModel):
    """Response model for interview feedback endpoints"""
    id: uuid.UUID
    interview_id: uuid.UUID
    org_id: uuid.UUID
    submitted_by: uuid.UUID
    raw_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_strengths: Optional[List[str]] = []
    ai_weaknesses: Optional[List[str]] = []
    ai_recommendation: Optional[str] = None
    overall_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Extended read model for frontend dashboard detail view
class InterviewDetailRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    candidate_name: str
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    job_title: str
    current_stage_id: Optional[uuid.UUID] = None
    interviewer_id: uuid.UUID
    interviewer_name: str
    interviewer_role: Optional[str] = None
    scheduled_at: str
    duration_minutes: int
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    feedback: Optional[FeedbackRead] = None

    model_config = ConfigDict(from_attributes=True)


