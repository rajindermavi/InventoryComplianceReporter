"""Fixtures and helpers for email drafting tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from icr.backend.emailer.draft import EMAIL_PHASE, draft_emails


@pytest.fixture
def office_email() -> str:
    return "compliance@example.com"


@pytest.fixture
def vessel_valid(office_email: str) -> dict[str, str]:
    return {
        "ship_id": "VESSEL_001",
        "ship_name": "Evergreen",
        "ship_email": "vessel@example.com",
        "office_email": office_email,
    }


@pytest.fixture
def vessel_missing_recipient() -> dict[str, str]:
    return {
        "ship_id": "VESSEL_002",
        "ship_name": "Atlas",
        "ship_email": "",
        "office_email": "",
    }


@pytest.fixture
def html_report() -> str:
    return "<html><body><h1>Report</h1></body></html>"


@pytest.fixture
def html_reports_map(vessel_valid: dict[str, str], html_report: str) -> dict[str, str]:
    return {vessel_valid["ship_id"]: html_report}


@pytest.fixture
def pdf_attachment() -> None:
    return None


@pytest.fixture
def summary_data() -> dict[str, object]:
    return {
        "run_id": "20240101_1200",
        "ams_vessels_found": 0,
        "vessels_selected": 0,
        "vessels_processed": 0,
        "vessels_with_issues": 0,
        "total_issue_rows": 0,
        "errors": [],
    }


def write_summary(path: Path, data: dict[str, object]) -> Path:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def read_summary(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def summary_path(tmp_path: Path, summary_data: dict[str, object]) -> Path:
    return write_summary(tmp_path / "summary.json", summary_data)


def test_valid_recipients_generate_draft(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    html_reports_map: dict[str, str],
    summary_path: Path,
    summary_data: dict[str, object],
) -> None:
    """Valid recipients generate a draft and update summary counters."""
    result = draft_emails(
        [vessel_valid],
        html_reports=html_reports_map,
        summary_path=summary_path,
        eml_output_dir=tmp_path / "emls",
    )

    assert len(result.drafts) == 1
    draft = result.drafts[0]
    assert draft.to_addresses == (vessel_valid["ship_email"], vessel_valid["office_email"])
    assert draft.eml_bytes is not None
    header_text = draft.eml_bytes.decode("utf-8", errors="ignore")
    assert "To:" in header_text
    assert vessel_valid["ship_email"] in header_text
    assert vessel_valid["office_email"] in header_text

    summary = read_summary(summary_path)
    assert summary["vessels_processed"] == 1
    assert summary["errors"] == []
    assert summary["run_id"] == summary_data["run_id"]
    assert summary["ams_vessels_found"] == summary_data["ams_vessels_found"]
    assert summary["vessels_selected"] == summary_data["vessels_selected"]
    assert summary["vessels_with_issues"] == summary_data["vessels_with_issues"]
    assert summary["total_issue_rows"] == summary_data["total_issue_rows"]


def test_missing_vessel_email_blocks_draft(
    vessel_missing_recipient: dict[str, str],
    summary_path: Path,
    summary_data: dict[str, object],
) -> None:
    """Missing vessel email blocks drafting and appends validation errors."""
    html_reports = {vessel_missing_recipient["ship_id"]: "<html>report</html>"}

    result = draft_emails(
        [vessel_missing_recipient],
        html_reports=html_reports,
        summary_path=summary_path,
    )

    assert result.drafts == ()
    assert len(result.errors) == 2
    assert result.errors[0].message == "Missing required recipient: vessel email address."
    assert result.errors[1].message == "Missing required recipient: office email address."

    summary = read_summary(summary_path)
    assert summary["vessels_processed"] == 0
    assert summary["run_id"] == summary_data["run_id"]
    assert summary["ams_vessels_found"] == summary_data["ams_vessels_found"]
    assert summary["vessels_selected"] == summary_data["vessels_selected"]
    assert summary["vessels_with_issues"] == summary_data["vessels_with_issues"]
    assert summary["total_issue_rows"] == summary_data["total_issue_rows"]
    assert summary["errors"] == [
        {
            "phase": EMAIL_PHASE,
            "message": "Missing required recipient: vessel email address.",
            "severity": "error",
            "vessel_id": vessel_missing_recipient["ship_id"],
        },
        {
            "phase": EMAIL_PHASE,
            "message": "Missing required recipient: office email address.",
            "severity": "error",
            "vessel_id": vessel_missing_recipient["ship_id"],
        },
    ]


def test_missing_office_email_continues_processing(
    vessel_valid: dict[str, str],
    html_report: str,
    summary_path: Path,
    summary_data: dict[str, object],
) -> None:
    """Missing office email prevents one draft but allows others to proceed."""
    vessel_missing_office = {
        "ship_id": "VESSEL_003",
        "ship_name": "Odyssey",
        "ship_email": "crew@example.com",
        "office_email": "",
    }
    html_reports = {
        vessel_valid["ship_id"]: html_report,
        vessel_missing_office["ship_id"]: html_report,
    }

    result = draft_emails(
        [vessel_missing_office, vessel_valid],
        html_reports=html_reports,
        summary_path=summary_path,
    )

    assert len(result.drafts) == 1
    assert result.drafts[0].vessel_id == vessel_valid["ship_id"]
    assert len(result.errors) == 1
    assert result.errors[0].message == "Missing required recipient: office email address."

    summary = read_summary(summary_path)
    assert summary["vessels_processed"] == 1
    assert summary["run_id"] == summary_data["run_id"]
    assert summary["ams_vessels_found"] == summary_data["ams_vessels_found"]
    assert summary["vessels_selected"] == summary_data["vessels_selected"]
    assert summary["vessels_with_issues"] == summary_data["vessels_with_issues"]
    assert summary["total_issue_rows"] == summary_data["total_issue_rows"]
    assert summary["errors"] == [
        {
            "phase": EMAIL_PHASE,
            "message": "Missing required recipient: office email address.",
            "severity": "error",
            "vessel_id": vessel_missing_office["ship_id"],
        }
    ]


def test_invalid_email_includes_vessel_id_and_preserves_errors(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    summary_data: dict[str, object],
) -> None:
    """Invalid email adds a vessel-scoped error while preserving prior entries."""
    vessel_invalid_email = dict(vessel_valid)
    vessel_invalid_email["ship_email"] = "bad-email"
    html_reports = {vessel_invalid_email["ship_id"]: "<html>report</html>"}

    existing_error = {
        "phase": "reporting",
        "message": "Preexisting issue.",
        "severity": "warning",
    }
    summary_data_with_error = dict(summary_data)
    summary_data_with_error["errors"] = [existing_error]
    summary_path = write_summary(tmp_path / "summary.json", summary_data_with_error)

    result = draft_emails(
        [vessel_invalid_email],
        html_reports=html_reports,
        summary_path=summary_path,
    )

    assert result.drafts == ()
    assert len(result.errors) == 1
    assert result.errors[0].vessel_id == vessel_invalid_email["ship_id"]

    summary = read_summary(summary_path)
    assert summary["vessels_processed"] == 0
    assert summary["errors"][0] == existing_error
    assert summary["errors"][1] == {
        "phase": EMAIL_PHASE,
        "message": "Invalid email address format: bad-email.",
        "severity": "error",
        "vessel_id": vessel_invalid_email["ship_id"],
    }


def test_subject_templating_is_deterministic(
    vessel_valid: dict[str, str],
    html_reports_map: dict[str, str],
    summary_path: Path,
) -> None:
    """Subject templating is deterministic and includes identifiers."""
    subject_template = "Compliance {SHIPID} {RUN_ID}"
    result = draft_emails(
        [vessel_valid],
        html_reports=html_reports_map,
        summary_path=summary_path,
        subject_template=subject_template,
        run_id="RUN_1234",
    )

    assert len(result.drafts) == 1
    draft = result.drafts[0]
    assert draft.subject == "Compliance VESSEL_001 RUN_1234"


def test_html_body_embeds_report_verbatim(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    summary_path: Path,
) -> None:
    """HTML report is embedded verbatim in the draft body and payload."""
    html_report = "<html><body><p>Local Report</p></body></html>"
    result = draft_emails(
        [vessel_valid],
        html_reports={vessel_valid["ship_id"]: html_report},
        summary_path=summary_path,
        eml_output_dir=tmp_path / "emls",
    )

    assert len(result.drafts) == 1
    draft = result.drafts[0]
    assert draft.html_body == html_report
    assert "http://" not in draft.html_body
    assert "https://" not in draft.html_body
    assert draft.eml_bytes is not None
    payload = draft.eml_bytes.decode("utf-8", errors="ignore")
    assert html_report in payload


def test_pdf_attachment_included_when_available(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    html_reports_map: dict[str, str],
    summary_path: Path,
) -> None:
    """PDF attachment is included when provided and no warnings are emitted."""
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")

    result = draft_emails(
        [vessel_valid],
        html_reports=html_reports_map,
        summary_path=summary_path,
        include_pdf=True,
        pdf_reports={vessel_valid["ship_id"]: pdf_path},
    )

    assert len(result.drafts) == 1
    assert result.warnings == ()
    assert len(result.drafts[0].attachments) == 1
    attachment = result.drafts[0].attachments[0]
    assert attachment.filename == "report.pdf"
    assert attachment.content_type == "application/pdf"
    assert attachment.data == b"%PDF-1.4 fake content"


def test_missing_pdf_logs_warning_but_drafts_email(
    vessel_valid: dict[str, str],
    html_reports_map: dict[str, str],
    summary_path: Path,
) -> None:
    """Missing PDF logs a warning while still producing a draft."""
    result = draft_emails(
        [vessel_valid],
        html_reports=html_reports_map,
        summary_path=summary_path,
        include_pdf=True,
        pdf_reports=None,
    )

    assert len(result.drafts) == 1
    assert len(result.warnings) == 1
    assert result.warnings[0].message == "Optional PDF attachment not available for vessel."
    summary = read_summary(summary_path)
    assert summary["errors"] == [
        {
            "phase": EMAIL_PHASE,
            "message": "Optional PDF attachment not available for vessel.",
            "severity": "warning",
            "vessel_id": vessel_valid["ship_id"],
        }
    ]


def test_eml_file_created_with_headers(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    html_reports_map: dict[str, str],
    summary_path: Path,
) -> None:
    """Writing .eml output creates a file with standard headers."""
    eml_dir = tmp_path / "emls"
    result = draft_emails(
        [vessel_valid],
        html_reports=html_reports_map,
        summary_path=summary_path,
        eml_output_dir=eml_dir,
    )

    assert len(result.drafts) == 1
    draft = result.drafts[0]
    assert draft.eml_path is not None
    assert draft.eml_path.exists()
    assert draft.eml_path.parent == eml_dir

    content = draft.eml_path.read_text(encoding="utf-8", errors="ignore")
    assert "To:" in content
    assert "Subject:" in content
    assert "Content-Type:" in content


def test_no_eml_file_when_disabled(
    vessel_valid: dict[str, str],
    html_reports_map: dict[str, str],
    summary_path: Path,
) -> None:
    """Disabling .eml output keeps drafts in memory only."""
    result = draft_emails(
        [vessel_valid],
        html_reports=html_reports_map,
        summary_path=summary_path,
        eml_output_dir=None,
    )

    assert len(result.drafts) == 1
    draft = result.drafts[0]
    assert draft.eml_path is None
    assert draft.eml_bytes is None


def test_summary_increment_semantics(
    vessel_valid: dict[str, str],
    summary_path: Path,
    summary_data: dict[str, object],
) -> None:
    """vessels_processed increments only for successful drafts."""
    vessel_invalid = {
        "ship_id": "VESSEL_010",
        "ship_name": "Orion",
        "ship_email": "",
        "office_email": "ops@example.com",
    }
    html_reports = {
        vessel_valid["ship_id"]: "<html>ok</html>",
        vessel_invalid["ship_id"]: "<html>bad</html>",
    }

    result = draft_emails(
        [vessel_invalid, vessel_valid],
        html_reports=html_reports,
        summary_path=summary_path,
    )

    assert len(result.drafts) == 1
    summary = read_summary(summary_path)
    assert summary["vessels_processed"] == 1
    assert summary["run_id"] == summary_data["run_id"]
    assert summary["ams_vessels_found"] == summary_data["ams_vessels_found"]
    assert summary["vessels_selected"] == summary_data["vessels_selected"]
    assert summary["vessels_with_issues"] == summary_data["vessels_with_issues"]
    assert summary["total_issue_rows"] == summary_data["total_issue_rows"]


def test_summary_errors_appended_and_preserved(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    summary_data: dict[str, object],
) -> None:
    """New drafting errors append without removing existing entries."""
    vessel_invalid = {
        "ship_id": "VESSEL_011",
        "ship_name": "Nova",
        "ship_email": "",
        "office_email": "ops@example.com",
    }
    existing_error = {
        "phase": "reporting",
        "message": "Preexisting issue.",
        "severity": "warning",
    }
    summary_data_with_error = dict(summary_data)
    summary_data_with_error["errors"] = [existing_error]
    summary_path = write_summary(tmp_path / "summary.json", summary_data_with_error)

    result = draft_emails(
        [vessel_invalid, vessel_valid],
        html_reports={
            vessel_invalid["ship_id"]: "<html>bad</html>",
            vessel_valid["ship_id"]: "<html>ok</html>",
        },
        summary_path=summary_path,
    )

    assert len(result.drafts) == 1
    summary = read_summary(summary_path)
    assert summary["errors"][0] == existing_error
    assert summary["errors"][1] == {
        "phase": EMAIL_PHASE,
        "message": "Missing required recipient: vessel email address.",
        "severity": "error",
        "vessel_id": vessel_invalid["ship_id"],
    }


def test_summary_field_preservation_on_update(
    vessel_valid: dict[str, str],
    summary_path: Path,
    summary_data: dict[str, object],
) -> None:
    """Summary updates preserve run_id and domain counters."""
    summary_before = read_summary(summary_path)

    draft_emails(
        [vessel_valid],
        html_reports={vessel_valid["ship_id"]: "<html>ok</html>"},
        summary_path=summary_path,
    )

    summary_after = read_summary(summary_path)
    assert summary_after["run_id"] == summary_before["run_id"]
    assert summary_after["ams_vessels_found"] == summary_before["ams_vessels_found"]
    assert summary_after["vessels_selected"] == summary_before["vessels_selected"]
    assert summary_after["vessels_with_issues"] == summary_before["vessels_with_issues"]
    assert summary_after["total_issue_rows"] == summary_before["total_issue_rows"]
    assert set(summary_after.keys()) == set(summary_before.keys())


def test_summary_update_is_deterministic(
    tmp_path: Path,
    vessel_valid: dict[str, str],
    summary_data: dict[str, object],
) -> None:
    """Identical inputs yield identical summary outputs."""
    html_reports = {vessel_valid["ship_id"]: "<html>ok</html>"}
    summary_path_a = write_summary(tmp_path / "summary_a.json", dict(summary_data))
    summary_path_b = write_summary(tmp_path / "summary_b.json", dict(summary_data))

    draft_emails(
        [vessel_valid],
        html_reports=html_reports,
        summary_path=summary_path_a,
    )
    draft_emails(
        [vessel_valid],
        html_reports=html_reports,
        summary_path=summary_path_b,
    )

    summary_a = read_summary(summary_path_a)
    summary_b = read_summary(summary_path_b)
    assert summary_a == summary_b
