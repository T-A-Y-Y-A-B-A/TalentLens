import uuid
from datetime import datetime
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.application import Application, ApplicationStageHistory
from app.models.recruitment import Job, PipelineStage
from app.models.candidate import Candidate
from app.models.ai import AIMatchResult
from app.schemas.analytics import AnalyticsDashboardResponse, TrendDataPoint, DeptDataPoint, SourceDataPoint

async def get_dashboard_analytics(db: AsyncSession, org_id: uuid.UUID) -> AnalyticsDashboardResponse:
    # 1. Fetch all applications for the org
    app_res = await db.execute(
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .options(joinedload(Job.department))
        .options(joinedload(Application.candidate))
        .where(Job.org_id == org_id)
    )
    applications_with_jobs = app_res.all()
    
    # 2. Fetch stage history for the org's applications
    hist_res = await db.execute(
        select(ApplicationStageHistory, Job)
        .join(Application, ApplicationStageHistory.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(joinedload(ApplicationStageHistory.application))
        .options(joinedload(Job.department))
        .where(Job.org_id == org_id)
    )
    stage_history_with_jobs = hist_res.all()
    
    # 3. Fetch PipelineStages for the org's jobs to identify "Hired" and "Interviewing"
    stages_res = await db.execute(
        select(PipelineStage)
        .join(Job)
        .where(Job.org_id == org_id)
    )
    pipeline_stages = stages_res.scalars().all()
    stage_map = {s.id: s.name.lower() for s in pipeline_stages}
    hired_stage_ids = {s.id for s in pipeline_stages if "hire" in s.name.lower() or "offer accepted" in s.name.lower()}
    interviewing_stage_ids = {s.id for s in pipeline_stages if "interview" in s.name.lower()}
    
    # 4. Fetch AI Matches for the org
    ai_res = await db.execute(
        select(AIMatchResult).where(AIMatchResult.org_id == org_id)
    )
    ai_matches = ai_res.scalars().all()
    
    # 5. Fetch Active Jobs
    jobs_res = await db.execute(
        select(Job).where(Job.org_id == org_id, Job.status == "open")
    )
    active_jobs = jobs_res.scalars().all()
    active_jobs_count = len(active_jobs)
    active_jobs_depts = len(set(j.department_id for j in active_jobs if j.department_id))
    
    # --- Compute Metrics ---
    now = datetime.utcnow()
    current_month_str = now.strftime("%Y-%m")
    
    # Pipeline Trend
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    trend_dict = defaultdict(lambda: {"applied": 0, "hired": 0})
    
    # Sources
    source_counts = defaultdict(int)
    
    # Dept Hires
    dept_hires = defaultdict(int)
    
    # Time to Hire & Pipeline Conversion
    total_applied = len(applications_with_jobs)
    total_hired = 0
    time_to_hire_days_list = []
    
    for app, job in applications_with_jobs:
        # Applied trend
        try:
            applied_dt = datetime.fromisoformat(app.applied_at)
            month_key = applied_dt.strftime("%b")
            trend_dict[month_key]["applied"] += 1
        except:
            pass
            
        # Source
        source = app.candidate.source or "Direct"
        source_counts[source] += 1
        
    for hist, job in stage_history_with_jobs:
        if hist.to_stage_id in hired_stage_ids:
            total_hired += 1
            # Hired trend
            try:
                moved_dt = datetime.fromisoformat(hist.moved_at)
                month_key = moved_dt.strftime("%b")
                trend_dict[month_key]["hired"] += 1
                
                # Time to hire
                applied_dt = datetime.fromisoformat(hist.application.applied_at)
                days = (moved_dt - applied_dt).days
                if days < 0: days = 0
                time_to_hire_days_list.append(days)
            except:
                pass
                
            # Dept hires
            dept_name = job.department.name if job.department else "Unassigned"
            dept_hires[dept_name] += 1

    time_to_hire_days = int(sum(time_to_hire_days_list) / len(time_to_hire_days_list)) if time_to_hire_days_list else 0
    pipeline_conversion_pct = round((total_hired / total_applied * 100), 1) if total_applied > 0 else 0.0
    
    # AI Match Success
    high_matches = [m for m in ai_matches if m.match_pct >= 80]
    high_match_progressed = 0
    for m in high_matches:
        # Did this candidate's application for this job reach interviewing or hired?
        app_hist = [h for h, j in stage_history_with_jobs if h.application.candidate_id == m.candidate_id and h.application.job_id == m.job_id]
        if any(h.to_stage_id in interviewing_stage_ids or h.to_stage_id in hired_stage_ids for h in app_hist):
            high_match_progressed += 1
            
    ai_match_success_pct = round((high_match_progressed / len(high_matches) * 100), 1) if high_matches else 0.0
    
    # Format trend data (last 6 months ideally, but simple chronological for MVP)
    pipeline_trend_data = []
    # To keep it simple, just return the months that have data, or a static 6 months ending in current month.
    current_month_idx = now.month - 1
    for i in range(5, -1, -1):
        idx = (current_month_idx - i) % 12
        m_name = months[idx]
        pipeline_trend_data.append(TrendDataPoint(
            month=m_name,
            applied=trend_dict[m_name]["applied"],
            hired=trend_dict[m_name]["hired"]
        ))
        
    dept_data = [DeptDataPoint(name=k, hires=v) for k, v in dept_hires.items()]
    source_data = [SourceDataPoint(name=k.capitalize(), value=v) for k, v in source_counts.items()]
    
    return AnalyticsDashboardResponse(
        time_to_hire_days=time_to_hire_days,
        time_to_hire_trend=0.0, # Placeholder trend
        pipeline_conversion_pct=pipeline_conversion_pct,
        pipeline_conversion_trend=0.0, # Placeholder trend
        ai_match_success_pct=ai_match_success_pct,
        active_jobs_count=active_jobs_count,
        active_jobs_depts=active_jobs_depts,
        pipeline_trend_data=pipeline_trend_data,
        dept_data=dept_data,
        source_data=source_data
    )
