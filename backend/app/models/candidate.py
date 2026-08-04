import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin

class ParseStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class Candidate(Base, TimestampMixin, TenantMixin):
    __tablename__ = "candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    name = Column(String, nullable=False)
    profile = Column(JSONB, default={})
    source = Column(String, nullable=True) # referral/portal/manual
    
    resumes = relationship("Resume", back_populates="candidate")
    applications = relationship("Application", back_populates="candidate")

class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), index=True, nullable=False)
    file_url = Column(String, nullable=False)
    parse_status = Column(Enum(ParseStatus), default=ParseStatus.PENDING, nullable=False)
    raw_text = Column(Text, nullable=True)
    
    candidate = relationship("Candidate", back_populates="resumes")
    parsed_data = relationship("ResumeParsedData", back_populates="resume", uselist=False)

class ResumeParsedData(Base, TimestampMixin):
    __tablename__ = "resume_parsed_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), index=True, nullable=False)
    skills = Column(JSONB, default=[])
    experience = Column(JSONB, default=[])
    education = Column(JSONB, default=[])
    certifications = Column(JSONB, default=[])
    projects = Column(JSONB, default=[])
    
    resume = relationship("Resume", back_populates="parsed_data")

class CandidateEmbedding(Base, TimestampMixin):
    __tablename__ = "candidate_embeddings"
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), primary_key=True)
    qdrant_point_id = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
