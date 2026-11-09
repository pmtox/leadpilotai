"""SMTP email delivery for customer call summaries."""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Dict, Optional

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    @property
    def is_configured(self) -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)

    def send_email(
        self,
        recipient: Optional[str],
        subject: str,
        body: str,
        consent_confirmed: bool = False,
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "draft",
            "message": "",
            "recipient": recipient,
            "subject": subject,
            "draft_text": body,
        }
        if not consent_confirmed:
            result["message"] = "Operator confirmation is required; email remains a draft."
            return result
        if not recipient:
            result["message"] = "Customer email address is missing; email remains a draft."
            return result
        if not self.is_configured:
            result["message"] = "SMTP is not configured; email remains a draft."
            return result

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = recipient
        message.set_content(body)

        stage = "connecting to the SMTP server"
        try:
            if settings.SMTP_PORT == 465:
                smtp_connection = smtplib.SMTP_SSL(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=20,
                    context=ssl.create_default_context(),
                )
            else:
                smtp_connection = smtplib.SMTP(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=20,
                )

            with smtp_connection as smtp:
                if settings.SMTP_PORT != 465:
                    stage = "starting TLS encryption"
                    smtp.ehlo()
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                if settings.SMTP_USERNAME:
                    stage = "authenticating with the SMTP server"
                    username = settings.SMTP_USERNAME.strip()
                    password = "".join(settings.SMTP_PASSWORD.split())
                    smtp.login(username, password)
                stage = "sending the message"
                smtp.send_message(message)
        except smtplib.SMTPServerDisconnected as exc:
            logger.warning("SMTP server disconnected while %s", stage)
            if stage == "authenticating with the SMTP server":
                detail = (
                    "SMTP server closed the connection during authentication. "
                    "For Gmail, verify the full Gmail address and use a current "
                    "Google App Password without spaces; then restart the backend."
                )
            elif stage == "sending the message":
                detail = (
                    "SMTP server closed the connection while sending. Verify the "
                    "sender address and that the SMTP account is permitted to send."
                )
            else:
                detail = (
                    f"SMTP server closed the connection while {stage}. "
                    "Verify the SMTP host, port, and TLS settings."
                )
            result.update(status="failed", message=f"Email delivery failed: {detail}")
            return result
        except (OSError, smtplib.SMTPException) as exc:
            logger.warning("SMTP delivery failed while %s: %s", stage, exc)
            result.update(
                status="failed",
                message=f"Email delivery failed while {stage}: {exc}",
            )
            return result

        result.update(status="sent", message="Email sent successfully.", draft_text=None)
        return result


email_service = EmailService()
