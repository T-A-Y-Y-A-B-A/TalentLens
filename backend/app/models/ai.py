import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, JSONType

class AIMatchResult(Base):
    __tablename__ = "ai_match_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    org_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    ats_score = Column(Float, nullable=True) # deterministic keyword match score
    strengths = Column(JSONType, nullable=False, default=list)
    weaknesses = Column(JSONType, nullable=False, default=list)
    recommendation = Column(String, nullable=False)
    interview_questions = Column(JSONType, nullable=False, default=list)

    prompt_version = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_ai_match_result"),)
    
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

class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    match_pct = Column(Integer, nullable=False)
    matched_skills = Column(JSONType, nullable=False, default=list)
    missing_skills = Column(JSONType, nullable=False, default=list)
    ai_explanation = Column(String, nullable=True)
    ai_explanation_generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate_match"),)
