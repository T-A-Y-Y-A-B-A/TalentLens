from pydantic import BaseModel
from typing import List

class TrendDataPoint(BaseModel):
    month: str
    applied: int
    hired: int

class DeptDataPoint(BaseModel):
    name: str
    hires: int

class SourceDataPoint(BaseModel):
    name: str
    value: int

class AnalyticsDashboardResponse(BaseModel):
    time_to_hire_days: int
    time_to_hire_trend: float
    pipeline_conversion_pct: float
    pipeline_conversion_trend: float
    active_jobs_count: int
    active_jobs_depts: int
    pipeline_trend_data: List[TrendDataPoint]
    dept_data: List[DeptDataPoint]
    source_data: List[SourceDataPoint]
