"""Inventory Compliance Reporter package.

Exports the Phase 2 public interfaces for runtime paths, persistence, and
ingestion so callers can import from the top-level package.
"""

from __future__ import annotations

from icr.backend.ingest.excel_reader import (
    IngestionFatalError,
    IngestionStats,
    IngestionSummary,
    ValidationIssue,
    ingest_excel_files,
)
from icr.backend.persistence.db import Database, RunMetadata
from icr.backend.persistence.paths import (
    RuntimePaths,
    get_app_data_dir,
    get_run_dir,
    get_runs_base_dir,
)

__all__ = [
    "Database",
    "IngestionFatalError",
    "IngestionStats",
    "IngestionSummary",
    "RunMetadata",
    "RuntimePaths",
    "ValidationIssue",
    "get_app_data_dir",
    "get_run_dir",
    "get_runs_base_dir",
    "ingest_excel_files",
]
