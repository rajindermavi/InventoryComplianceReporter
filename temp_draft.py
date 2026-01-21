from __future__ import annotations

import json
from pathlib import Path

from src.icr.backend.emailer.draft import EMAIL_PHASE, draft_emails


def read_summary(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))

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

def missing_vessel_email_blocks_draft(
    vessel_missing_recipient: dict[str, str],
    summary_path: Path,
    summary_data: dict[str, object],
) -> None:
    html_reports = {vessel_missing_recipient["ship_id"]: "<html>report</html>"}

    result = draft_emails(
        [vessel_missing_recipient],
        html_reports=html_reports,
        summary_path=summary_path,
    )

    print(result)

    assert result.drafts == ()
    assert len(result.errors) == 1
    assert result.errors[0].message == "Missing required recipient: vessel email address."

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
        }
    ]


if __name__ == '__main__':
    missing_vessel_email_blocks_draft(
        {
        "ship_id": "VESSEL_002",
        "ship_name": "Atlas",
        "ship_email": "",
        "office_email": "",
    },
    write_summary(Path('') / "summary.json", summary_data()),
    summary_data()
    )