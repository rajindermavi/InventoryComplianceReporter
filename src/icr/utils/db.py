"""
Database lifecycle management.

Responsibilities:
- Resolve per-user writable runtime directory (Windows-safe)
- Create per-run SQLite database file
- Ensure auditability and deterministic run layout

Notes:
- Application is distributed via PyInstaller
- Runtime data must NOT be written relative to executable path
- Default base directory should be under LOCALAPPDATA

Implementation deferred to Phase 2.
"""