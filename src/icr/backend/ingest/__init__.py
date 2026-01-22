"""Ingestion package.
- Deterministic ingestion of Excel input
- Early normalization and validation of data
- Faithful preservation of raw input
- Clear, actionable validation warnings and errors
- User-controlled continuation when recoverable issues are present
"""

from .excel_reader import (
    DatabaseLike,
    IngestionFatalError,
    IngestionStats,
    IngestionSummary,
    RuntimePathsLike,
    SheetSpec,
    ValidationIssue,
    ingest_excel_files,
)

__all__ = [
    "DatabaseLike",
    "RuntimePathsLike",
    "ValidationIssue",
    "IngestionFatalError",
    "IngestionStats",
    "IngestionSummary",
    "SheetSpec",
    "ingest_excel_files",
]
