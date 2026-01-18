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


DOMAIN_SCHEMA_SQL = """
CREATE TABLE vessel (
    ship_id TEXT,
    ship_name TEXT,
    customer_no TEXT,
    imo_no TEXT,
    ship_status TEXT,
    ship_email TEXT,
    office_email TEXT,
    ams INTEGER
);

CREATE TABLE vessel_inventory_row (
    ship_id TEXT,
    item TEXT,
    onboard_edition TEXT,
    store_edition TEXT,
    description TEXT
);

CREATE TABLE ic_inventory_row (
    item TEXT,
    current_edition TEXT,
    description TEXT,
    current_date TEXT
);
"""


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
    with db_instance.connect() as conn:
        conn.executescript(DOMAIN_SCHEMA_SQL)
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
            WHERE error_type='missing_key_field' AND column_name='item';
            """
        ).fetchall()

        assert issues
        assert _fetch_count(conn, "ic_inventory_row") == 0
