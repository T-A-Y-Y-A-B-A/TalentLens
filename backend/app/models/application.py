import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin, GUID

class Application(Base, TimestampMixin, TenantMixin):
    __tablename__ = "applications"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(GUID(), ForeignKey("candidates.id"), index=True, nullable=False)
    job_id = Column(GUID(), ForeignKey("jobs.id"), index=True, nullable=False)
    current_stage_id = Column(GUID(), ForeignKey("pipeline_stages.id"), nullable=True)
    status = Column(String, default="active")
    applied_at = Column(String, nullable=False)
    
    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", foreign_keys=[job_id], lazy="select")
    history = relationship("ApplicationStageHistory", back_populates="application")

class ApplicationStageHistory(Base, TimestampMixin):
    __tablename__ = "application_stage_history"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(GUID(), ForeignKey("applications.id"), index=True, nullable=False)
    from_stage_id = Column(GUID(), ForeignKey("pipeline_stages.id"), nullable=True)
    to_stage_id = Column(GUID(), ForeignKey("pipeline_stages.id"), nullable=False)
    moved_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    moved_at = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    
    application = relationship("Application", back_populates="history")
