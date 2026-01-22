from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from icr.backend.delivery.pdf import render as pdf_render


@dataclass
class FakeRunPaths:
    output_dir: Path


class FakePdfRenderer:
    def __init__(self, *, fail_on: set[Path] | None = None) -> None:
        self._fail_on = fail_on or set()

    @property
    def name(self) -> str:
        return "fake-renderer"

    @property
    def version(self) -> str | None:
        return "1.0"

    def render(self, html_path: Path, pdf_path: Path) -> None:
        if html_path in self._fail_on:
            raise RuntimeError("boom")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-FAKE")


@pytest.fixture
def run_paths(tmp_path: Path) -> FakeRunPaths:
    return FakeRunPaths(output_dir=tmp_path / "output")


@pytest.fixture
def vessels() -> list[dict[str, str]]:
    return [
        {"ship_id": "VESSEL_001", "report_filename": "reports/html/VESSEL_001.html"},
        {"ship_id": "VESSEL_002", "report_filename": "reports/html/VESSEL_002.html"},
    ]


@pytest.fixture
def html_reports(run_paths: FakeRunPaths, vessels: list[dict[str, str]]) -> dict[str, Path]:
    reports_dir = run_paths.output_dir / "reports" / "html"
    reports_dir.mkdir(parents=True, exist_ok=True)
    created: dict[str, Path] = {}
    for vessel in vessels:
        path = reports_dir / f"{vessel['ship_id']}.html"
        path.write_text(f"<html>{vessel['ship_id']}</html>", encoding="utf-8")
        created[vessel["ship_id"]] = path
    return created


def _options(**kwargs: object) -> dict[str, object]:
    return kwargs


def test_pdf_generation_disabled_skips_all(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], html_reports: dict[str, Path]
) -> None:
    results = pdf_render.generate_pdfs(
        run_paths,
        vessels,
        _options(pdf_enabled=False),
        logger=None,
    )

    assert len(results) == len(vessels)
    assert all(result.status == "skipped" for result in results)
    assert all(result.reason and "disabled" in result.reason.lower() for result in results)

    pdf_dir = run_paths.output_dir / "reports" / "pdf"
    assert not pdf_dir.exists()


def test_pdf_missing_html_is_skipped(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], html_reports: dict[str, Path], monkeypatch
) -> None:
    missing_vessel = {"ship_id": "VESSEL_003", "report_filename": "reports/html/VESSEL_003.html"}
    all_vessels = vessels + [missing_vessel]

    monkeypatch.setattr(pdf_render, "choose_renderer", lambda preference: FakePdfRenderer())

    results = pdf_render.generate_pdfs(
        run_paths,
        all_vessels,
        _options(pdf_enabled=True),
        logger=None,
    )

    by_vessel = {result.vessel_id: result for result in results}
    assert by_vessel["VESSEL_003"].status == "skipped"
    assert "html" in (by_vessel["VESSEL_003"].reason or "").lower()
    assert by_vessel["VESSEL_001"].status == "generated"
    assert by_vessel["VESSEL_002"].status == "generated"
    assert by_vessel["VESSEL_003"].pdf_path is None


def test_pdf_renderer_unavailable(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], html_reports: dict[str, Path], monkeypatch
) -> None:
    monkeypatch.setattr(pdf_render, "choose_renderer", lambda preference: None)

    results = pdf_render.generate_pdfs(
        run_paths,
        vessels,
        _options(pdf_enabled=True),
        logger=None,
    )

    assert len(results) == len(vessels)
    assert all(result.status == "skipped" for result in results)
    assert all("renderer" in (result.reason or "").lower() for result in results)

    pdf_dir = run_paths.output_dir / "reports" / "pdf"
    assert not pdf_dir.exists()


def test_pdf_successful_generation(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], html_reports: dict[str, Path], monkeypatch
) -> None:
    monkeypatch.setattr(pdf_render, "choose_renderer", lambda preference: FakePdfRenderer())

    results = pdf_render.generate_pdfs(
        run_paths,
        vessels,
        _options(pdf_enabled=True),
        logger=None,
    )

    assert all(result.status == "generated" for result in results)
    assert all(result.renderer_name == "fake-renderer" for result in results)
    assert all(result.renderer_version == "1.0" for result in results)

    pdf_paths = {result.vessel_id: result.pdf_path for result in results}
    assert pdf_paths["VESSEL_001"] == run_paths.output_dir / "reports" / "pdf" / "VESSEL_001.pdf"
    assert pdf_paths["VESSEL_002"] == run_paths.output_dir / "reports" / "pdf" / "VESSEL_002.pdf"
    assert pdf_paths["VESSEL_001"].exists()
    assert pdf_paths["VESSEL_002"].exists()


def test_pdf_renderer_failure_isolated(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], html_reports: dict[str, Path], monkeypatch
) -> None:
    failing_html = html_reports["VESSEL_002"]
    renderer = FakePdfRenderer(fail_on={failing_html})
    monkeypatch.setattr(pdf_render, "choose_renderer", lambda preference: renderer)

    results = pdf_render.generate_pdfs(
        run_paths,
        vessels,
        _options(pdf_enabled=True),
        logger=None,
    )

    by_vessel = {result.vessel_id: result for result in results}
    assert by_vessel["VESSEL_002"].status == "failed"
    assert by_vessel["VESSEL_001"].status == "generated"
    assert (by_vessel["VESSEL_002"].reason or "").lower()
    assert by_vessel["VESSEL_001"].pdf_path is not None
    assert by_vessel["VESSEL_001"].pdf_path.exists()


def test_pdf_does_not_mutate_html(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], html_reports: dict[str, Path], monkeypatch
) -> None:
    monkeypatch.setattr(pdf_render, "choose_renderer", lambda preference: FakePdfRenderer())

    html_path = html_reports["VESSEL_001"]
    before_mtime = html_path.stat().st_mtime_ns

    first = pdf_render.generate_pdfs(
        run_paths,
        vessels,
        _options(pdf_enabled=True),
        logger=None,
    )
    second = pdf_render.generate_pdfs(
        run_paths,
        vessels,
        _options(pdf_enabled=True),
        logger=None,
    )

    after_mtime = html_path.stat().st_mtime_ns
    assert before_mtime == after_mtime

    first_path = {result.vessel_id: result.pdf_path for result in first}["VESSEL_001"]
    second_path = {result.vessel_id: result.pdf_path for result in second}["VESSEL_001"]
    assert first_path == second_path
