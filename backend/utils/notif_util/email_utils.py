import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# load from env variables (.env file)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER_NAME = os.getenv("SENDER_NAME", "Smart Task Manager")

def ail(to_email: str, subject: str, body: str) -> None:
    """
    Sends an email using SMTP.

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Plain text or HTML message body
    """
    if not (SMTP_USER and SMTP_PASS):
        raise RuntimeError("SMTP credentials not configured. Please set SMTP_USER and SMTP_PASS env vars.")

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((SENDER_NAME, SMTP_USER))
        msg["To"] = to_email
        msg["Subject"] = subject

        # plain text fallback + HTML version
        text_part = MIMEText(body, "plain")
        html_part = MIMEText(f"<html><body><p>{body}</p></body></html>", "html")
        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"✅ Email sent to {to_email}")

    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        raise
