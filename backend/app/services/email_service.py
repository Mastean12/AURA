import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_user:
        logger.info("SMTP not configured — skipping email to %s (subject: %s)", to_email, subject)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body.replace("<br>", "\n"), "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())

        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception as e:
        logger.warning("Failed to send email to %s: %s", to_email, e)
        return False


async def send_workspace_invite(to_email: str, inviter_name: str, workspace_name: str, login_url: str) -> bool:
    subject = f"You've been invited to {workspace_name} on AURA"
    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 20px; font-weight: 600; color: #2563eb;">AURA</span>
        <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">Enterprise Intelligence</span>
      </div>
      <h2 style="font-size: 18px; color: #111827; margin-bottom: 12px;">You've been invited</h2>
      <p style="font-size: 14px; color: #4b5563; line-height: 1.6;">
        <strong>{inviter_name}</strong> has invited you to join the workspace
        <strong>{workspace_name}</strong> on AURA.
      </p>
      <p style="font-size: 14px; color: #4b5563; line-height: 1.6;">
        Click the button below to sign in and access the workspace.
      </p>
      <div style="margin: 24px 0;">
        <a href="{login_url}" style="display: inline-block; background: #2563eb; color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 500;">
          Sign in to AURA
        </a>
      </div>
      <p style="font-size: 12px; color: #9ca3af; margin-top: 32px;">
        If you didn't expect this invitation, you can ignore this email.
      </p>
    </div>
    """
    return await send_email(to_email, subject, html)
