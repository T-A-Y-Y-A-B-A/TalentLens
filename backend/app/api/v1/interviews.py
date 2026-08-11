import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from sqlalchemy.exc import IntegrityError
from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.identity import User
from app.models.interview import Interview
from app.models.application import Application, ApplicationStageHistory
from app.models.recruitment import Job, PipelineStage
from app.models.candidate import Candidate
from app.schemas.interview import InterviewCreate, InterviewUpdate, InterviewRead, InterviewDetailRead

from app.workers.tasks.interview_email import send_interview_invite_email, send_interview_update_email, send_interview_cancel_email

router = APIRouter(prefix="/interviews", tags=["interviews"])

@router.post("", response_model=InterviewRead)
async def create_interview(
    interview_in: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "manage"))
):
    # Verify application exists and belongs to org
    app_res = await db.execute(
        select(Application).join(Job)
        .options(joinedload(Application.job), joinedload(Application.candidate))
        .where(Application.id == interview_in.application_id, Job.org_id == current_user.org_id)
    )
    application = app_res.scalars().first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found in your organization")

    # Verify interviewer exists
    int_res = await db.execute(select(User).where(User.id == interview_in.interviewer_id))
    interviewer = int_res.scalars().first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    # Check for existing scheduled interview for this application at the given time slot
    existing_res = await db.execute(
        select(Interview).where(
            Interview.application_id == interview_in.application_id,
            Interview.scheduled_at == interview_in.scheduled_at,
            Interview.status != "cancelled"
        )
    )
    if existing_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An interview is already scheduled for this application at this time slot."
        )

    try:
        from datetime import datetime, timezone
        
        # 1. Look up interview-type pipeline stage for this job
        stage_res = await db.execute(
            select(PipelineStage)
            .where(PipelineStage.job_id == application.job_id)
            .order_by(PipelineStage.order_index)
        )
        all_stages = stage_res.scalars().all()
        interview_stage = next(
            (s for s in all_stages if "interview" in s.name.lower()), None
        )

        # 2. Create interview
        interview = Interview(**interview_in.dict())
        db.add(interview)

        # 3. Conditionally advance stage — in same transaction
        history_row = None
        if interview_stage:
            current_stage = next(
                (s for s in all_stages if s.id == application.current_stage_id), None
            )
            current_order = current_stage.order_index if current_stage else -1
            if interview_stage.order_index > current_order:
                old_stage_id = application.current_stage_id
                application.current_stage_id = interview_stage.id
                application.updated_at = datetime.now(timezone.utc)
                history_row = ApplicationStageHistory(
                    application_id=application.id,
                    from_stage_id=old_stage_id,
                    to_stage_id=interview_stage.id,
                    moved_by=current_user.id,
                    moved_at=datetime.now(timezone.utc).isoformat(),
                    notes=f"Auto-advanced to Interview stage on interview creation (actor: {current_user.email})"
                )
                db.add(history_row)
        else:
            import structlog
            structlog.get_logger().warning("interview_stage_not_found",
                job_id=str(application.job_id),
                org_id=str(current_user.org_id)
            )

        # 4. Single atomic commit
        await db.commit()
        await db.refresh(interview)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An interview is already scheduled for this application at this time slot."
        )
    
    # Enqueue email task (non-blocking, fail-safe)
    try:
        send_interview_invite_email.delay(
            str(interview.id),
            application.candidate.email,
            interviewer.email,
            application.candidate.name,
            interviewer.full_name,
            application.job.title,
            interview.scheduled_at,
            interview.duration_minutes,
            interview.meeting_link,
            interview.notes,
            candidate_id=str(application.candidate_id)
        )
    except Exception as e:
        import structlog
        structlog.get_logger().warning("failed_to_enqueue_interview_invite_email", error=str(e))
    
    return interview

@router.get("", response_model=List[InterviewDetailRead])
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "read"))
):
    # Fetch all interviews for the org
    query = (
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(
            joinedload(Interview.application).joinedload(Application.candidate),
            joinedload(Interview.application).joinedload(Application.job),
            joinedload(Interview.feedback)
        )
        .where(Job.org_id == current_user.org_id)
        .order_by(Interview.scheduled_at)
    )
    
    if current_user.role.value == "interviewer":
        query = query.where(Interview.interviewer_id == current_user.id)
        
    res = await db.execute(query)
    interviews = res.scalars().all()
    
    # We need interviewer names. A simple way is to load users.
    user_ids = {i.interviewer_id for i in interviews}
    users = {}
    if user_ids:
        u_res = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in u_res.scalars().all():
            users[u.id] = u
            
    results = []
    for i in interviews:
        u = users.get(i.interviewer_id)
        interviewer_name = u.full_name if u else "Unknown"
        interviewer_role_str = u.role.value if (u and hasattr(u, "role") and hasattr(u.role, "value")) else (str(u.role) if u else "Interviewer")
        
        fb_read = None
        if i.feedback:
            fb_read = FeedbackRead.model_validate(i.feedback)
            
        results.append(InterviewDetailRead(
            id=i.id,
            application_id=i.application_id,
            candidate_id=i.application.candidate_id,
            job_id=i.application.job_id,
            candidate_name=i.application.candidate.name,
            candidate_email=i.application.candidate.email,
            candidate_phone=i.application.candidate.phone,
            job_title=i.application.job.title,
            current_stage_id=i.application.current_stage_id,
            interviewer_id=i.interviewer_id,
            interviewer_name=interviewer_name,
            interviewer_role=interviewer_role_str,
            scheduled_at=i.scheduled_at,
            duration_minutes=i.duration_minutes,
            meeting_link=i.meeting_link,
            notes=i.notes,
            status=i.status,
            created_at=i.created_at,
            feedback=fb_read
        ))
    return results

