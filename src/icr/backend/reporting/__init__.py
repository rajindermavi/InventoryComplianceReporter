"""Reporting package.
- Per-vessel report data assembly
- HTML report rendering
- Run-level summary generation
- Output artifact layout on disk
"""

from .html import render_run_summary, render_vessel_report

__all__ = ["render_run_summary", "render_vessel_report"]
