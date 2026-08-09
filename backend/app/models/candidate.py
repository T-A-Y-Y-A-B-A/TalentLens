import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin, GUID, JSONType

class ParseStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    name = Column(String, nullable=False)
    profile = Column(JSONType(), default={})
    source = Column(String, nullable=True) # referral/portal/manual
    hashed_password = Column(String, nullable=True)  # For candidate self-serve portal auth
    
    resumes = relationship("Resume", back_populates="candidate", order_by="desc(Resume.created_at)")
    applications = relationship("Application", back_populates="candidate")
    
    @property
    def resume(self):
        from sqlalchemy import inspect
        from sqlalchemy.orm.attributes import NO_VALUE
        state = inspect(self)
        if "resumes" in state.dict and state.dict["resumes"] is not NO_VALUE and state.dict["resumes"]:
            return state.dict["resumes"][0]
        return None


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(GUID(), ForeignKey("candidates.id"), index=True, nullable=False)
    file_url = Column(String, nullable=False)
    parse_status = Column(Enum(ParseStatus), default=ParseStatus.PENDING, nullable=False)
    raw_text = Column(Text, nullable=True)
    
    candidate = relationship("Candidate", back_populates="resumes")
    parsed_data = relationship("ResumeParsedData", back_populates="resume", uselist=False)

class ResumeParsedData(Base, TimestampMixin):
    __tablename__ = "resume_parsed_data"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    resume_id = Column(GUID(), ForeignKey("resumes.id"), index=True, nullable=False)
    skills = Column(JSONType(), default=[])
    experience = Column(JSONType(), default=[])
    education = Column(JSONType(), default=[])
    certifications = Column(JSONType(), default=[])
    projects = Column(JSONType(), default=[])
    
    resume = relationship("Resume", back_populates="parsed_data")

class CandidateEmbedding(Base, TimestampMixin):
    __tablename__ = "candidate_embeddings"
    
    candidate_id = Column(GUID(), ForeignKey("candidates.id"), primary_key=True)
    qdrant_point_id = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
