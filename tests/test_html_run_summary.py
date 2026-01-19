import pytest

from icr.backend.reporting.html import render_run_summary


@pytest.fixture
def run_with_multiple_vessels() -> list[dict[str, object]]:
    return [
        {
            "ship_id": "VESSEL_001",
            "ship_name": "Ocean Star",
            "issue_count": 2,
            "report_filename": "VESSEL_001.html",
        },
        {
            "ship_id": "VESSEL_002",
            "ship_name": "Calm Seas",
            "issue_count": 0,
            "report_filename": "VESSEL_002.html",
        },
    ]


@pytest.fixture
def run_with_no_issues() -> list[dict[str, object]]:
    return [
        {
            "ship_id": "VESSEL_003",
            "ship_name": "Still Waters",
            "issue_count": 0,
            "report_filename": "VESSEL_003.html",
        }
    ]


def test_render_run_summary_multiple_vessels(
    run_with_multiple_vessels: list[dict[str, object]],
) -> None:
    html = render_run_summary(run_with_multiple_vessels, run_timestamp="2024-05-03 14:00")

    assert "<!doctype html>" in html
    assert "<h1>Run Summary</h1>" in html
    assert "2024-05-03 14:00" in html
    assert "Vessels processed:</strong> 2" in html
    assert "Vessels with issues:</strong> 1" in html
    assert "Vessels with no issues:</strong> 1" in html
    assert "VESSEL_001 - Ocean Star" in html
    assert "VESSEL_002 - Calm Seas" in html
    assert "VESSEL_001.html" in html
    assert "VESSEL_002.html" in html


def test_render_run_summary_no_issues(
    run_with_no_issues: list[dict[str, object]],
) -> None:
    html = render_run_summary(run_with_no_issues, run_timestamp="2024-05-04 08:10")

    assert "Vessels processed:</strong> 1" in html
    assert "Vessels with issues:</strong> 0" in html
    assert "Vessels with no issues:</strong> 1" in html
    assert "VESSEL_003 - Still Waters" in html
    assert any(
        token in html
        for token in (
            "No issues detected",
            "Vessels with issues:</strong> 0",
        )
    )


def test_render_run_summary_no_vessels() -> None:
    html = render_run_summary([], run_timestamp="2024-05-05 07:00")

    assert "Vessels processed:</strong> 0" in html
    assert "No vessels processed." in html


def test_render_run_summary_is_deterministic(
    run_with_multiple_vessels: list[dict[str, object]],
) -> None:
    first = render_run_summary(run_with_multiple_vessels, run_timestamp="2024-05-03 14:00")
    second = render_run_summary(run_with_multiple_vessels, run_timestamp="2024-05-03 14:00")

    assert first == second
