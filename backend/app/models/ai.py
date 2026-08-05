import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin, GUID, JSONType

class AiMatchResult(Base, TimestampMixin):
    __tablename__ = "ai_match_results"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(GUID(), ForeignKey("applications.id"), index=True, nullable=False)
    match_pct = Column(Float, nullable=False)
    missing_skills = Column(JSONType(), default=[])
    strengths = Column(JSONType(), default=[])
    weaknesses = Column(JSONType(), default=[])
    recommendation = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    model_used = Column(String, nullable=False)
    generated_at = Column(String, nullable=False)
    
class AiUsageLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = "ai_usage_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    feature = Column(String, nullable=False) # matching/copilot/feedback/jd_generation
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=False)
    cache_hit = Column(Boolean, default=False)
