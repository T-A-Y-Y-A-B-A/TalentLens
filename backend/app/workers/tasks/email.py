import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import structlog

from app.workers.celery_app import celery_app
from app.core.config import settings

logger = structlog.get_logger()

@celery_app.task(name="send_invite_email")
def send_invite_email(invite_id: str, to_email: str, invite_url: str):
    logger.info("sending_invite_email_started", invite_id=invite_id, to_email=to_email)
    
    subject = "You've been invited to join TalentLens"
    body = f"""
    Hello,
    
    You have been invited to join your organization on TalentLens.
    
    Click the link below to accept your invitation and set up your account:
    {invite_url}
    
    This link will expire in 7 days.
    """
    
    if getattr(settings, "EMAIL_BACKEND", "console").lower() == "smtp":
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
            server.send_message(msg)
            server.quit()
            logger.info("invite_email_sent_smtp", invite_id=invite_id, to_email=to_email)
        except Exception as e:
            logger.error("invite_email_smtp_failed", invite_id=invite_id, to_email=to_email, error=str(e))
    else:
        # Fallback to console logging
        logger.info(
            "invite_email_simulated", 
            invite_id=invite_id, 
            to_email=to_email, 
            subject=subject,
            body=body
        )
