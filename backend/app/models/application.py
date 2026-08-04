import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin

class Application(Base, TimestampMixin, TenantMixin):
    __tablename__ = "applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), index=True, nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), index=True, nullable=False)
    current_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=True)
    status = Column(String, default="active")
    applied_at = Column(String, nullable=False)
    
    candidate = relationship("Candidate", back_populates="applications")
    history = relationship("ApplicationStageHistory", back_populates="application")

class ApplicationStageHistory(Base, TimestampMixin):
    __tablename__ = "application_stage_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), index=True, nullable=False)
    from_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=True)
    to_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False)
    moved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    moved_at = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    
    application = relationship("Application", back_populates="history")
