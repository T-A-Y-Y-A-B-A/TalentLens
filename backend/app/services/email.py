from celery import Celery
import httpx

from app.core.config import settings

celery_app = Celery(
    "email_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

def _send_email(to_email: str, subject: str, body: str):
    if not settings.BREVO_API_KEY:
        print(f"BREVO_API_KEY is not set. Would have sent: {subject} to {to_email}")
        return

    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "sender": {"email": settings.SMTP_USER, "name": "TalentLens"},
            "to": [{"email": to_email}],
            "subject": subject,
            # Simple wrapper to make the plaintext body look okay in HTML
            "htmlContent": f"<p>{body.replace(chr(10), '<br>')}</p>"
        }
        
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        response.raise_for_status()
        print(f"Successfully sent email to {to_email}. Brevo response: {response.text}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

@celery_app.task
def send_verification_email(email: str, token: str):
    subject = "Verify your TalentLens account"
    url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    body = f"Please verify your email by clicking the following link:\n{url}"
    _send_email(email, subject, body)

@celery_app.task
def send_password_reset_email(email: str, token: str):
    subject = "Reset your TalentLens password"
    url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = f"You requested a password reset. Click the following link:\n{url}"
    _send_email(email, subject, body)
