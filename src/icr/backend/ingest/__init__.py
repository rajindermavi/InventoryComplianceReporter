"""Ingestion package."""

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
