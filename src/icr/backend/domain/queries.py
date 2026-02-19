"""Read-only domain queries for Phase 3 comparison data."""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Mapping


def _ensure_row_factory(conn: sqlite3.Connection) -> None:
    if conn.row_factory is None:
        conn.row_factory = sqlite3.Row


def get_ams_vessels(conn: sqlite3.Connection) -> Iterable[Mapping[str, Any]]:
    """Return all vessels marked as AMS."""
    _ensure_row_factory(conn)
    query = """
        SELECT
            ship_id,
            ship_name,
            ams,
            ship_email,
            office_email
        FROM vessel
        WHERE ams = 1
        ORDER BY ship_id
    """
    rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def get_onboard_inventory(
    conn: sqlite3.Connection, ship_id: str
) -> Iterable[Mapping[str, Any]]:
    """Return onboard inventory records for the given vessel."""
    _ensure_row_factory(conn)
    query = """
        SELECT
            ship_id,
            item,
            onboard_edition,
            description
        FROM vessel_inventory_row
        WHERE ship_id = ?
        ORDER BY item
    """
    rows = conn.execute(query, (ship_id,)).fetchall()
    return [dict(row) for row in rows]


def get_reference_inventory(conn: sqlite3.Connection) -> Iterable[Mapping[str, Any]]:
    """Return reference (IC) inventory records."""
    _ensure_row_factory(conn)
    query = """
        SELECT
            item,
            description,
            current_edition
        FROM ic_inventory_row
        ORDER BY item
    """
    rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]
