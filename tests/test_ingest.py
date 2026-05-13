"""Tests for Phase 2C Excel ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sqlite3

import pytest
from openpyxl import Workbook

from icr.backend.ingest.excel_reader import (
    IngestionFatalError,
    ingest_excel_files,
)
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
def db(runtime_paths: paths_mod.RuntimePaths) -> Database:
    """Create a fresh Phase 2B database for ingestion tests."""

    db_paths = DbRuntimePaths(
        run_id=runtime_paths.run_id,
        db_path=runtime_paths.data_dir / "run.sqlite",
    )
    db_instance = Database(db_paths)
    db_instance.initialize(
        RunMetadata(
            run_id=db_paths.run_id,
            app_version="1.2.3",
            git_commit="deadbeef",
            build_date="2024-01-01",
            input_fingerprint="abc123",
        )
    )
    return db_instance


def _write_workbook(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


def _write_valid_sources(tmp_path: Path) -> dict[str, Path]:
    ic_path = tmp_path / "SAFE_IC_INVENTORY.xlsx"
    vessels_index_path = tmp_path / "SAFE_VESSELS_INDEX.xlsx"
    vessels_inventory_path = tmp_path / "SAFE_VESSELS_INVENTORY.xlsx"

    _write_workbook(
        ic_path,
        ["ITEM", "ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [["ITEM1", "Desc", "PLIN", "CLS", "UPC", "ED1", date(2024, 1, 1)]],
    )
    _write_workbook(
        vessels_index_path,
        [
            "SHIPID",
            "SHIPNAME",
            "CUSTNO",
            "IMONO",
            "SHIPSTAT",
            "EMAIL",
            "NOTE1",
            "NOTE2",
            "NOTE3",
        ],
        [["S1", "Ship", "C1", "IMO", "Active", "ship@example.com", "N1", "N2", "N3"]],
    )
    _write_workbook(
        vessels_inventory_path,
        ["SHIPID", "SHIPNAME", "CUSTNO", "ITEM", "EDITION", "STOREEDT", "DESCRIP"],
        [["S1", "Ship", "C1", "ITEM1", "ED1", "SE1", "Desc"]],
    )

    return {
        "ic": ic_path,
        "vessels_index": vessels_index_path,
        "vessels_inventory": vessels_inventory_path,
    }


def _fetch_count(conn: sqlite3.Connection, table_name: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]


def _result_for(summary, source_name: str):
    for result in summary.results:
        if result.source_name == source_name:
            return result
    raise AssertionError(f"Missing ingestion result for {source_name}")


def test_valid_ingestion_inserts_rows(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    assert summary.has_warnings is False
    assert len(summary.results) == 3
    assert all(result.rows_inserted == 1 for result in summary.results)

    with db.connect() as conn:
        assert _fetch_count(conn, "vessel") == 1
        assert _fetch_count(conn, "vessel_inventory_row") == 1
        assert _fetch_count(conn, "ic_inventory_row") == 1


def test_missing_required_column_is_fatal(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["ic"],
        ["ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [["Desc", "PLIN", "CLS", "UPC", "ED1", date(2024, 1, 1)]],
    )

    with pytest.raises(IngestionFatalError):
        ingest_excel_files(
            ic_inventory_path=sources["ic"],
            vessels_index_path=sources["vessels_index"],
            vessels_inventory_path=sources["vessels_inventory"],
            db=db,
            paths=runtime_paths,
        )

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM validation_errors;").fetchall()

    assert rows
    assert any(row["error_type"] == "missing_required_column" for row in rows)
    assert any(row["severity"] == "fatal" for row in rows)


def test_empty_rows_emit_warnings_and_continue(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["ic"],
        ["ITEM", "ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [
            [None, None, None, None, None, None, None],
            ["ITEM1", "Desc", "PLIN", "CLS", "UPC", "ED1", date(2024, 1, 1)],
        ],
    )

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    ic_result = _result_for(summary, "safe_ic_inventory")
    assert ic_result.rows_seen == 2
    assert ic_result.rows_inserted == 1

    with db.connect() as conn:
        issues = conn.execute(
            "SELECT error_type FROM validation_errors WHERE error_type='empty_row';"
        ).fetchall()
        assert issues
        assert _fetch_count(conn, "ic_inventory_row") == 1


def test_duplicate_headers_warn_and_use_first_column(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["ic"],
        [
            "ITEM",
            "ITEM",
            "ITMDESC",
            "PLINID",
            "ITMCLSS",
            "UPCCODE",
            "EDITION",
            "CURRDATE",
        ],
        [["FIRST", "SECOND", "Desc", "PLIN", "CLS", "UPC", "ED1", date(2024, 1, 1)]],
    )

    ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        warnings = conn.execute(
            "SELECT * FROM validation_errors WHERE error_type='duplicate_header';"
        ).fetchall()
        row = conn.execute("SELECT item FROM ic_inventory_row;").fetchone()

    assert warnings
    assert row is not None
    assert row["item"] == "FIRST"


def test_missing_key_fields_skip_rows_with_warning(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["ic"],
        ["ITEM", "ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [[None, "Desc", "PLIN", "CLS", "UPC", "ED1", date(2024, 1, 1)]],
    )

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    ic_result = _result_for(summary, "safe_ic_inventory")
    assert ic_result.rows_seen == 1
    assert ic_result.rows_inserted == 0

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        issues = conn.execute(
            """
            SELECT * FROM validation_errors
            WHERE error_type='missing_req_col_field' AND column_name='item';
            """
        ).fetchall()

        assert issues
        assert _fetch_count(conn, "ic_inventory_row") == 0


def test_invalid_email_format_emits_warning_and_ingests_row(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["vessels_index"],
        [
            "SHIPID",
            "SHIPNAME",
            "CUSTNO",
            "IMONO",
            "SHIPSTAT",
            "EMAIL",
            "NOTE1",
            "NOTE2",
            "NOTE3",
        ],
        [["S1", "Ship", "C1", "IMO", "Active", "not-an-email", "N1", "N2", "N3"]],
    )

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    assert summary.has_warnings is True

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        issues = conn.execute(
            """
            SELECT * FROM validation_errors
            WHERE error_type='invalid_email_format' AND column_name='email';
            """
        ).fetchall()
        inserted_row = conn.execute("SELECT ship_email FROM vessel;").fetchone()

    assert issues
    assert inserted_row is not None
    assert inserted_row["ship_email"] == "not-an-email"


def test_invalid_date_format_warns_and_sets_null_current_date(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["ic"],
        ["ITEM", "ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [["ITEM1", "Desc", "PLIN", "CLS", "UPC", "ED1", "2024-01-01"]],
    )

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    assert summary.has_warnings is True

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        issues = conn.execute(
            """
            SELECT * FROM validation_errors
            WHERE error_type='invalid_date_format' AND column_name='currdate';
            """
        ).fetchall()
        ic_row = conn.execute('SELECT "current_date" FROM ic_inventory_row;').fetchone()

    assert issues
    assert ic_row is not None
    assert ic_row["current_date"] is None


def test_mmddyyyy_date_is_parsed_and_stored_as_iso_date(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["ic"],
        ["ITEM", "ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [["ITEM1", "Desc", "PLIN", "CLS", "UPC", "ED1", "02/14/2026"]],
    )

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    assert summary.has_warnings is False

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        ic_row = conn.execute('SELECT "current_date" FROM ic_inventory_row;').fetchone()

    assert ic_row is not None
    assert ic_row["current_date"] == "2026-02-14"


def test_numeric_shipid_is_coerced_to_string(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["vessels_index"],
        [
            "SHIPID",
            "SHIPNAME",
            "CUSTNO",
            "IMONO",
            "SHIPSTAT",
            "EMAIL",
            "NOTE1",
            "NOTE2",
            "NOTE3",
        ],
        [[12345, "Ship", "C1", "IMO", "Active", "ship@example.com", "N1", "N2", "N3"]],
    )

    ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT ship_id, typeof(ship_id) AS t FROM vessel;").fetchone()

    assert row is not None
    assert row["ship_id"] == "12345"
    assert row["t"] == "text"


def test_smrtchrt_emails_merged_with_email_column(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    """SMRTCHRT emails are appended to EMAIL, semicolons expanded, duplicates dropped."""
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["vessels_index"],
        ["SHIPID", "SHIPNAME", "CUSTNO", "IMONO", "SHIPSTAT", "EMAIL", "NOTE1", "NOTE2", "NOTE3", "SMRTCHRT"],
        [["S1", "Ship", "C1", "IMO", "Active", "ship@example.com", "N1", "N2", "N3", "smart1@example.com;smart2@example.com"]],
    )

    ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT ship_email FROM vessel;").fetchone()

    assert row is not None
    assert row["ship_email"] == "ship@example.com;smart1@example.com;smart2@example.com"


def test_smrtchrt_absent_uses_email_only(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    """When SMRTCHRT column is absent ship_email contains only the EMAIL value."""
    sources = _write_valid_sources(tmp_path)

    ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT ship_email FROM vessel;").fetchone()

    assert row is not None
    assert row["ship_email"] == "ship@example.com"


def test_smrtchrt_duplicate_emails_deduplicated(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    """Addresses already in EMAIL are not repeated when also present in SMRTCHRT."""
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["vessels_index"],
        ["SHIPID", "SHIPNAME", "CUSTNO", "IMONO", "SHIPSTAT", "EMAIL", "NOTE1", "NOTE2", "NOTE3", "SMRTCHRT"],
        [["S1", "Ship", "C1", "IMO", "Active", "ship@example.com", "N1", "N2", "N3", "ship@example.com;extra@example.com"]],
    )

    ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT ship_email FROM vessel;").fetchone()

    assert row is not None
    assert row["ship_email"] == "ship@example.com;extra@example.com"


def test_smrtchrt_invalid_email_warns_and_ingests(
    tmp_path: Path,
    db: Database,
    runtime_paths: paths_mod.RuntimePaths,
) -> None:
    """Invalid email in SMRTCHRT emits a warning but still ingests the row."""
    sources = _write_valid_sources(tmp_path)
    _write_workbook(
        sources["vessels_index"],
        ["SHIPID", "SHIPNAME", "CUSTNO", "IMONO", "SHIPSTAT", "EMAIL", "NOTE1", "NOTE2", "NOTE3", "SMRTCHRT"],
        [["S1", "Ship", "C1", "IMO", "Active", "ship@example.com", "N1", "N2", "N3", "not-an-email"]],
    )

    summary = ingest_excel_files(
        ic_inventory_path=sources["ic"],
        vessels_index_path=sources["vessels_index"],
        vessels_inventory_path=sources["vessels_inventory"],
        db=db,
        paths=runtime_paths,
    )

    assert summary.has_warnings is True

    with db.connect() as conn:
        conn.row_factory = sqlite3.Row
        issues = conn.execute(
            "SELECT * FROM validation_errors WHERE error_type='invalid_email_format' AND column_name='smrtchrt';"
        ).fetchall()
        row = conn.execute("SELECT ship_email FROM vessel;").fetchone()

    assert issues
    assert row is not None
    assert row["ship_email"] == "ship@example.com;not-an-email"
