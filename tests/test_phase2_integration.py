"""Minimal integration test for Phase 2 happy path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
from openpyxl import Workbook

from icr.backend.ingest.excel_reader import IC_SPEC, _ingest_single_file
from icr.backend.persistence import paths as paths_mod
from icr.backend.persistence.db import Database, RunMetadata


@dataclass(frozen=True)
class DbRuntimePaths:
    """Runtime paths wrapper providing the database path."""

    run_id: str
    db_path: Path


def _write_workbook(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


def _create_ic_table(db: Database) -> None:
    with db.connect() as conn:
        conn.execute(
            """
            CREATE TABLE ic_inventory_row (
                item TEXT,
                current_edition TEXT,
                description TEXT,
                current_date TEXT
            );
            """
        )


def test_phase2_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise runtime paths, database lifecycle, and single-file ingestion."""

    monkeypatch.setattr(paths_mod, "_resolve_user_data_base", lambda: tmp_path)

    # 1) Create runtime paths.
    runtime_paths = paths_mod.RuntimePaths.create()
    assert runtime_paths.run_dir.exists()

    # 2) Initialize the database.
    db_paths = DbRuntimePaths(
        run_id=runtime_paths.run_id,
        db_path=runtime_paths.data_dir / "run.sqlite",
    )
    db = Database(db_paths)
    db.initialize(
        RunMetadata(
            run_id=db_paths.run_id,
            app_version="1.2.3",
            git_commit="deadbeef",
            build_date="2024-01-01",
            input_fingerprint="abc123",
        )
    )
    _create_ic_table(db)

    # 3) Ingest one valid Excel file.
    ic_path = tmp_path / "SAFE_IC_INVENTORY.xlsx"
    _write_workbook(
        ic_path,
        ["ITEM", "ITMDESC", "PLINID", "ITMCLSS", "UPCCODE", "EDITION", "CURRDATE"],
        [["ITEM1", "Desc", "PLIN", "CLS", "UPC", "ED1", date(2024, 1, 1)]],
    )
    result = _ingest_single_file(ic_path, IC_SPEC, db, runtime_paths)

    # 4) Assert database exists, rows inserted, and no fatal errors.
    assert db.db_path.exists()
    assert result.rows_inserted == 1
    assert result.warnings == ()
    with db.connect() as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM ic_inventory_row;").fetchone()[0]
    assert row_count == 1
