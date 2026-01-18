"""Tests for runtime path resolution and run-scoped directories."""

from __future__ import annotations

from pathlib import Path

import pytest

from icr.backend.persistence import paths as paths_mod


@pytest.fixture()
def runtime_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a temp-backed app data base for runtime path tests."""

    monkeypatch.setattr(paths_mod, "_resolve_user_data_base", lambda: tmp_path)
    return tmp_path


def test_run_directory_created(runtime_base: Path) -> None:
    runtime_paths = paths_mod.RuntimePaths.create()

    assert runtime_paths.run_dir.exists()
    assert runtime_paths.run_dir.is_dir()


def test_app_data_dir_resolution(runtime_base: Path) -> None:
    app_dir = paths_mod.get_app_data_dir()

    assert app_dir == runtime_base / paths_mod.APP_DIR_NAME
    assert app_dir.exists()
    assert app_dir.is_dir()


def test_subdirectory_structure(runtime_base: Path) -> None:
    runtime_paths = paths_mod.RuntimePaths.create()

    subdirs = {
        runtime_paths.data_dir,
        runtime_paths.logs_dir,
        runtime_paths.output_dir,
        runtime_paths.tmp_dir,
    }

    for subdir in subdirs:
        assert subdir.exists()
        assert subdir.is_dir()
        assert subdir.parent == runtime_paths.run_dir


def test_isolation_between_instances(runtime_base: Path) -> None:
    first = paths_mod.RuntimePaths.create(run_id="test-run")
    second = paths_mod.RuntimePaths.create(run_id="test-run")

    assert first.run_dir != second.run_dir
    assert first.run_id != second.run_id
    assert first.run_dir.exists()
    assert second.run_dir.exists()


def test_stable_attribute_access(runtime_base: Path) -> None:
    runtime_paths = paths_mod.RuntimePaths.create()

    run_dir = runtime_paths.run_dir
    data_dir = runtime_paths.data_dir
    logs_dir = runtime_paths.logs_dir
    output_dir = runtime_paths.output_dir
    tmp_dir = runtime_paths.tmp_dir

    assert runtime_paths.run_dir == run_dir
    assert runtime_paths.data_dir == data_dir
    assert runtime_paths.logs_dir == logs_dir
    assert runtime_paths.output_dir == output_dir
    assert runtime_paths.tmp_dir == tmp_dir
