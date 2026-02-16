from icr.backend.domain.compare import compare_inventory
from icr.backend.domain.models import IssueType


def test_compare_inventory_returns_ok_for_matching_editions() -> None:
    result = compare_inventory(
        ship_id="S1",
        onboard_items=[{"item": "Chart A", "onboard_edition": "2025"}],
        reference_items=[{"item": "Chart A", "current_edition": "2025"}],
    )

    assert len(result) == 1
    issue = result[0]
    assert issue.issue_type is IssueType.OK
    assert issue.item == "Chart A"
    assert issue.onboard_edition == "2025"
    assert issue.current_edition == "2025"


def test_compare_inventory_returns_outdated_when_editions_differ() -> None:
    result = compare_inventory(
        ship_id="S1",
        onboard_items=[{"item": "Chart A", "onboard_edition": "2024"}],
        reference_items=[{"item": "Chart A", "current_edition": "2025"}],
    )

    assert [row.issue_type for row in result] == [IssueType.OUTDATED]


def test_compare_inventory_returns_missing_reference_for_onboard_only_item() -> None:
    result = compare_inventory(
        ship_id="S1",
        onboard_items=[{"item": "Chart A", "edition": "2025"}],
        reference_items=[],
    )

    assert [row.issue_type for row in result] == [IssueType.MISSING_REFERENCE]
    assert result[0].current_edition is None


def test_compare_inventory_returns_missing_onboard_when_onboard_edition_empty() -> None:
    result = compare_inventory(
        ship_id="S1",
        onboard_items=[{"item": "Chart A", "onboard_edition": ""}],
        reference_items=[{"item": "Chart A", "current_edition": "2025"}],
    )

    assert [row.issue_type for row in result] == [IssueType.MISSING_ONBOARD]


def test_compare_inventory_deduplicates_identical_ok_rows_by_default() -> None:
    onboard = [
        {"item": "Chart A", "onboard_edition": "2025"},
        {"item": "Chart A", "onboard_edition": "2025"},
    ]
    reference = [{"item": "Chart A", "current_edition": "2025"}]

    result = compare_inventory("S1", onboard, reference)

    assert len(result) == 2
    assert result[0].issue_type is IssueType.OK


def test_compare_inventory_can_disable_deduplication() -> None:
    onboard = [
        {"item": "Chart A", "onboard_edition": "2025"},
        {"item": "Chart A", "onboard_edition": "2025"},
    ]
    reference = [{"item": "Chart A", "current_edition": "2025"}]

    result = compare_inventory("S1", onboard, reference, deduplicate=False)

    assert len(result) == 2
    assert all(row.issue_type is IssueType.OK for row in result)
