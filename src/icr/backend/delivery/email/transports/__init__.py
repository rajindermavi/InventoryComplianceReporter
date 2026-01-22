"""Transport implementations for email delivery."""

from .base import EmailTransport, TransportResult
from .smtp import SmtpConfig, SmtpTransport

__all__ = ["EmailTransport", "TransportResult", "SmtpConfig", "SmtpTransport"]
