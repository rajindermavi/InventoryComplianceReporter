"""Read-only domain queries for Phase 3 comparison data."""

from __future__ import annotations

import sqlite3
from typing import Iterable


def _ensure_row_factory(conn: sqlite3.Connection) -> None:
    if conn.row_factory is None:
        conn.row_factory = sqlite3.Row


def get_ams_vessels(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    """Return all vessels marked as AMS."""
    _ensure_row_factory(conn)
    query = """
        SELECT
            ship_id,
            is_ams,
            vessel_email,
            office_email
        FROM vessels
        WHERE is_ams = 1
        ORDER BY ship_id
    """
    return conn.execute(query).fetchall()


def get_onboard_inventory(
    conn: sqlite3.Connection, ship_id: str
) -> Iterable[sqlite3.Row]:
    """Return onboard inventory records for the given vessel."""
    _ensure_row_factory(conn)
    query = """
        SELECT
            ship_id,
            item,
            edition
        FROM onboard_inventory
        WHERE ship_id = ?
        ORDER BY item
    """
    return conn.execute(query, (ship_id,)).fetchall()


def get_reference_inventory(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    """Return reference (IC) inventory records."""
    _ensure_row_factory(conn)
    query = """
        SELECT
            item,
            edition
        FROM reference_inventory
        ORDER BY item
    """
    return conn.execute(query).fetchall()
