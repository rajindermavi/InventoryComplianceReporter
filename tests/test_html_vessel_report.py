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
def ok_issues() -> list[IssueRow]:
    return [
        IssueRow(
            ship_id="VESSEL_001",
            ship_name="Ocean Star",
            item="PUB-101",
            item_description="Navigation Charts Vol. 1",
            onboard_edition="1.0",
            current_edition="1.0",
            issue_type=IssueType.OK,
        ),
        IssueRow(
            ship_id="VESSEL_001",
            ship_name="Ocean Star",
            item="PUB-201",
            item_description="Safety Manual",
            onboard_edition="3.0",
            current_edition="3.0",
            issue_type=IssueType.OK,
        ),
    ]

@pytest.fixture
def issues() -> list[IssueRow]:
    return [
        IssueRow(
            ship_id="VESSEL_001",
            ship_name="Ocean Star",
            item="PUB-100",
            item_description="Nautical Almanac",
            onboard_edition="1.0",
            current_edition="2.0",
            issue_type=IssueType.OUTDATED,
        ),
        IssueRow(
            ship_id="VESSEL_001",
            ship_name="Ocean Star",
            item="PUB-200",
            item_description="Tide Tables",
            onboard_edition="",
            current_edition="3.0",
            issue_type=IssueType.MISSING_ONBOARD,
        ),
    ]


def test_render_vessel_report_with_issues(
    vessel_with_discrepancies: dict[str, str],
    issues: list[IssueRow],
    ok_issues: list[IssueRow],
) -> None:
    html = render_vessel_report(
        vessel_with_discrepancies,
        issues,
        ok_issues,
        run_timestamp="2024-05-01 10:30",
    )

    assert "<!doctype html>" in html
    assert "<h1>Inventory Compliance Report</h1>" in html
    assert "Ocean Star" in html
    assert "2024-05-01 10:30" in html
    assert "<table>" in html
    assert "<th>Item</th>" in html
    assert "PUB-100" in html
    assert "1.0" in html
    assert "2.0" in html
    assert "Outdated" in html
    assert "Missing onboard edition" in html
    assert "<h3>Discrepancies</h3>" in html
    assert "<h3>Matches</h3>" in html
    assert "PUB-101" in html
    assert "PUB-201" in html
    assert "No discrepancies found for this vessel." not in html


def test_render_vessel_report_no_issues(
    vessel_without_discrepancies: dict[str, str],
) -> None:
    html = render_vessel_report(
        vessel_without_discrepancies,
        [],
        [],
        run_timestamp="2024-05-02 09:15",
    )

    assert "Calm Seas" in html
    assert "2024-05-02 09:15" in html
    assert "No discrepancies found for this vessel." in html
    assert "<table>" not in html


def test_render_vessel_report_is_deterministic(
    vessel_with_discrepancies: dict[str, str],
    issues: list[IssueRow],
    ok_issues: list[IssueRow],
) -> None:
    html_first = render_vessel_report(
        vessel_with_discrepancies,
        issues,
        ok_issues,
        run_timestamp="2024-05-01 10:30",
    )
    html_second = render_vessel_report(
        vessel_with_discrepancies,
        issues,
        ok_issues,
        run_timestamp="2024-05-01 10:30",
    )

    assert html_first == html_second
