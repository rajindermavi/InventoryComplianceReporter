"""PDF renderer selection for Phase 7A.

This module chooses an available HTML -> PDF renderer without requiring
optional dependencies at import time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class PdfRenderer(Protocol):
    """Protocol for HTML -> PDF renderers."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str | None: ...

    def render(self, html_path: Path, pdf_path: Path) -> None: ...


class _WeasyPrintRenderer:
    def __init__(self, html_cls: object, version: str | None) -> None:
        self._html_cls = html_cls
        self._version = version

    @property
    def name(self) -> str:
        return "weasyprint"

    @property
    def version(self) -> str | None:
        return self._version

    def render(self, html_path: Path, pdf_path: Path) -> None:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        html = self._html_cls(filename=str(html_path))
        html.write_pdf(str(pdf_path))


def choose_renderer(preference: str | None) -> PdfRenderer | None:
    """Choose a PDF renderer based on the user preference.

    Returns None when no supported renderer is available.
    """

    normalized = (preference or "auto").strip().lower()

    if normalized in {"auto", "weasyprint", "weasy-print"}:
        renderer = _load_weasyprint_renderer()
        if renderer:
            return renderer
        if normalized != "auto":
            return None

    return None


def _load_weasyprint_renderer() -> PdfRenderer | None:
    try:
        import weasyprint  # type: ignore[import-not-found]
    except Exception:
        return None

    try:
        html_cls = weasyprint.HTML
        version = getattr(weasyprint, "__version__", None)
    except Exception:
        return None

    return _WeasyPrintRenderer(html_cls, version)
