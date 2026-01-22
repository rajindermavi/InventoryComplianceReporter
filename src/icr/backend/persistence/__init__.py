"""Persistence subsystem.
- Windows-safe, cross-platform path resolution
- Per-user application data directory
- Self-contained per-run workspace
- Early, consistent logging destination setup
- One SQLite database per run
- Schema-first initialization
- Strong auditability and provenance
- Explicit, safe connection management
"""

from .db import Database, RunMetadata
from .paths import RuntimePaths, get_app_data_dir, get_run_dir, get_runs_base_dir

__all__ = [
    "Database",
    "RunMetadata",
    "RuntimePaths",
    "get_app_data_dir",
    "get_runs_base_dir",
    "get_run_dir",
]
