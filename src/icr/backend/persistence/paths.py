"""Runtime path resolution utilities.

Runtime paths are resolved dynamically because executables may be packaged
with PyInstaller and can run from non-writable locations. Relative paths are
forbidden to avoid writing beside the executable or to an unexpected CWD.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

APP_DIR_NAME = "InventoryComplianceReporter"
RUNS_DIR_NAME = "runs"
RUN_SUBDIRS = ("data", "logs", "output", "tmp")


def _resolve_user_data_base() -> Path:
    """Resolve the per-user writable data root in a cross-platform way."""

    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if local_app_data:
            return Path(local_app_data)
        return Path.home() / "AppData" / "Local"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home)
    return Path.home() / ".local" / "share"


def get_app_data_dir() -> Path:
    """Return the per-user app data base directory.

    This uses the LOCALAPPDATA location on Windows, which is writable for the
    current user and safe for PyInstaller deployments. The directory is created
    if it does not exist.
    """

    base_dir = _resolve_user_data_base() / APP_DIR_NAME
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_runs_base_dir() -> Path:
    """Return the base directory for run artifacts.

    The runs directory is nested under the per-user app data location, which is
    writable and safe for PyInstaller executables. The directory is created if
    it does not exist.
    """

    runs_dir = get_app_data_dir() / RUNS_DIR_NAME
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


def _generate_run_id(suffix: str | None = None) -> str:
    """Generate a timestamp-based run ID with an optional suffix."""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
    if not suffix:
        return timestamp
    cleaned = suffix.strip().replace(" ", "-")
    if os.sep in cleaned or (os.altsep and os.altsep in cleaned):
        raise ValueError("Run suffix must not contain path separators.")
    return f"{timestamp}_{cleaned}"


def _reserve_run_dir(runs_base_dir: Path, run_id: str) -> tuple[str, Path]:
    """Create a unique run directory under the runs base directory."""

    candidate = run_id
    counter = 1
    while True:
        run_dir = runs_base_dir / candidate
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            counter += 1
            candidate = f"{run_id}_{counter:02d}"
            continue
        return candidate, run_dir


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved, run-scoped filesystem layout for a single execution."""

    run_id: str
    app_base_dir: Path
    run_dir: Path
    data_dir: Path
    logs_dir: Path
    output_dir: Path
    tmp_dir: Path
    log_file: Path

    @classmethod
    def create(cls, *, run_id: str | None = None, suffix: str | None = None) -> "RuntimePaths":
        """Create the run directory and all canonical subdirectories.

        Paths are resolved once and should be passed explicitly to downstream
        modules. The only filesystem side effects are under the per-user
        application data directory.
        """

        app_base_dir = get_app_data_dir()
        runs_base_dir = get_runs_base_dir()
        resolved_run_id = run_id or _generate_run_id(suffix)
        if run_id and suffix:
            raise ValueError("Provide either run_id or suffix, not both.")

        resolved_run_id, run_dir = _reserve_run_dir(runs_base_dir, resolved_run_id)
        subdirs = {name: run_dir / name for name in RUN_SUBDIRS}
        for path in subdirs.values():
            path.mkdir(parents=True, exist_ok=True)

        logs_dir = subdirs["logs"]
        log_file = logs_dir / "run.log"

        return cls(
            run_id=resolved_run_id,
            app_base_dir=app_base_dir,
            run_dir=run_dir,
            data_dir=subdirs["data"],
            logs_dir=logs_dir,
            output_dir=subdirs["output"],
            tmp_dir=subdirs["tmp"],
            log_file=log_file,
        )
