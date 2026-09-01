"""Log emails to stdout (development / tests)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ConsoleEmailBackend:
    def send(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None,
        from_addr: str,
        reply_to: str | None,
    ) -> None:
        logger.info(
            "EMAIL to=%s from=%s reply_to=%s subject=%s\n%s",
            to,
            from_addr,
            reply_to or "",
            subject,
            text_body,
        )
