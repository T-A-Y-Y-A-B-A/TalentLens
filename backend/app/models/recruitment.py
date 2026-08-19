import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin, TenantMixin, GUID, JSONType

class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"

class WorkType(str, enum.Enum):
    REMOTE = "REMOTE"
    ONSITE = "ONSITE"
    HYBRID = "HYBRID"

class Department(Base, TimestampMixin, TenantMixin):
    __tablename__ = "departments"

    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    
    jobs = relationship("Job", back_populates="department")

class Job(Base, TimestampMixin, TenantMixin):
    __tablename__ = "jobs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    department_id = Column(GUID(), ForeignKey("departments.id"), index=True, nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    requirements = Column(JSONType(), default={})
    work_type = Column(Enum(WorkType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    location = Column(String, nullable=True)
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    salary_range = Column(String, nullable=True)
    company_description = Column(String, nullable=True)
    key_responsibilities = Column(JSONType(), default=list, nullable=True)
    expectations = Column(JSONType(), default=list, nullable=True)
    benefits = Column(JSONType(), default=list, nullable=True)
    
    department = relationship("Department", back_populates="jobs")
    pipeline_stages = relationship("PipelineStage", back_populates="job", cascade="all, delete-orphan")

class PipelineStage(Base, TimestampMixin):
    __tablename__ = "pipeline_stages"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    
    job = relationship("Job", back_populates="pipeline_stages")

class JobEmbedding(Base, TimestampMixin):
    __tablename__ = "job_embeddings"
    
    job_id = Column(GUID(), ForeignKey("jobs.id"), primary_key=True)
    qdrant_point_id = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
