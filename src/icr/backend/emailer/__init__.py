"""Emailer package.
- Email recipient resolution
- Subject and body templating
- HTML report embedding
- Optional `.eml` draft file generation
- Run summary updates related to email drafting
"""

from .draft import (
    DEFAULT_SUBJECT_TEMPLATE,
    EMAIL_PHASE,
    DraftAttachment,
    DraftEmail,
    DraftIssue,
    DraftingResult,
    draft_emails,
)

__all__ = [
    "DEFAULT_SUBJECT_TEMPLATE",
    "EMAIL_PHASE",
    "DraftAttachment",
    "DraftEmail",
    "DraftIssue",
    "DraftingResult",
    "draft_emails",
]
