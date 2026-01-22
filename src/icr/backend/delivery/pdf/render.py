"""Phase 7A PDF generation orchestrator.

Consumes existing HTML report artifacts and writes PDF copies into the
run workspace without mutating report content.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Protocol

from .engine import PdfRenderer, choose_renderer


class _LoggerLike(Protocol):
    def info(self, msg: str, *args: object, **kwargs: object) -> None: ...

    def warning(self, msg: str, *args: object, **kwargs: object) -> None: ...

    def error(self, msg: str, *args: object, **kwargs: object) -> None: ...

    def exception(self, msg: str, *args: object, **kwargs: object) -> None: ...


@dataclass(frozen=True)
class PdfResult:
    """Per-vessel PDF generation outcome."""

    vessel_id: str
    status: str
    pdf_path: Path | None
    reason: str | None
    renderer_name: str | None
    renderer_version: str | None


def generate_pdfs(
    run_paths: object,
    vessels: Iterable[object],
    options: object,
    logger: _LoggerLike | None,
) -> list[PdfResult]:
    """Generate PDFs from existing HTML reports without altering HTML."""

    pdf_enabled = bool(_get_option(options, "pdf_enabled", False))
    renderer_preference = _get_option(options, "pdf_renderer", None) or _get_option(
        options, "pdf_renderer_preference", None
    )

    if not pdf_enabled:
        return [
            PdfResult(
                vessel_id=_coerce_vessel_id(vessel) or "UNKNOWN",
                status="skipped",
                pdf_path=None,
                reason="PDF generation disabled by user.",
                renderer_name=None,
                renderer_version=None,
            )
            for vessel in vessels
        ]

    renderer = choose_renderer(renderer_preference)
    renderer_name, renderer_version = _renderer_metadata(renderer)

    reports_root = _resolve_reports_root(run_paths)
    html_files = _list_html_files(reports_root)

    results: list[PdfResult] = []

    for vessel in vessels:
        vessel_id = _coerce_vessel_id(vessel)
        if not vessel_id:
            results.append(
                PdfResult(
                    vessel_id="UNKNOWN",
                    status="skipped",
                    pdf_path=None,
                    reason="Missing vessel identifier.",
                    renderer_name=renderer_name,
                    renderer_version=renderer_version,
                )
            )
            continue

        html_path = _resolve_html_report(vessel, vessel_id, reports_root, html_files)
        if not html_path or not html_path.exists():
            results.append(
                PdfResult(
                    vessel_id=vessel_id,
                    status="skipped",
                    pdf_path=None,
                    reason="HTML report not found for vessel.",
                    renderer_name=renderer_name,
                    renderer_version=renderer_version,
                )
            )
            if logger:
                logger.warning("PDF skipped: missing HTML report for %s", vessel_id)
            continue

        if renderer is None:
            results.append(
                PdfResult(
                    vessel_id=vessel_id,
                    status="skipped",
                    pdf_path=None,
                    reason="No PDF renderer available.",
                    renderer_name=None,
                    renderer_version=None,
                )
            )
            if logger:
                logger.warning("PDF skipped: renderer unavailable for %s", vessel_id)
            continue

        pdf_path = _pdf_output_path(html_path)

        try:
            renderer.render(html_path, pdf_path)
        except Exception as exc:  # noqa: BLE001 - per-vessel failure only
            reason = _format_exception_reason(exc)
            results.append(
                PdfResult(
                    vessel_id=vessel_id,
                    status="failed",
                    pdf_path=None,
                    reason=reason,
                    renderer_name=renderer_name,
                    renderer_version=renderer_version,
                )
            )
            if logger:
                logger.exception("PDF generation failed for %s", vessel_id)
            continue

        results.append(
            PdfResult(
                vessel_id=vessel_id,
                status="generated",
                pdf_path=pdf_path,
                reason=None,
                renderer_name=renderer_name,
                renderer_version=renderer_version,
            )
        )
        if logger:
            logger.info("PDF generated for %s", vessel_id)

    # TODO: Append PDF results to summary.json in an append-only manner.
    return results


def _resolve_reports_root(run_paths: object) -> Path:
    if isinstance(run_paths, (str, Path)):
        return Path(run_paths)
    for attr in ("output_dir", "run_dir", "reports_dir", "reporting_dir"):
        if hasattr(run_paths, attr):
            value = getattr(run_paths, attr)
            if value:
                return Path(value)
    return Path(".")


def _list_html_files(reports_root: Path) -> list[Path]:
    if not reports_root.exists():
        return []
    return sorted(path for path in reports_root.rglob("*.html") if path.is_file())


def _resolve_html_report(
    vessel: object,
    vessel_id: str,
    reports_root: Path,
    html_files: list[Path],
) -> Path | None:
    explicit = _extract_report_path(vessel, reports_root)
    if explicit and explicit.exists():
        return explicit

    normalized = vessel_id.strip().lower()
    exact = [path for path in html_files if path.stem.lower() == normalized]
    if exact:
        return exact[0]

    contains = [path for path in html_files if normalized and normalized in path.stem.lower()]
    if not contains:
        return None

    return sorted(contains, key=_path_sort_key)[0]


def _extract_report_path(vessel: object, reports_root: Path) -> Path | None:
    for key in (
        "report_path",
        "report_file",
        "report_filename",
        "html_report",
        "html_report_path",
    ):
        value = _get_option(vessel, key, None)
        if not value:
            continue
        path = Path(str(value))
        if not path.is_absolute():
            path = reports_root / path
        return path
    return None


def _pdf_output_path(html_path: Path) -> Path:
    if html_path.parent.name.lower() == "html":
        pdf_dir = html_path.parent.parent / "pdf"
    else:
        pdf_dir = html_path.parent
    return pdf_dir / f"{html_path.stem}.pdf"


def _renderer_metadata(renderer: PdfRenderer | None) -> tuple[str | None, str | None]:
    if renderer is None:
        return None, None
    name = getattr(renderer, "name", None)
    version = getattr(renderer, "version", None)
    return name, version


def _coerce_vessel_id(vessel: object) -> str:
    if isinstance(vessel, str):
        return vessel.strip()
    for key in ("ship_id", "vessel_id", "id"):
        value = _get_option(vessel, key, None)
        if value:
            return str(value).strip()
    return ""


def _get_option(container: object, name: str, default: object) -> object:
    if container is None:
        return default
    if isinstance(container, Mapping):
        return container.get(name, default)
    if hasattr(container, name):
        return getattr(container, name)
    return default


def _path_sort_key(path: Path) -> tuple[int, str]:
    return (len(path.stem), str(path))


def _format_exception_reason(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return type(exc).__name__
