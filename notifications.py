import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.sms_providers import send_sms_via_provider
from app.auth_utils import validate_email_format


def _send_email(to_email: str, subject: str, body_text: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user).strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "1") != "0"

    if not smtp_host or not smtp_from:
        return False

    message = MIMEMultipart()
    message["From"] = smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body_text, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [to_email], message.as_string())
        return True
    except Exception as exc:
        print(f"Email send failed: {exc}")
        return False


def _send_sms(phone_number: str, message: str) -> bool:
    preferred_provider = os.getenv("SMS_PREFERRED_PROVIDER", "Mock")
    try:
        result = send_sms_via_provider(phone_number, message, preferred_provider)
        return bool(result.get("success"))
    except Exception as exc:
        print(f"SMS send failed: {exc}")
        return False


def send_password_reset_message(contact: str, reset_link: str) -> bool:
    """Send password reset link using contact channel (email or SMS)."""
    if validate_email_format(contact):
        subject = "Market Pulse Password Reset"
        body = (
            "You requested a password reset for Market Pulse.\n\n"
            f"Reset your password using this secure link:\n{reset_link}\n\n"
            "This link expires in 1 hour. If you did not request this reset, ignore this message."
        )
        return _send_email(contact, subject, body)

    sms_message = (
        "Market Pulse password reset requested. "
        f"Use this link within 1 hour: {reset_link}"
    )
    return _send_sms(contact, sms_message)
