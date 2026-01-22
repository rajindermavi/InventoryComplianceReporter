"""SMTP transport for Phase 7B.

This module sends pre-rendered .eml drafts as opaque bytes.
"""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from pathlib import Path

from .base import TransportResult


@dataclass(frozen=True)
class SmtpConfig:
    """SMTP configuration for sending draft emails."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None
    use_tls: bool = True
    use_ssl: bool = False
    timeout_seconds: int = 30
    envelope_from: str | None = None
    envelope_to: tuple[str, ...] = ()


class SmtpTransport:
    """SMTP transport that sends .eml files without modification."""

    name = "smtp"

    def __init__(self, config: SmtpConfig) -> None:
        self._config = config

    def send(self, eml_path: Path) -> TransportResult:
        try:
            eml_bytes = eml_path.read_bytes()
        except Exception as exc:  # noqa: BLE001
            return TransportResult(
                success=False,
                provider_message_id=None,
                error=f"{type(exc).__name__}: {exc}",
            )

        if not self._config.envelope_from:
            return TransportResult(
                success=False,
                provider_message_id=None,
                error="Missing SMTP envelope_from configuration.",
            )
        if not self._config.envelope_to:
            return TransportResult(
                success=False,
                provider_message_id=None,
                error="Missing SMTP envelope_to configuration.",
            )

        try:
            server = self._connect()
            try:
                response = server.sendmail(
                    self._config.envelope_from,
                    list(self._config.envelope_to),
                    eml_bytes,
                )
            finally:
                try:
                    server.quit()
                except Exception:
                    server.close()

            if response:
                return TransportResult(
                    success=False,
                    provider_message_id=None,
                    error=f"SMTP send errors: {response}",
                )

            return TransportResult(
                success=True,
                provider_message_id=None,
                error=None,
            )
        except Exception as exc:  # noqa: BLE001
            return TransportResult(
                success=False,
                provider_message_id=None,
                error=f"{type(exc).__name__}: {exc}",
            )

    def _connect(self) -> smtplib.SMTP:
        config = self._config
        if config.use_ssl:
            server: smtplib.SMTP = smtplib.SMTP_SSL(
                config.host,
                config.port,
                timeout=config.timeout_seconds,
            )
        else:
            server = smtplib.SMTP(
                config.host,
                config.port,
                timeout=config.timeout_seconds,
            )

        if config.use_tls and not config.use_ssl:
            server.starttls()
        if config.username:
            server.login(config.username, config.password or "")
        return server
