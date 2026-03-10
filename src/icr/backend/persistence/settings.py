"""Persistent user settings stored in the app data directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from icr.backend.persistence.paths import get_app_data_dir

SETTINGS_FILE = "settings.json"


def _settings_path() -> Path:
    return get_app_data_dir() / SETTINGS_FILE


def load_settings() -> dict[str, Any]:
    """Return saved settings, or an empty dict if none exist."""
    path = _settings_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict[str, Any]) -> None:
    """Persist *settings* to disk, merging with any existing values."""
    path = _settings_path()
    current = load_settings()
    current.update(settings)
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
