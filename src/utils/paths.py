"""Runtime path resolution utilities.

Runtime paths are resolved dynamically because executables may be packaged
with PyInstaller and can run from non-writable locations. Relative paths are
forbidden to avoid writing beside the executable or to an unexpected CWD.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_app_data_dir() -> Path:
    """Return the per-user app data base directory.

    This uses the LOCALAPPDATA location on Windows, which is writable for the
    current user and safe for PyInstaller deployments. The directory is created
    if it does not exist.
    """

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError(
            "LOCALAPPDATA is not set; cannot resolve a writable runtime directory."
        )

    base_dir = Path(local_app_data) / "InventoryComplianceReporter"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_runs_base_dir() -> Path:
    """Return the base directory for run artifacts.

    The runs directory is nested under the per-user app data location, which is
    writable and safe for PyInstaller executables. The directory is created if
    it does not exist.
    """

    runs_dir = get_app_data_dir() / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir


def get_run_dir(run_id: str) -> Path:
    """Return the directory for a specific run ID.

    Each run is placed under the runs base directory to keep artifacts in a
    user-writable, PyInstaller-safe location. The directory is created if it
    does not exist.
    """

    run_dir = get_runs_base_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
