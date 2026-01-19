"""HTML reporting boundary.

Responsibilities:
- Render HTML report artifacts
- Apply templates and layout rules
"""

from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence

from icr.backend.domain.models import IssueType


def render_vessel_report(
    vessel: Mapping[str, Any],
    issues: Sequence[Any],
    *,
    run_timestamp: str,
    source_files: Sequence[str],
) -> str:
    """Render a per-vessel compliance report as HTML."""
    ship_id = _coerce_text(vessel.get("ship_id")) or "UNKNOWN"
    ship_name = _coerce_text(vessel.get("ship_name"))
    vessel_label = _format_vessel_label(ship_id, ship_name)

    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>Vessel Report - {escape(ship_id)}</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; color: #222; margin: 24px; }",
        "h1, h2 { margin-bottom: 0.3em; }",
        ".meta { margin: 0.2em 0; }",
        "table { border-collapse: collapse; width: 100%; margin-top: 12px; }",
        "th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }",
        "th { background: #f2f2f2; }",
        ".ok { color: #1b5e20; font-weight: bold; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Inventory Compliance Report</h1>",
        f'<p class="meta"><strong>Vessel:</strong> {escape(vessel_label)}</p>',
        f'<p class="meta"><strong>Run timestamp:</strong> {escape(run_timestamp)}</p>',
        "<h2>Source Files</h2>",
        _render_source_files(source_files),
        "<h2>Discrepancies</h2>",
    ]

    if issues:
        lines.append(_render_issue_table(issues))
    else:
        lines.append('<p class="ok">No issues found for this vessel.</p>')

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines)


def render_run_summary(
    vessels: Sequence[Mapping[str, Any]],
    *,
    run_timestamp: str,
) -> str:
    """Render a run-level summary report as HTML."""
    total = len(vessels)
    with_issues = sum(1 for vessel in vessels if _coerce_int(vessel.get("issue_count")) > 0)
    without_issues = total - with_issues

    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Run Summary</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; color: #222; margin: 24px; }",
        "h1, h2 { margin-bottom: 0.3em; }",
        ".meta { margin: 0.2em 0; }",
        "table { border-collapse: collapse; width: 100%; margin-top: 12px; }",
        "th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }",
        "th { background: #f2f2f2; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Run Summary</h1>",
        f'<p class="meta"><strong>Run timestamp:</strong> {escape(run_timestamp)}</p>',
        f'<p class="meta"><strong>Vessels processed:</strong> {total}</p>',
        f'<p class="meta"><strong>Vessels with issues:</strong> {with_issues}</p>',
        f'<p class="meta"><strong>Vessels with no issues:</strong> {without_issues}</p>',
        "<h2>Vessels</h2>",
    ]

    if vessels:
        lines.append(_render_vessel_summary_table(vessels))
    else:
        lines.append("<p>No vessels processed.</p>")

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines)


def _render_source_files(source_files: Sequence[str]) -> str:
    if not source_files:
        return "<p>No source files provided.</p>"
    items = "\n".join(f"<li>{escape(_coerce_text(name))}</li>" for name in source_files)
    return f"<ul>\n{items}\n</ul>"


def _render_issue_table(issues: Sequence[Any]) -> str:
    rows = []
    for issue in issues:
        item = _coerce_text(_get_field(issue, "item"))
        onboard = _format_optional(_get_field(issue, "onboard_edition"))
        current = _format_optional(_get_field(issue, "current_edition"))
        issue_type = _format_issue_type(_get_field(issue, "issue_type"))
        rows.append(
            "<tr>"
            f"<td>{escape(item)}</td>"
            f"<td>{escape(onboard)}</td>"
            f"<td>{escape(current)}</td>"
            f"<td>{escape(issue_type)}</td>"
            "</tr>"
        )

    header = (
        "<tr>"
        "<th>Item</th>"
        "<th>Onboard Edition</th>"
        "<th>Current Edition</th>"
        "<th>Issue Type</th>"
        "</tr>"
    )
    return f"<table>\n{header}\n" + "\n".join(rows) + "\n</table>"


def _render_vessel_summary_table(vessels: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for vessel in vessels:
        ship_id = _coerce_text(vessel.get("ship_id")) or "UNKNOWN"
        ship_name = _coerce_text(vessel.get("ship_name"))
        label = _format_vessel_label(ship_id, ship_name)
        issue_count = _coerce_int(vessel.get("issue_count"))
        report_name = _coerce_text(vessel.get("report_filename"))
        report_cell = escape(report_name)
        if report_name:
            report_cell = f'<a href="{escape(report_name)}">{escape(report_name)}</a>'
        rows.append(
            "<tr>"
            f"<td>{escape(label)}</td>"
            f"<td>{issue_count}</td>"
            f"<td>{report_cell}</td>"
            "</tr>"
        )

    header = (
        "<tr>"
        "<th>Vessel</th>"
        "<th>Issue Count</th>"
        "<th>Report File</th>"
        "</tr>"
    )
    return f"<table>\n{header}\n" + "\n".join(rows) + "\n</table>"


def _format_vessel_label(ship_id: str, ship_name: str | None) -> str:
    if ship_name:
        return f"{ship_id} - {ship_name}"
    return ship_id


def _format_optional(value: Any) -> str:
    text = _coerce_text(value)
    if not text:
        return "N/A"
    return text


def _format_issue_type(value: Any) -> str:
    if isinstance(value, IssueType):
        value = value.value
    text = _coerce_text(value).upper()
    if text == "OUTDATED":
        return "Outdated"
    if text == "MISSING_ONBOARD":
        return "Missing onboard edition"
    if text == "MISSING_REFERENCE":
        return "Missing reference edition"
    return _coerce_text(value) or "Unknown"


def _get_field(record: Any, field: str) -> Any:
    if hasattr(record, field):
        return getattr(record, field)
    if isinstance(record, Mapping):
        return record.get(field)
    return None


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _coerce_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    text = _coerce_text(value).strip()
    return int(text) if text.isdigit() else 0
