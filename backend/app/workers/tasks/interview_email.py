import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import structlog
from typing import Optional

from app.workers.celery_app import celery_app
from app.core.config import settings

logger = structlog.get_logger()

def _send_email(subject: str, body: str, to_emails: list[str]):
    if getattr(settings, "EMAIL_BACKEND", "console").lower() == "smtp":
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
            server.send_message(msg)
            server.quit()
            logger.info("interview_email_sent_smtp", to_emails=to_emails, subject=subject)
        except Exception as e:
            logger.error("interview_email_smtp_failed", to_emails=to_emails, error=str(e))
    else:
        # Fallback to console logging
        logger.info(
            "interview_email_simulated", 
            to_emails=to_emails, 
            subject=subject,
            body=body
        )

@celery_app.task(name="send_interview_invite_email")
def send_interview_invite_email(
    interview_id: str,
    candidate_email: str,
    interviewer_email: str,
    candidate_name: str,
    interviewer_name: str,
    job_title: str,
    scheduled_at: str,
    duration_minutes: int,
    meeting_link: Optional[str] = None,
    notes: Optional[str] = None,
    *,
    candidate_id: Optional[str] = None
):
    logger.info("send_interview_invite_email_started", interview_id=interview_id)
    
    subject = f"Interview Scheduled: {job_title} - {candidate_name}"
    
    body = f"Hello,\n\nAn interview has been scheduled for the {job_title} position.\n\n"
    body += f"Candidate: {candidate_name}\n"
    body += f"Interviewer: {interviewer_name}\n"
    body += f"Time: {scheduled_at}\n"
    body += f"Duration: {duration_minutes} minutes\n\n"
    
    if meeting_link:
        body += f"Meeting Link: {meeting_link}\n\n"
        
    if notes:
        body += f"Notes: {notes}\n\n"
        
    body += "Best regards,\nTalentLens Team"
    
    to_emails = [email for email in [candidate_email, interviewer_email] if email]
    _send_email(subject, body, to_emails)

    if candidate_id:
        import asyncio
        from app.core.database import AsyncSessionLocal, engine
        from app.models.support import Notification
        
        async def _insert_notification():
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
            from sqlalchemy.pool import NullPool
            from app.core.config import settings
            engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
            async_session = async_sessionmaker(engine_local, expire_on_commit=False)
            
            try:
                async with async_session() as db:
                    notif = Notification(
                        recipient_type="candidate",
                        recipient_id=candidate_id,
                        type="interview_invite",
                        channel="email",
                        payload={"interview_id": interview_id, "job_title": job_title, "scheduled_at": scheduled_at}
                    )
                    db.add(notif)
                    await db.commit()
            finally:
                await engine_local.dispose()
            
        asyncio.run(_insert_notification())


@celery_app.task(name="send_interview_update_email")
def send_interview_update_email(
    interview_id: str,
    candidate_email: str,
    interviewer_email: str,
    candidate_name: str,
    interviewer_name: str,
    job_title: str,
    scheduled_at: str,
    duration_minutes: int,
    meeting_link: Optional[str] = None,
    notes: Optional[str] = None,
    *,
    candidate_id: Optional[str] = None
):
    logger.info("send_interview_update_email_started", interview_id=interview_id)
    
    subject = f"Interview Updated: {job_title} - {candidate_name}"
    
    body = f"Hello,\n\nThe interview for the {job_title} position has been updated.\n\n"
    body += f"Candidate: {candidate_name}\n"
    body += f"Interviewer: {interviewer_name}\n"
    body += f"New Time: {scheduled_at}\n"
    body += f"Duration: {duration_minutes} minutes\n\n"
    
    if meeting_link:
        body += f"Meeting Link: {meeting_link}\n\n"
        
    if notes:
        body += f"Notes: {notes}\n\n"
        
    body += "Best regards,\nTalentLens Team"
    
    to_emails = [email for email in [candidate_email, interviewer_email] if email]
    _send_email(subject, body, to_emails)

    if candidate_id:
        import asyncio
        from app.core.database import AsyncSessionLocal, engine
        from app.models.support import Notification
        
        async def _insert_notification():
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
            from sqlalchemy.pool import NullPool
            from app.core.config import settings
            engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
            async_session = async_sessionmaker(engine_local, expire_on_commit=False)
            
            try:
                async with async_session() as db:
                    notif = Notification(
                        recipient_type="candidate",
                        recipient_id=candidate_id,
                        type="interview_update",
                        channel="email",
                        payload={"interview_id": interview_id, "job_title": job_title, "scheduled_at": scheduled_at}
                    )
                    db.add(notif)
                    await db.commit()
            finally:
                await engine_local.dispose()
            
        asyncio.run(_insert_notification())


@celery_app.task(name="send_interview_cancel_email")
def send_interview_cancel_email(
    interview_id: str,
    candidate_email: str,
    interviewer_email: str,
    candidate_name: str,
    interviewer_name: str,
    job_title: str,
    scheduled_at: str,
    *,
    candidate_id: Optional[str] = None
):
    logger.info("send_interview_cancel_email_started", interview_id=interview_id)
    
    subject = f"Interview Cancelled: {job_title} - {candidate_name}"
    
    body = f"Hello,\n\nThe following interview has been cancelled:\n\n"
    body += f"Candidate: {candidate_name}\n"
    body += f"Interviewer: {interviewer_name}\n"
    body += f"Position: {job_title}\n"
    body += f"Original Time: {scheduled_at}\n\n"
    body += "Best regards,\nTalentLens Team"
    
    to_emails = [email for email in [candidate_email, interviewer_email] if email]
    _send_email(subject, body, to_emails)

    if candidate_id:
        import asyncio
        from app.core.database import AsyncSessionLocal, engine
        from app.models.support import Notification
        
        async def _insert_notification():
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
            from sqlalchemy.pool import NullPool
            from app.core.config import settings
            engine_local = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
            async_session = async_sessionmaker(engine_local, expire_on_commit=False)
            
            try:
                async with async_session() as db:
                    notif = Notification(
                        recipient_type="candidate",
                        recipient_id=candidate_id,
                        type="interview_cancel",
                        channel="email",
                        payload={"interview_id": interview_id, "job_title": job_title, "scheduled_at": scheduled_at}
                    )
                    db.add(notif)
                    await db.commit()
            finally:
                await engine_local.dispose()
            
        asyncio.run(_insert_notification())
