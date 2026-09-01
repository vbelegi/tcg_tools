"""SMTP email backend (Hostinger and other providers)."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import Settings


class SmtpEmailBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

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
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        host = self._settings.smtp_host or ""
        port = self._settings.smtp_port or 465
        user = self._settings.smtp_user or ""
        password = self._settings.smtp_password or ""
        use_tls = self._settings.smtp_tls

        if use_tls and port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.sendmail(from_addr, [to], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                if use_tls:
                    smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.sendmail(from_addr, [to], msg.as_string())
