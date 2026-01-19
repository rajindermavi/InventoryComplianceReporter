import pytest

from icr.backend.domain.models import IssueRow, IssueType
from icr.backend.reporting.html import render_vessel_report


@pytest.fixture
def vessel_with_discrepancies() -> dict[str, str]:
    return {"ship_id": "VESSEL_001", "ship_name": "Ocean Star"}


@pytest.fixture
def vessel_without_discrepancies() -> dict[str, str]:
    return {"ship_id": "VESSEL_002", "ship_name": "Calm Seas"}


@pytest.fixture
def issues() -> list[IssueRow]:
    return [
        IssueRow(
            ship_id="VESSEL_001",
            item="PUB-100",
            onboard_edition="1.0",
            current_edition="2.0",
            issue_type=IssueType.OUTDATED,
        ),
        IssueRow(
            ship_id="VESSEL_001",
            item="PUB-200",
            onboard_edition="",
            current_edition="3.0",
            issue_type=IssueType.MISSING_ONBOARD,
        ),
    ]


def test_render_vessel_report_with_issues(
    vessel_with_discrepancies: dict[str, str], issues: list[IssueRow]
) -> None:
    html = render_vessel_report(
        vessel_with_discrepancies,
        issues,
        run_timestamp="2024-05-01 10:30",
        source_files=["index.xlsx", "inventory.xlsx", "ic.xlsx"],
    )

    assert "<!doctype html>" in html
    assert "<h1>Inventory Compliance Report</h1>" in html
    assert "VESSEL_001 - Ocean Star" in html
    assert "2024-05-01 10:30" in html
    assert "index.xlsx" in html
    assert "inventory.xlsx" in html
    assert "ic.xlsx" in html
    assert "<table>" in html
    assert "<th>Item</th>" in html
    assert "PUB-100" in html
    assert "1.0" in html
    assert "2.0" in html
    assert "Outdated" in html
    assert "Missing onboard edition" in html
    assert "No issues found for this vessel." not in html


def test_render_vessel_report_no_issues(
    vessel_without_discrepancies: dict[str, str]
) -> None:
    html = render_vessel_report(
        vessel_without_discrepancies,
        [],
        run_timestamp="2024-05-02 09:15",
        source_files=["index.xlsx"],
    )

    assert "VESSEL_002 - Calm Seas" in html
    assert "2024-05-02 09:15" in html
    assert "index.xlsx" in html
    assert "No issues found for this vessel." in html
    assert "<table>" not in html


def test_render_vessel_report_is_deterministic(
    vessel_with_discrepancies: dict[str, str], issues: list[IssueRow]
) -> None:
    html_first = render_vessel_report(
        vessel_with_discrepancies,
        issues,
        run_timestamp="2024-05-01 10:30",
        source_files=["index.xlsx", "inventory.xlsx", "ic.xlsx"],
    )
    html_second = render_vessel_report(
        vessel_with_discrepancies,
        issues,
        run_timestamp="2024-05-01 10:30",
        source_files=["index.xlsx", "inventory.xlsx", "ic.xlsx"],
    )

    assert html_first == html_second
