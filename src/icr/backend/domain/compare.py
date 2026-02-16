from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from .models import IssueRow, IssueType

def compare_inventory(
    ship_id: str,
    onboard_items: Iterable[Mapping[str, Any]],
    reference_items: Iterable[Mapping[str, Any]],
    *,
    deduplicate: bool = False,
) -> list[IssueRow]:
    reference_by_item: dict[str, Mapping[str, Any]] = {}
    for idx, record in enumerate(reference_items, start=1):
        item_key = record.get("item")
        if not isinstance(item_key, str) or item_key == "":
            raise ValueError(
                f"Reference row {idx} violates canonical schema: missing/invalid 'item'."
            )
        if item_key not in reference_by_item:
            reference_by_item[item_key] = record

    issues: list[IssueRow] = []
    for record in onboard_items:
        item_key = record.get("item")
        reference_record = reference_by_item.get(item_key)
        current_edition = None if reference_record is None else reference_record.get("current_edition")
        onboard_edition = record.get("onboard_edition") 

        if reference_record is None:
            issues.append(
                IssueRow(
                    ship_id=ship_id,
                    item=item_key,
                    onboard_edition=onboard_edition,
                    current_edition=None,
                    issue_type=IssueType.MISSING_REFERENCE,
                )
            )
            continue

        if onboard_edition is None or onboard_edition == "":

            issues.append(
                IssueRow(
                    ship_id=ship_id,
                    item=item_key,
                    onboard_edition=onboard_edition,
                    current_edition=current_edition,
                    issue_type=IssueType.MISSING_ONBOARD,
                )
            )
            continue

        if current_edition != onboard_edition:
            issues.append(
                IssueRow(
                    ship_id=ship_id,
                    item=item_key,
                    onboard_edition=onboard_edition,
                    current_edition=current_edition,
                    issue_type=IssueType.OUTDATED,
                )
            )
            continue

        issues.append(
            IssueRow(
                ship_id=ship_id,
                item=item_key,
                onboard_edition=onboard_edition,
                current_edition=current_edition,
                issue_type=IssueType.OK,
            )
        )

    if deduplicate:
        return _dedupe_issues(issues)
    return issues


def _dedupe_issues(issues: list[IssueRow]) -> list[IssueRow]:
    seen: set[tuple[str, Optional[str], IssueType]] = set()
    deduped: list[IssueRow] = []
    for issue in issues:
        key = (issue.item, issue.onboard_edition, issue.issue_type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped
