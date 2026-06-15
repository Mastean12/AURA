import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_user:
        logger.info("SMTP not configured — would send email to %s (subject: %s)", to_email, subject)
        logger.info("--- EMAIL PREVIEW ---\nTo: %s\nSubject: %s\nBody:\n%s\n--- END PREVIEW ---", to_email, subject, html_body)
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


async def send_workspace_invite(
    to_email: str, inviter_name: str, workspace_name: str,
    role: str, organization_name: str, login_url: str
) -> bool:
    subject = f"Invitation to join {workspace_name} on AURA Enterprise Intelligence"

    role_display = role.replace("_", " ").title()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background-color:#f4f5f7;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
        <tr><td align="center">
          <table width="480" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(135deg,#1e3a5f,#2563eb);padding:32px 40px;text-align:center;">
                <p style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:24px;font-weight:700;color:#ffffff;margin:0;">
                  <span style="color:#93c5fd;">AURA</span>
                  <span style="font-weight:400;color:#bfdbfe;font-size:16px;margin-left:8px;">Enterprise Intelligence</span>
                </p>
              </td>
            </tr>
            <!-- Body -->
            <tr>
              <td style="padding:40px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
                <p style="font-size:16px;color:#1f2937;margin:0 0 20px 0;">
                  Hi {to_email.split('@')[0].title()},
                </p>

                <p style="font-size:14px;color:#4b5563;line-height:1.7;margin:0 0 16px 0;">
                  <strong style="color:#1f2937;">{inviter_name}</strong> has invited you to join the workspace
                  <strong style="color:#2563eb;">{workspace_name}</strong>
                  within <strong>{organization_name}</strong> on AURA Enterprise Intelligence.
                </p>

                <p style="font-size:14px;color:#4b5563;line-height:1.7;margin:0 0 16px 0;">
                  You have been assigned the role of <strong>{role_display}</strong>.
                  This role determines what you can access and manage within the workspace.
                </p>

                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f5ff;border-radius:8px;margin:24px 0;">
                  <tr><td style="padding:20px;">
                    <p style="font-size:12px;color:#6b7280;margin:0 0 4px 0;text-transform:uppercase;letter-spacing:0.5px;">Invitation Details</p>
                    <table cellpadding="0" cellspacing="0" style="font-size:13px;color:#4b5563;">
                      <tr><td style="padding:4px 12px 4px 0;color:#9ca3af;">Organization</td><td>{organization_name}</td></tr>
                      <tr><td style="padding:4px 12px 4px 0;color:#9ca3af;">Workspace</td><td>{workspace_name}</td></tr>
                      <tr><td style="padding:4px 12px 4px 0;color:#9ca3af;">Your Role</td><td>{role_display}</td></tr>
                      <tr><td style="padding:4px 12px 4px 0;color:#9ca3af;">Invited By</td><td>{inviter_name}</td></tr>
                    </table>
                  </td></tr>
                </table>

                <div style="text-align:center;margin:32px 0;">
                  <a href="{login_url}"
                     style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;
                            padding:14px 32px;border-radius:8px;font-size:14px;font-weight:600;
                            font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
                    Sign In to AURA
                  </a>
                </div>

                <p style="font-size:13px;color:#6b7280;line-height:1.6;margin:0 0 8px 0;">
                  AURA is an AI-powered Enterprise Intelligence Platform that transforms documents,
                  reports, and data into executive-ready insights, forecasts, and board-level reports.
                </p>

                <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">

                <p style="font-size:12px;color:#9ca3af;line-height:1.5;margin:0;">
                  If you did not expect this invitation, you can ignore this email.
                  If you have questions, please contact the person who invited you.
                </p>
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
                <p style="font-size:11px;color:#9ca3af;margin:0;">
                  AURA Enterprise Intelligence Platform &bull; AI-Powered Decision Support
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    return await send_email(to_email, subject, html)
