"""Tests for email sender functionality."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from aiosmtplib import SMTPException

from app.email.sender import EmailSender, send_batch_emails, send_email


class TestEmailSender:
    """Test cases for EmailSender class."""

    def test_init_with_env_vars(self):
        """Test EmailSender initialization with environment variables."""
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "test@example.com",
                "SMTP_PASSWORD": "test_password",
                "SMTP_FROM_EMAIL": "noreply@example.com",
                "SMTP_FROM_NAME": "Test Service",
            },
        ):
            sender = EmailSender()
            assert sender.smtp_host == "smtp.example.com"
            assert sender.smtp_port == 587
            assert sender.smtp_user == "test@example.com"
            assert sender.smtp_password == "test_password"
            assert sender.from_email == "noreply@example.com"
            assert sender.from_name == "Test Service"

    def test_init_with_params(self):
        """Test EmailSender initialization with parameters."""
        sender = EmailSender(
            smtp_host="custom.smtp.com",
            smtp_port=465,
            smtp_user="custom@example.com",
            smtp_password="custom_pass",
            from_email="from@example.com",
            from_name="Custom Name",
        )
        assert sender.smtp_host == "custom.smtp.com"
        assert sender.smtp_port == 465
        assert sender.smtp_user == "custom@example.com"
        assert sender.smtp_password == "custom_pass"
        assert sender.from_email == "from@example.com"
        assert sender.from_name == "Custom Name"

    def test_init_incomplete_config(self):
        """Test EmailSender initialization with incomplete config."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SMTP configuration is incomplete"):
                EmailSender()

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending."""
        sender = EmailSender(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
        )

        with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None

            result = await sender.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<h1>Test Email</h1>",
                text_content="Test Email",
            )

            assert result is True
            assert mock_send.called
            assert mock_send.call_count == 1

            # Verify call arguments
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["hostname"] == "smtp.test.com"
            assert call_kwargs["port"] == 587
            assert call_kwargs["username"] == "test@test.com"
            assert call_kwargs["password"] == "password"
            assert call_kwargs["start_tls"] is True

    @pytest.mark.asyncio
    async def test_send_email_failure(self):
        """Test email sending failure."""
        sender = EmailSender(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
        )

        with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = SMTPException("Connection failed")

            with pytest.raises(SMTPException):
                await sender.send_email(
                    to_email="recipient@example.com",
                    subject="Test Subject",
                    html_content="<h1>Test Email</h1>",
                )

    @pytest.mark.asyncio
    async def test_send_email_retry(self):
        """Test email sending with retry logic."""
        sender = EmailSender(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
        )

        with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            # Fail twice, then succeed
            mock_send.side_effect = [
                SMTPException("Temporary failure"),
                SMTPException("Temporary failure"),
                None,
            ]

            result = await sender.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<h1>Test Email</h1>",
            )

            assert result is True
            assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_send_batch_emails_success(self):
        """Test successful batch email sending."""
        sender = EmailSender(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
        )

        recipients = [
            {
                "to_email": f"user{i}@example.com",
                "subject": f"Test {i}",
                "html_content": f"<h1>Email {i}</h1>",
            }
            for i in range(3)
        ]

        with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None

            result = await sender.send_batch_emails(recipients)

            assert result["success_count"] == 3
            assert result["failure_count"] == 0
            assert len(result["failed_emails"]) == 0
            assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_send_batch_emails_partial_failure(self):
        """Test batch email sending with some failures."""
        sender = EmailSender(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
        )

        recipients = [
            {
                "to_email": f"user{i}@example.com",
                "subject": f"Test {i}",
                "html_content": f"<h1>Email {i}</h1>",
            }
            for i in range(5)
        ]

        call_count = 0

        async def mock_send_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail on specific attempts (accounting for retries)
            # user0: success (1 call)
            # user1: fail 3 times (calls 2,3,4)
            # user2: success (call 5)
            # user3: fail 3 times (calls 6,7,8)
            # user4: success (call 9)
            if call_count in [2, 3, 4, 6, 7, 8]:
                raise SMTPException("Failed")
            return None

        with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = mock_send_side_effect

            result = await sender.send_batch_emails(recipients)

            assert result["success_count"] == 3
            assert result["failure_count"] == 2
            assert len(result["failed_emails"]) == 2
            # Check that user1 and user3 failed
            failed_addresses = [f["email"] for f in result["failed_emails"]]
            assert "user1@example.com" in failed_addresses
            assert "user3@example.com" in failed_addresses

    @pytest.mark.asyncio
    async def test_send_batch_emails_max_failures(self):
        """Test batch email sending stops after max failures."""
        sender = EmailSender(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
        )

        recipients = [
            {
                "to_email": f"user{i}@example.com",
                "subject": f"Test {i}",
                "html_content": f"<h1>Email {i}</h1>",
            }
            for i in range(10)
        ]

        with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            # All emails fail (even after retries)
            mock_send.side_effect = SMTPException("All failed")

            result = await sender.send_batch_emails(recipients, max_failures=3)

            # Should stop after 3 failures
            assert result["success_count"] == 0
            assert result["failure_count"] == 3
            assert len(result["failed_emails"]) == 3
            # With retry logic (3 attempts per email), total calls should be 9 (3 emails × 3 retries)
            assert mock_send.call_count == 9

    @pytest.mark.asyncio
    async def test_convenience_send_email(self):
        """Test convenience send_email function."""
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.test.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "test@test.com",
                "SMTP_PASSWORD": "password",
            },
        ):
            with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = None

                result = await send_email(
                    to_email="recipient@example.com",
                    subject="Test",
                    html_content="<h1>Test</h1>",
                )

                assert result is True
                assert mock_send.called

    @pytest.mark.asyncio
    async def test_convenience_send_batch_emails(self):
        """Test convenience send_batch_emails function."""
        recipients = [
            {
                "to_email": "user1@example.com",
                "subject": "Test 1",
                "html_content": "<h1>Test 1</h1>",
            },
            {
                "to_email": "user2@example.com",
                "subject": "Test 2",
                "html_content": "<h1>Test 2</h1>",
            },
        ]

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.test.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "test@test.com",
                "SMTP_PASSWORD": "password",
            },
        ):
            with patch("app.email.sender.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = None

                result = await send_batch_emails(recipients)

                assert result["success_count"] == 2
                assert result["failure_count"] == 0
                assert mock_send.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