@router.get("/{interview_id}", response_model=InterviewDetailRead)
async def get_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "read"))
):
    query = (
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(
            joinedload(Interview.application).joinedload(Application.candidate),
            joinedload(Interview.application).joinedload(Application.job),
            joinedload(Interview.feedback)
        )
        .where(Interview.id == interview_id, Job.org_id == current_user.org_id)
    )
    
    if current_user.role.value == "interviewer":
        query = query.where(Interview.interviewer_id == current_user.id)
        
    res = await db.execute(query)
    i = res.scalars().first()
    if not i:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    u_res = await db.execute(select(User).where(User.id == i.interviewer_id))
    u = u_res.scalars().first()
    
    interviewer_role_str = u.role.value if (u and hasattr(u, "role") and hasattr(u.role, "value")) else (str(u.role) if u else "Interviewer")
    
    fb_read = None
    if i.feedback:
        fb_read = FeedbackRead.model_validate(i.feedback)

    return InterviewDetailRead(
        id=i.id,
        application_id=i.application_id,
        candidate_id=i.application.candidate_id,
        job_id=i.application.job_id,
        candidate_name=i.application.candidate.name,
        candidate_email=i.application.candidate.email,
        candidate_phone=i.application.candidate.phone,
        job_title=i.application.job.title,
        current_stage_id=i.application.current_stage_id,
        interviewer_id=i.interviewer_id,
        interviewer_name=u.full_name if u else "Unknown",
        interviewer_role=interviewer_role_str,
        scheduled_at=i.scheduled_at,
        duration_minutes=i.duration_minutes,
        meeting_link=i.meeting_link,
        notes=i.notes,
        status=i.status,
        created_at=i.created_at,
        feedback=fb_read
    )

@router.patch("/{interview_id}", response_model=InterviewRead)
async def update_interview(
    interview_id: uuid.UUID,
    update_in: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "manage"))
):
    res = await db.execute(
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(
            joinedload(Interview.application).joinedload(Application.candidate),
            joinedload(Interview.application).joinedload(Application.job)
        )
        .where(Interview.id == interview_id, Job.org_id == current_user.org_id)
    )
    interview = res.scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    update_data = update_in.dict(exclude_unset=True)
    needs_email = False
    
    # Check if we need to send a rescheduled email
    if 'scheduled_at' in update_data and update_data['scheduled_at'] != interview.scheduled_at:
        needs_email = True
    if 'meeting_link' in update_data and update_data['meeting_link'] != interview.meeting_link:
        needs_email = True
        
    for field, value in update_data.items():
        setattr(interview, field, value)
        
    await db.commit()
    await db.refresh(interview)
    
    if needs_email:
        u_res = await db.execute(select(User).where(User.id == interview.interviewer_id))
        u = u_res.scalars().first()
        try:
            send_interview_update_email.delay(
                str(interview.id),
                interview.application.candidate.email,
                u.email if u else None,
                interview.application.candidate.name,
                u.full_name if u else "Interviewer",
                interview.application.job.title,
                interview.scheduled_at,
                interview.duration_minutes,
                interview.meeting_link,
                interview.notes,
                candidate_id=str(interview.application.candidate_id)
            )
        except Exception as e:
            import structlog
            structlog.get_logger().warning("failed_to_enqueue_interview_update_email", error=str(e))
        
    return interview

@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "manage"))
):
    res = await db.execute(
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(
            joinedload(Interview.application).joinedload(Application.candidate),
            joinedload(Interview.application).joinedload(Application.job)
        )
        .where(Interview.id == interview_id, Job.org_id == current_user.org_id)
    )
    interview = res.scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    interview.status = "cancelled"
    await db.commit()
    
    u_res = await db.execute(select(User).where(User.id == interview.interviewer_id))
    u = u_res.scalars().first()
    
    try:
        send_interview_cancel_email.delay(
            str(interview.id),
            interview.application.candidate.email,
            u.email if u else None,
            interview.application.candidate.name,
            u.full_name if u else "Interviewer",
            interview.application.job.title,
            interview.scheduled_at,
            candidate_id=str(interview.application.candidate_id)
        )
    except Exception as e:
        import structlog
        structlog.get_logger().warning("failed_to_enqueue_interview_cancel_email", error=str(e))


# ---------------------------------------------------------------------------
# Interview Feedback endpoints
# ---------------------------------------------------------------------------

from app.schemas.interview import FeedbackSubmit, FeedbackRead
from app.services.interview_feedback_service import submit_feedback, get_feedback


@router.post("/{interview_id}/feedback", response_model=FeedbackRead, status_code=201)
async def create_or_update_feedback(
    interview_id: uuid.UUID,
    body: FeedbackSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "update")),
):
    """
    Submit (or re-generate) AI interview feedback for an interview.
    Casbin check is also enforced at the service layer for defence-in-depth.
    """
    return await submit_feedback(db, interview_id, body.raw_notes, current_user)


@router.get("/{interview_id}/feedback", response_model=FeedbackRead)
async def read_feedback(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews", "read")),
):
    """
    Retrieve existing AI feedback for an interview.
    Returns 404 if feedback has not yet been generated.
    """
    from app.core.exceptions import DomainException
    feedback = await get_feedback(db, interview_id, current_user)
    if not feedback:
        raise DomainException("feedback_not_found", "Feedback not yet generated for this interview", status_code=404)
    return feedback

