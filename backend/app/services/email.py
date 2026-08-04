from celery import Celery
import smtplib
from email.message import EmailMessage

from app.core.config import settings

celery_app = Celery(
    "email_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

def _send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = "noreply@talentlens.local"
    msg['To'] = to_email

    # Connect to local Mailpit (assuming it's on localhost:1025)
    # In production, this would be configured via env vars
    try:
        with smtplib.SMTP("localhost", 1025) as server:
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

@celery_app.task
def send_verification_email(email: str, token: str):
    subject = "Verify your TalentLens account"
    # FRONTEND_URL from settings
    url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    body = f"Please verify your email by clicking the following link:\n{url}"
    _send_email(email, subject, body)

@celery_app.task
def send_password_reset_email(email: str, token: str):
    subject = "Reset your TalentLens password"
    url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = f"You requested a password reset. Click the following link:\n{url}"
    _send_email(email, subject, body)
