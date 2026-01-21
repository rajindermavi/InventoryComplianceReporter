"""Email drafting boundary.

Responsibilities:
- Compose email drafts from report artifacts
- Apply configured templates and subject lines
- Resolve recipients and generate .eml drafts
- Append-only updates to summary.json
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from string import Formatter
from typing import Any, Mapping, Sequence

EMAIL_PHASE = "email_drafting"
DEFAULT_SUBJECT_TEMPLATE = "Inventory Compliance - {SHIPNAME}"
EMAIL_REGEX = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass(frozen=True)
class DraftAttachment:
    """Binary attachment included with the draft email."""

    filename: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class DraftEmail:
    """In-memory representation of a drafted email."""

    vessel_id: str
    to_addresses: tuple[str, ...]
    subject: str
    html_body: str
    attachments: tuple[DraftAttachment, ...]
    eml_path: Path | None
    eml_bytes: bytes | None


@dataclass(frozen=True)
class DraftIssue:
    """Validation error or warning encountered during drafting."""

    vessel_id: str | None
    message: str
    severity: str


@dataclass(frozen=True)
class DraftingResult:
    """Aggregate result of draft email generation."""

    drafts: tuple[DraftEmail, ...]
    errors: tuple[DraftIssue, ...]
    warnings: tuple[DraftIssue, ...]


def draft_emails(
    vessels: Sequence[Mapping[str, Any]],
    *,
    html_reports: Mapping[str, str | Path],
    summary_path: Path | str,
    subject_template: str = DEFAULT_SUBJECT_TEMPLATE,
    default_office_email: str | None = None,
    include_pdf: bool = False,
    pdf_reports: Mapping[str, str | Path] | None = None,
    eml_output_dir: Path | str | None = None,
    from_email: str | None = None,
    run_id: str | None = None,
) -> DraftingResult:
    """Draft per-vessel emails and update summary.json.

    Args:
        vessels: Sequence of vessel metadata mappings.
        html_reports: Map of ship_id -> HTML report content or path.
        summary_path: Path to the run summary.json file.
        subject_template: Subject template using format placeholders.
        default_office_email: Office email fallback when missing on vessel.
        include_pdf: Attach PDFs when available.
        pdf_reports: Map of ship_id -> PDF path (optional).
        eml_output_dir: Optional directory to write .eml drafts.
        from_email: Optional From header for .eml drafts.
        run_id: Optional run_id to use for templating.
    """

    summary = _read_summary(summary_path)
    resolved_run_id = run_id or _coerce_text(summary.get("run_id"))

    drafts: list[DraftEmail] = []
    errors: list[DraftIssue] = []
    warnings: list[DraftIssue] = []
    processed = 0

    for vessel in vessels:
        ship_id = _coerce_text(vessel.get("ship_id"))
        if not ship_id:
            errors.append(
                DraftIssue(
                    vessel_id=None,
                    message="Missing required vessel identifier: ship_id.",
                    severity="error",
                )
            )
            continue

        vessel_errors: list[DraftIssue] = []
        vessel_warnings: list[DraftIssue] = []

        recipients = _resolve_recipients(
            vessel,
            default_office_email=default_office_email,
            errors=vessel_errors,
        )

        report_html = _resolve_html_report(
            html_reports.get(ship_id), ship_id=ship_id, errors=vessel_errors
        )

        subject = _format_subject(
            subject_template,
            vessel,
            run_id=resolved_run_id,
            warnings=vessel_warnings,
        )

        attachments = _resolve_attachments(
            ship_id,
            include_pdf=include_pdf,
            pdf_reports=pdf_reports,
            warnings=vessel_warnings,
        )

        if vessel_errors:
            errors.extend(vessel_errors)
            warnings.extend(vessel_warnings)
            continue

        message = _build_email_message(
            to_addresses=recipients,
            subject=subject,
            html_body=report_html,
            attachments=attachments,
            from_email=from_email,
        )

        eml_path: Path | None = None
        eml_bytes: bytes | None = None
        if eml_output_dir:
            eml_dir = Path(eml_output_dir)
            eml_dir.mkdir(parents=True, exist_ok=True)
            filename = _format_eml_filename(ship_id, vessel.get("ship_name"))
            eml_path = eml_dir / filename
            eml_bytes = message.as_bytes()
            eml_path.write_bytes(eml_bytes)

        drafts.append(
            DraftEmail(
                vessel_id=ship_id,
                to_addresses=tuple(recipients),
                subject=subject,
                html_body=report_html,
                attachments=tuple(attachments),
                eml_path=eml_path,
                eml_bytes=eml_bytes,
            )
        )
        processed += 1
        warnings.extend(vessel_warnings)

    _update_summary(
        summary_path,
        summary,
        processed_increment=processed,
        issues=errors + warnings,
    )

    return DraftingResult(
        drafts=tuple(drafts),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _resolve_recipients(
    vessel: Mapping[str, Any],
    *,
    default_office_email: str | None,
    errors: list[DraftIssue],
) -> list[str]:
    ship_id = _coerce_text(vessel.get("ship_id"))
    ship_email = _coerce_text(vessel.get("ship_email"))
    office_email = _coerce_text(vessel.get("office_email")) or _coerce_text(default_office_email)

    if not ship_email:
        errors.append(
            DraftIssue(
                vessel_id=ship_id,
                message="Missing required recipient: vessel email address.",
                severity="error",
            )
        )
    if not office_email:
        errors.append(
            DraftIssue(
                vessel_id=ship_id,
                message="Missing required recipient: office email address.",
                severity="error",
            )
        )

    recipients = [email for email in (ship_email, office_email) if email]
    for email in recipients:
        if not _is_valid_email(email):
            errors.append(
                DraftIssue(
                    vessel_id=ship_id,
                    message=f"Invalid email address format: {email}.",
                    severity="error",
                )
            )
    return recipients


def _resolve_html_report(
    report_source: str | Path | None,
    *,
    ship_id: str,
    errors: list[DraftIssue],
) -> str:
    if report_source is None:
        errors.append(
            DraftIssue(
                vessel_id=ship_id,
                message="Missing required HTML report for vessel.",
                severity="error",
            )
        )
        return ""

    if isinstance(report_source, Path):
        return report_source.read_text(encoding="utf-8")

    text = _coerce_text(report_source)
    if not text:
        errors.append(
            DraftIssue(
                vessel_id=ship_id,
                message="HTML report is empty for vessel.",
                severity="error",
            )
        )
        return ""

    candidate = Path(text)
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    return text


def _format_subject(
    template: str,
    vessel: Mapping[str, Any],
    *,
    run_id: str,
    warnings: list[DraftIssue],
) -> str:
    ship_id = _coerce_text(vessel.get("ship_id")) or "UNKNOWN"
    ship_name = _coerce_text(vessel.get("ship_name"))
    if not ship_name:
        warnings.append(
            DraftIssue(
                vessel_id=ship_id,
                message="Missing optional metadata: ship_name.",
                severity="warning",
            )
        )

    values = {
        "SHIPID": ship_id,
        "SHIPNAME": ship_name or ship_id,
        "RUN_ID": run_id,
    }
    formatter = Formatter()
    missing_fields = [
        field_name
        for _, field_name, _, _ in formatter.parse(template)
        if field_name and field_name not in values
    ]
    for field_name in missing_fields:
        warnings.append(
            DraftIssue(
                vessel_id=ship_id,
                message=f"Unknown subject template placeholder: {field_name}.",
                severity="warning",
            )
        )

    return template.format_map(_DefaultDict(values))


def _resolve_attachments(
    ship_id: str,
    *,
    include_pdf: bool,
    pdf_reports: Mapping[str, str | Path] | None,
    warnings: list[DraftIssue],
) -> list[DraftAttachment]:
    attachments: list[DraftAttachment] = []
    if not include_pdf:
        return attachments

    if not pdf_reports or ship_id not in pdf_reports:
        warnings.append(
            DraftIssue(
                vessel_id=ship_id,
                message="Optional PDF attachment not available for vessel.",
                severity="warning",
            )
        )
        return attachments

    pdf_source = pdf_reports[ship_id]
    pdf_path = Path(pdf_source) if not isinstance(pdf_source, Path) else pdf_source
    if not pdf_path.exists():
        warnings.append(
            DraftIssue(
                vessel_id=ship_id,
                message=f"Optional PDF attachment not found at {pdf_path}.",
                severity="warning",
            )
        )
        return attachments

    attachments.append(
        DraftAttachment(
            filename=pdf_path.name,
            content_type="application/pdf",
            data=pdf_path.read_bytes(),
        )
    )
    return attachments


def _build_email_message(
    *,
    to_addresses: Sequence[str],
    subject: str,
    html_body: str,
    attachments: Sequence[DraftAttachment],
    from_email: str | None,
) -> EmailMessage:
    message = EmailMessage()
    message["To"] = ", ".join(to_addresses)
    message["Subject"] = subject
    if from_email:
        message["From"] = from_email
    message.set_content("This message contains an HTML report.")
    message.add_alternative(html_body, subtype="html")

    for attachment in attachments:
        maintype, subtype = attachment.content_type.split("/", 1)
        message.add_attachment(
            attachment.data,
            maintype=maintype,
            subtype=subtype,
            filename=attachment.filename,
        )
    return message


def _format_eml_filename(ship_id: str, ship_name: Any) -> str:
    safe_id = _sanitize_filename(ship_id or "UNKNOWN")
    safe_name = _sanitize_filename(_coerce_text(ship_name))
    if safe_name:
        return f"{safe_id}_{safe_name}.eml"
    return f"{safe_id}.eml"


def _sanitize_filename(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_"))
    return cleaned or "UNKNOWN"


def _is_valid_email(address: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(address.strip()))


def _read_summary(summary_path: Path | str) -> dict[str, Any]:
    path = Path(summary_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "run_id" not in data:
        raise ValueError("summary.json must include run_id.")
    if "errors" not in data or not isinstance(data["errors"], list):
        raise ValueError("summary.json must include an errors list.")
    return data


def _update_summary(
    summary_path: Path | str,
    summary: Mapping[str, Any],
    *,
    processed_increment: int,
    issues: Sequence[DraftIssue],
) -> None:
    updated = dict(summary)
    updated_errors = list(updated.get("errors", []))
    existing_keys = {_summary_key(entry) for entry in updated_errors}

    for issue in issues:
        entry = _issue_to_entry(issue)
        key = _summary_key(entry)
        if key in existing_keys:
            continue
        updated_errors.append(entry)
        existing_keys.add(key)

    updated["errors"] = updated_errors
    if processed_increment:
        updated["vessels_processed"] = int(updated.get("vessels_processed", 0)) + processed_increment

    path = Path(summary_path)
    path.write_text(json.dumps(updated, indent=2), encoding="utf-8")


def _issue_to_entry(issue: DraftIssue) -> dict[str, Any]:
    entry = {
        "phase": EMAIL_PHASE,
        "message": issue.message,
        "severity": issue.severity,
    }
    if issue.vessel_id:
        entry["vessel_id"] = issue.vessel_id
    return entry


def _summary_key(entry: Mapping[str, Any] | Any) -> tuple[str, str, str, str]:
    if not isinstance(entry, Mapping):
        return ("", "", _coerce_text(entry), "")
    return (
        _coerce_text(entry.get("phase")),
        _coerce_text(entry.get("vessel_id")),
        _coerce_text(entry.get("message")),
        _coerce_text(entry.get("severity")),
    )


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


class _DefaultDict(dict[str, str]):
    def __missing__(self, key: str) -> str:  # pragma: no cover - trivial fallback
        return ""
