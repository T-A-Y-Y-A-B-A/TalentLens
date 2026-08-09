import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, JSONType

class AIMatchResult(Base):
    __tablename__ = "ai_match_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    org_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    match_pct = Column(Float, nullable=False)
    ats_score = Column(Float, nullable=True)
    missing_skills = Column(JSONType, nullable=False, default=list)
    strengths = Column(JSONType, nullable=False, default=list)
    weaknesses = Column(JSONType, nullable=False, default=list)
    recommendation = Column(String, nullable=False)
    interview_questions = Column(JSONType, nullable=False, default=list)

    prompt_version = Column(String, nullable=False)
    cache_key = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization")
    job = relationship("Job")
    candidate = relationship("Candidate")


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    org_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    endpoint = Column(String, nullable=False) # e.g. "POST /api/v1/jobs/{id}/match"
    prompt_version = Column(String, nullable=False)
    
    # Metrics
    prompt_tokens = Column(Float, nullable=False, default=0)
    completion_tokens = Column(Float, nullable=False, default=0)
    total_tokens = Column(Float, nullable=False, default=0)
    latency_ms = Column(Float, nullable=False, default=0)
    
    cache_hit = Column(Boolean, nullable=False, default=False)
    candidates_matched = Column(Float, nullable=False, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    organization = relationship("Organization")
    user = relationship("User")
