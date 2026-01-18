"""Tests for database lifecycle, schema initialization, and connections."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path

import pytest

from icr.backend.persistence import paths as paths_mod
from icr.backend.persistence.db import Database, RunMetadata


@dataclass(frozen=True)
class DbRuntimePaths:
    """Runtime paths wrapper providing the database path."""

    run_id: str
    db_path: Path


@pytest.fixture()
def runtime_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> paths_mod.RuntimePaths:
    """Provide temporary Phase 2A runtime paths for tests."""

    monkeypatch.setattr(paths_mod, "_resolve_user_data_base", lambda: tmp_path)
    return paths_mod.RuntimePaths.create()


@pytest.fixture()
def db_paths(runtime_paths: paths_mod.RuntimePaths) -> DbRuntimePaths:
    """Provide a runtime paths object with the derived database path."""

    db_path = runtime_paths.data_dir / "run.sqlite"
    return DbRuntimePaths(run_id=runtime_paths.run_id, db_path=db_path)


def _make_metadata(run_id: str) -> RunMetadata:
    return RunMetadata(
        run_id=run_id,
        app_version="1.2.3",
        git_commit="deadbeef",
        build_date="2024-01-01",
        input_fingerprint="abc123",
    )


def test_database_file_created(db_paths: DbRuntimePaths) -> None:
    db = Database(db_paths)

    db.initialize(_make_metadata(db_paths.run_id))

    assert db.db_path.exists()
    assert db.db_path.is_file()


def test_schema_tables_exist(db_paths: DbRuntimePaths) -> None:
    db = Database(db_paths)
    db.initialize(_make_metadata(db_paths.run_id))

    with db.connect() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
    table_names = {row[0] for row in tables}

    assert {"metadata", "raw_excel_rows", "validation_errors"} <= table_names


def test_metadata_row_inserted(db_paths: DbRuntimePaths) -> None:
    db = Database(db_paths)
    db.initialize(_make_metadata(db_paths.run_id))

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM metadata;").fetchone()

    assert row is not None
    required_fields = {"run_id", "created_at", "app_version", "git_commit", "build_date"}
    assert required_fields <= set(row.keys())
    assert row["run_id"] == db_paths.run_id
    assert row["created_at"]


def test_journal_mode_is_wal(db_paths: DbRuntimePaths) -> None:
    db = Database(db_paths)
    db.initialize(_make_metadata(db_paths.run_id))

    with db.connect() as conn:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]

    assert str(journal_mode).lower() == "wal"


def test_connect_returns_new_connections(db_paths: DbRuntimePaths) -> None:
    db = Database(db_paths)
    db.initialize(_make_metadata(db_paths.run_id))

    conn_one = db.connect()
    conn_two = db.connect()

    try:
        assert conn_one is not conn_two
        assert conn_one.execute("SELECT 1;").fetchone()[0] == 1
        assert conn_two.execute("SELECT 1;").fetchone()[0] == 1
    finally:
        conn_one.close()
        conn_two.close()

    with db.connect() as conn:
        assert conn.execute("SELECT 1;").fetchone()[0] == 1
