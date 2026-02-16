"""Domain-level functions for vessel discovery and processing."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from icr.backend.persistence import get_runs_base_dir

from .queries import get_ams_vessels


def _get_latest_run_db_path() -> Path | None:
    """Find the most recent run database.

    Returns the database path from the most recently modified run directory,
    or None if no runs exist.
    """
    runs_base = get_runs_base_dir()
    run_dirs = [entry for entry in runs_base.iterdir() if entry.is_dir()]

    if not run_dirs:
        return None

    # Sort by modification time, newest first
    latest_run = sorted(run_dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    db_path = latest_run / "data" / "run.sqlite"

    return db_path if db_path.exists() else None


def discover_ams_vessels() -> list[dict[str, str]]:
    """Fetch all AMS-marked vessels from the most recent run database.

    Returns:
        A list of vessel dictionaries with keys: ship_id, ams, ship_email, office_email

    Raises:
        FileNotFoundError: If no run database exists
        sqlite3.Error: If database query fails
    """
    db_path = _get_latest_run_db_path()

    if db_path is None:
        raise FileNotFoundError("No run database found. Please ingest data first.")

    conn = sqlite3.connect(db_path)
    try:
        vessels = get_ams_vessels(conn)
        # Convert sqlite3.Row objects to dictionaries
        return [dict(row) for row in vessels]
    finally:
        conn.close()


def process_vessels(vessel_ids: list[str]) -> dict[str, int]:
    """Process selected vessels to generate issue row reports.

    Args:
        vessel_ids: List of ship IDs to process

    Returns:
        A summary dictionary with processing statistics

    Raises:
        FileNotFoundError: If no run database exists
        sqlite3.Error: If database query fails
    """
    db_path = _get_latest_run_db_path()

    if db_path is None:
        raise FileNotFoundError("No run database found. Please ingest data first.")

    # TODO: Implement vessel processing logic
    # For now, return a basic summary
    return {
        "vessels_processed": len(vessel_ids),
        "vessels_with_issues": 0,
        "total_issue_rows": 0,
    }