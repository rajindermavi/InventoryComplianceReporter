"""Database lifecycle management for per-run SQLite persistence.

This module is responsible for initializing a run-scoped database using the
path provided by Phase 2A runtime paths. It guarantees schema-first setup,
WAL mode activation, and append-only enforcement for raw and validation data.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


class RuntimePathsLike(Protocol):
    """Minimum runtime path contract required for database initialization."""

    run_id: str
    db_path: Path


@dataclass(frozen=True)
class RunMetadata:
    """Required run metadata recorded immediately after schema initialization."""

    run_id: str
    app_version: str
    git_commit: str
    build_date: str
    input_fingerprint: str
    created_at: str | None = None


SCHEMA_SQL = """
CREATE TABLE metadata (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    app_version TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    build_date TEXT NOT NULL,
    input_fingerprint TEXT NOT NULL
);

CREATE TABLE raw_excel_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_number INTEGER NOT NULL,
    row_json TEXT NOT NULL
);

CREATE TABLE validation_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_number INTEGER,
    column_name TEXT,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL
);

CREATE TRIGGER raw_excel_rows_no_update
BEFORE UPDATE ON raw_excel_rows
BEGIN
    SELECT RAISE(ABORT, 'raw_excel_rows is append-only');
END;

CREATE TRIGGER raw_excel_rows_no_delete
BEFORE DELETE ON raw_excel_rows
BEGIN
    SELECT RAISE(ABORT, 'raw_excel_rows is append-only');
END;

CREATE TRIGGER validation_errors_no_update
BEFORE UPDATE ON validation_errors
BEGIN
    SELECT RAISE(ABORT, 'validation_errors is append-only');
END;

CREATE TRIGGER validation_errors_no_delete
BEFORE DELETE ON validation_errors
BEGIN
    SELECT RAISE(ABORT, 'validation_errors is append-only');
END;
"""


class Database:
    """Run-scoped database wrapper with explicit connection management."""

    def __init__(self, paths: RuntimePathsLike) -> None:
        """Store the run-scoped database path; no connections are cached."""

        self._db_path = paths.db_path
        self._run_id = paths.run_id

    @property
    def db_path(self) -> Path:
        """Return the database path provided by runtime paths."""

        return self._db_path

    def connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection to the run database."""

        return sqlite3.connect(self._db_path)

    def initialize(self, metadata: RunMetadata) -> None:
        """Create the database, initialize schema, and insert run metadata.

        Schema creation and metadata insertion are performed atomically. WAL
        mode is enabled once during initialization. The database file must not
        already exist for the current run.
        """

        if metadata.run_id != self._run_id:
            raise ValueError("Run metadata run_id must match runtime paths run_id.")

        if self._db_path.exists():
            raise FileExistsError(f"Run database already exists: {self._db_path}")

        conn = sqlite3.connect(self._db_path)
        try:
            self._enable_wal(conn)
            with conn:
                conn.executescript(SCHEMA_SQL)
                self._insert_metadata(conn, metadata)
        finally:
            conn.close()

    @staticmethod
    def _enable_wal(conn: sqlite3.Connection) -> None:
        """Enable SQLite WAL mode for the connection."""

        result = conn.execute("PRAGMA journal_mode=WAL;").fetchone()
        if not result or str(result[0]).lower() != "wal":
            raise RuntimeError("Failed to enable SQLite WAL mode.")

    @staticmethod
    def _insert_metadata(conn: sqlite3.Connection, metadata: RunMetadata) -> None:
        """Insert the run metadata row into the metadata table."""

        created_at = metadata.created_at or _utc_now_iso()
        conn.execute(
            """
            INSERT INTO metadata (
                run_id,
                created_at,
                app_version,
                git_commit,
                build_date,
                input_fingerprint
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                metadata.run_id,
                created_at,
                metadata.app_version,
                metadata.git_commit,
                metadata.build_date,
                metadata.input_fingerprint,
            ),
        )


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing 'Z'."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
