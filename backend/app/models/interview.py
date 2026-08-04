import uuid
from sqlalchemy import Column, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin

class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), index=True, nullable=False)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    scheduled_at = Column(String, nullable=False)
    meeting_link = Column(String, nullable=True)
    status = Column(String, default="scheduled")
    
    feedback = relationship("InterviewFeedback", back_populates="interview", uselist=False)

class InterviewFeedback(Base, TimestampMixin):
    __tablename__ = "interview_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), index=True, nullable=False)
    raw_notes = Column(String, nullable=True)
    ai_summary = Column(String, nullable=True)
    ai_strengths = Column(JSONB, default=[])
    ai_weaknesses = Column(JSONB, default=[])
    ai_recommendation = Column(String, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    interview = relationship("Interview", back_populates="feedback")
