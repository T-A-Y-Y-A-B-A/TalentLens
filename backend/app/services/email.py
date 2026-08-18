from celery import Celery
import httpx
from datetime import datetime

from app.core.config import settings

celery_app = Celery(
    "email_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

def get_html_template(title: str, content: str, action_url: str, action_text: str) -> str:
    year = datetime.now().year
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 40px; margin-bottom: 40px;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; border-radius: 12px; border: 1px solid #e4e4e7; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                        <tr>
                            <td align="center" style="padding: 40px 0; background-color: #4f46e5;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">TalentLens</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 48px;">
                                <h2 style="color: #18181b; font-size: 20px; font-weight: 600; margin-top: 0; margin-bottom: 24px;">{title}</h2>
                                <p style="color: #52525b; font-size: 16px; line-height: 1.6; margin-top: 0; margin-bottom: 32px;">
                                    {content}
                                </p>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td align="center">
                                            <a href="{action_url}" style="display: inline-block; background-color: #4f46e5; color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; padding: 14px 32px; border-radius: 8px;">
                                                {action_text}
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #71717a; font-size: 14px; line-height: 1.5; margin-top: 40px; margin-bottom: 0;">
                                    If you didn't request this email, you can safely ignore it.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding: 24px; background-color: #fafafa; border-top: 1px solid #e4e4e7;">
                                <p style="color: #a1a1aa; font-size: 13px; margin: 0;">
                                    &copy; {year} TalentLens Inc. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def _send_email(to_email: str, subject: str, html_body: str):
    try:
        # Private Google Apps Script Webhook
        url = "https://script.google.com/macros/s/AKfycbz3xI3lvt1v6jimMY080Gu5DQ8ALShXElYgUjVBGvgvgslOxQY4FNfzrPLjIu-imwr4/exec"
        payload = {
            "to": to_email,
            "subject": subject,
            "htmlBody": html_body
        }
        
        # Google Apps Script returns a 302 redirect on POST, so follow_redirects=True is required
        response = httpx.post(url, json=payload, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        print(f"Successfully sent email to {to_email} via Google Apps Script. Response: {response.text}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

@celery_app.task
def send_verification_email(email: str, token: str):
    subject = "Welcome to TalentLens - Verify your email"
    url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = get_html_template(
        title="Verify your email address",
        content="Welcome to TalentLens! To get started and securely access your account, we just need to quickly verify your email address.",
        action_url=url,
        action_text="Verify Email Address"
    )
    _send_email(email, subject, html)

@celery_app.task
def send_password_reset_email(email: str, token: str):
    subject = "Reset your TalentLens password"
    url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = get_html_template(
        title="Password Reset Request",
        content="We received a request to reset the password for your TalentLens account. Click the button below to securely set a new password.",
        action_url=url,
        action_text="Reset Password"
    )
    _send_email(email, subject, html)
