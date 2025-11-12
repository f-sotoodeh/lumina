# backend/app/core/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks
from app.core.i18n import Translator
from app.core.config import settings

def _send_email_sync(to_email: str, subject: str, html_body: str):
    """Synchronous email sending function"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.EMAIL_USER
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            server.send_message(msg)
        
        print(f"[EMAIL] Successfully sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")

async def send_otp_email(background_tasks: BackgroundTasks, email: str, otp: str, lang: str = "en"):
    t = Translator.get(lang)
    
    subject = t["email"]["otp_subject"]
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #6366f1;">{t["email"]["otp_title"]}</h2>
        <p>{t["email"]["otp_body"]}</p>
        <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 32px; letter-spacing: 8px; font-weight: bold; margin: 20px 0;">
            {otp}
        </div>
        <p>{t["email"]["otp_expiry"]}</p>
        <hr>
        <small style="color: #888;">Lumina — impress editor</small>
    </div>
    """
    
    background_tasks.add_task(_send_email_sync, email, subject, html_body)
