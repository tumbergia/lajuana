from __future__ import annotations

import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.common.enums import NotificationChannel
from app.core.config import settings
from app.core.logging import logger
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.notifications.provider import NotificationProvider, SendResult

_SERVICE_DEFAULTS: dict[str, tuple[str, int]] = {
    "gmail": ("smtp.gmail.com", 587),
    "outlook": ("smtp.office365.com", 587),
    "yahoo": ("smtp.mail.yahoo.com", 587),
}


def _resolve_smtp_config() -> tuple[str, int]:
    if settings.email_host and settings.email_port:
        return settings.email_host, settings.email_port
    defaults = _SERVICE_DEFAULTS.get(settings.email_service.lower())
    if defaults:
        return defaults
    logger.warning(
        "[email] Unknown email_service=%s, falling back to Gmail defaults",
        settings.email_service,
    )
    return ("smtp.gmail.com", 587)


def _html_to_plain(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


class EmailProvider(NotificationProvider):
    channel = NotificationChannel.EMAIL

    async def send(self, entry: NotificationOutboxDocument) -> SendResult:
        import aiosmtplib

        if not settings.email_user or not settings.email_pass:
            return SendResult(
                success=False,
                error_code="missing_credentials",
                error_detail="Email SMTP credentials not configured.",
            )

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
        msg["To"] = entry.recipient_identifier
        msg["Subject"] = entry.subject or "Notificación La Juana"

        plain_body = _html_to_plain(entry.rendered_body or "")
        plain_part = MIMEText(plain_body, "plain", "utf-8")
        html_part = MIMEText(entry.rendered_body or "", "html", "utf-8")
        msg.attach(plain_part)
        msg.attach(html_part)

        host, port = _resolve_smtp_config()

        try:
            async with aiosmtplib.SMTP(
                hostname=host,
                port=port,
                timeout=30,
                start_tls=False,
            ) as smtp:
                await smtp.starttls()
                await smtp.login(settings.email_user, settings.email_pass)
                await smtp.send_message(msg)

            logger.info(
                "[email] Sent | to=%s | outbox_id=%s | service=%s",
                entry.recipient_identifier,
                str(entry.id),
                settings.email_service,
            )
            return SendResult(success=True, provider_message_id=str(entry.id))
        except Exception as exc:
            logger.error(
                "[email] Send failed | to=%s | error=%s",
                entry.recipient_identifier,
                exc,
            )
            return SendResult(
                success=False,
                error_code="send_failed",
                error_detail=str(exc),
            )

    async def validate_config(self) -> bool:
        if not settings.email_user or not settings.email_pass:
            return False

        try:
            import aiosmtplib  # type: ignore[import-unused]
        except ImportError:
            return False

        host, port = _resolve_smtp_config()
        try:
            async with aiosmtplib.SMTP(
                hostname=host,
                port=port,
                timeout=10,
                start_tls=False,
            ) as smtp:
                await smtp.starttls()
                await smtp.login(settings.email_user, settings.email_pass)
            return True
        except Exception:
            return False
