"""Email sender using SMTP with retry logic."""

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EmailSender:
    """SMTP email sender with async support and retry logic."""

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
    ):
        """
        Initialize email sender with SMTP configuration.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            from_name: Sender name
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
        self.from_name = from_name or os.getenv("SMTP_FROM_NAME", "Research Curator")

        # Validate configuration
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            raise ValueError("SMTP configuration is incomplete. Check environment variables.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """
        Send a single email with retry logic.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)

        Returns:
            bool: True if email was sent successfully

        Raises:
            aiosmtplib.SMTPException: If sending fails after retries
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Add text part (fallback)
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except aiosmtplib.SMTPException as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            raise

    async def send_batch_emails(
        self,
        recipients: list[dict[str, Any]],
        max_failures: int = 5,
    ) -> dict[str, Any]:
        """
        Send emails to multiple recipients.

        Args:
            recipients: List of dicts with keys: to_email, subject, html_content, text_content
            max_failures: Maximum number of failures before stopping

        Returns:
            dict: Summary with success_count, failure_count, failed_emails
        """
        success_count = 0
        failure_count = 0
        failed_emails = []

        for recipient in recipients:
            if failure_count >= max_failures:
                logger.warning(f"Stopping batch send: reached max failures ({max_failures})")
                break

            try:
                await self.send_email(
                    to_email=recipient["to_email"],
                    subject=recipient["subject"],
                    html_content=recipient["html_content"],
                    text_content=recipient.get("text_content"),
                )
                success_count += 1
            except Exception as e:
                failure_count += 1
                failed_emails.append({"email": recipient["to_email"], "error": str(e)})
                logger.error(f"Failed to send to {recipient['to_email']}: {e}")

        logger.info(f"Batch send complete: {success_count} succeeded, {failure_count} failed")

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "failed_emails": failed_emails,
        }


# Convenience function for quick email sending
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """
    Send a single email using default SMTP configuration.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)

    Returns:
        bool: True if email was sent successfully
    """
    sender = EmailSender()
    return await sender.send_email(to_email, subject, html_content, text_content)


async def send_batch_emails(recipients: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Send emails to multiple recipients using default SMTP configuration.

    Args:
        recipients: List of dicts with keys: to_email, subject, html_content, text_content

    Returns:
        dict: Summary with success_count, failure_count, failed_emails
    """
    sender = EmailSender()
    return await sender.send_batch_emails(recipients)
