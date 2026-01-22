"""Emailer package."""

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
