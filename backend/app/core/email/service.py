"""Email delivery abstraction."""

from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings
from app.core.email.backends.console import ConsoleEmailBackend
from app.core.email.backends.smtp import SmtpEmailBackend

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        settings = get_settings()
        if settings.use_console_email:
            self._backend = ConsoleEmailBackend()
        else:
            self._backend = SmtpEmailBackend(settings)

    def send(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        settings = get_settings()
        if not settings.email_enabled and not settings.use_console_email:
            logger.warning("Email disabled; skipping send to %s subject=%s", to, subject)
            return
        try:
            self._backend.send(
                to=to,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                from_addr=settings.resolved_email_from,
                reply_to=settings.email_reply_to,
            )
        except Exception:
            logger.exception("Failed to send email to %s subject=%s", to, subject)
            raise


@lru_cache
def get_email_service() -> EmailService:
    return EmailService()
