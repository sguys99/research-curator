"""SMTP 재시도 로직을 포함한 이메일 발송기."""

import logging
import os
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


# SMTP 이메일 발송을 담당하는 메인 클래스
class EmailSender:
    """비동기 지원 및 재시도 로직이 포함된 SMTP 발송기."""

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
    ) -> None:
        """
        SMTP 설정으로 이메일 발송기를 초기화한다.

        Args:
            smtp_host: SMTP 서버 호스트
            smtp_port: SMTP 서버 포트
            smtp_user: SMTP 사용자명
            smtp_password: SMTP 비밀번호
            from_email: 발신 이메일 주소
            from_name: 발신자 이름
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
        self.from_name = from_name or os.getenv("SMTP_FROM_NAME", "Research Curator")

        # 설정 검증(누락 시 즉시 오류)
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            raise ValueError("SMTP configuration is incomplete. Check environment variables.")

    @retry(
        stop=stop_after_attempt(3),  # 최대 3회 시도
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 2, 4, 8초 대기
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
        재시도 로직을 포함해 단일 이메일을 발송한다.

        Args:
            to_email: 수신자 이메일 주소
            subject: 이메일 제목
            html_content: HTML 본문
            text_content: 일반 텍스트 본문(선택)

        Returns:
            bool: 발송 성공 여부

        Raises:
            aiosmtplib.SMTPException: 재시도 후에도 발송 실패한 경우
        """
        try:
            # 메시지 생성
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            # 텍스트 파트 추가(폴백)
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)

            # HTML 파트 추가
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # SMTP 전송
            tls_context = ssl.create_default_context()
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
                tls_context=tls_context,
                validate_certs=True,
                timeout=30,
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
        다수 수신자에게 이메일을 발송한다.

        Args:
            recipients: to_email, subject, html_content, text_content 키가 있는 목록
            max_failures: 중단 전 허용 실패 횟수

        Returns:
            dict: 성공/실패 개수와 실패 목록 요약
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


# 빠른 이메일 발송용 편의 함수
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """
    기본 SMTP 설정으로 단일 이메일을 발송한다.

    Args:
        to_email: 수신자 이메일 주소
        subject: 이메일 제목
        html_content: HTML 본문
        text_content: 일반 텍스트 본문(선택)

    Returns:
        bool: 발송 성공 여부
    """
    sender = EmailSender()
    return await sender.send_email(to_email, subject, html_content, text_content)


async def send_batch_emails(recipients: list[dict[str, Any]]) -> dict[str, Any]:
    """
    기본 SMTP 설정으로 다수 수신자에게 이메일을 발송한다.

    Args:
        recipients: to_email, subject, html_content, text_content 키가 있는 목록

    Returns:
        dict: 성공/실패 개수와 실패 목록 요약
    """
    sender = EmailSender()
    return await sender.send_batch_emails(recipients)
