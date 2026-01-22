"""Delivery package.

Responsibilities:
- Post-report artifact handling (packaging/delivery)
- Phase 7A PDF generation
- Phase 7B delivery actions (future)
"""

from .email import EmailDeliveryPlan, EmailDeliveryResult, deliver_emails
from .pdf import PdfResult, generate_pdfs

__all__ = [
    "EmailDeliveryPlan",
    "EmailDeliveryResult",
    "PdfResult",
    "deliver_emails",
    "generate_pdfs",
]
