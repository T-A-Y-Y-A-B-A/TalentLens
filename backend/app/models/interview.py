import uuid
from sqlalchemy import Column, String, ForeignKey, Float, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, GUID, JSONType


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"
    __table_args__ = (
        UniqueConstraint("application_id", "scheduled_at", name="uq_interviews_application_scheduled_at"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(GUID(), ForeignKey("applications.id"), index=True, nullable=False)
    interviewer_id = Column(GUID(), ForeignKey("users.id"), index=True, nullable=False)
    scheduled_at = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=True, default=60)
    meeting_link = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(String, default="scheduled")

    application = relationship("Application", foreign_keys=[application_id])
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    feedback = relationship("InterviewFeedback", back_populates="interview", uselist=False)


class InterviewFeedback(Base, TimestampMixin):
    __tablename__ = "interview_feedback"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    interview_id = Column(GUID(), ForeignKey("interviews.id"), index=True, nullable=False)
    # Direct tenant column — avoids Interview→Application→Job join for every isolation check
    org_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    # Audit: who submitted the raw notes. RESTRICT so feedback survives user deletion.
    submitted_by = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    raw_notes = Column(String, nullable=True)
    ai_summary = Column(String, nullable=True)
    ai_strengths = Column(JSONType(), default=[])
    ai_weaknesses = Column(JSONType(), default=[])
    ai_recommendation = Column(String, nullable=True)
    overall_score = Column(Float, nullable=True)

    interview = relationship("Interview", back_populates="feedback")
    submitter = relationship("User", foreign_keys=[submitted_by])
