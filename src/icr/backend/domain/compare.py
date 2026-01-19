from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from .models import IssueRow, IssueType


def normalize_edition(edition: Optional[str], *, case_fold: bool) -> Optional[str]:
    if edition is None:
        return None
    text = edition if isinstance(edition, str) else str(edition)
    normalized = " ".join(text.strip().split())
    if case_fold:
        normalized = normalized.casefold()
    return normalized


def compare_inventory(
    ship_id: str,
    onboard_items: Iterable[Mapping[str, Any]],
    reference_items: Iterable[Mapping[str, Any]],
    *,
    case_fold_items: bool = True,
    case_fold_editions: bool = False,
    deduplicate: bool = True,
) -> list[IssueRow]:
    reference_by_item: dict[str, Mapping[str, Any]] = {}
    for record in reference_items:
        item_key = _normalize_item(record.get("item"), case_fold=case_fold_items)
        if not item_key:
            continue
        if item_key not in reference_by_item:
            reference_by_item[item_key] = record

    issues: list[IssueRow] = []
    for record in onboard_items:
        raw_item = record.get("item")
        display_item = _clean_item(raw_item)
        item_key = _normalize_item(raw_item, case_fold=case_fold_items)
        reference_record = reference_by_item.get(item_key)

        onboard_edition = _extract_edition(record, prefer_keys=("onboard_edition", "edition"))
        normalized_onboard = normalize_edition(onboard_edition, case_fold=case_fold_editions)

        if normalized_onboard is None or normalized_onboard == "":
            current_edition = None
            if reference_record is not None:
                current_edition = _extract_edition(
                    reference_record, prefer_keys=("current_edition", "edition")
                )
            issues.append(
                IssueRow(
                    ship_id=ship_id,
                    item=display_item,
                    onboard_edition=onboard_edition,
                    current_edition=current_edition,
                    issue_type=IssueType.MISSING_ONBOARD,
                )
            )
            continue

        if reference_record is None:
            issues.append(
                IssueRow(
                    ship_id=ship_id,
                    item=display_item,
                    onboard_edition=onboard_edition,
                    current_edition=None,
                    issue_type=IssueType.MISSING_REFERENCE,
                )
            )
            continue

        current_edition = _extract_edition(
            reference_record, prefer_keys=("current_edition", "edition")
        )
        normalized_current = normalize_edition(current_edition, case_fold=case_fold_editions)
        if normalized_current != normalized_onboard:
            issues.append(
                IssueRow(
                    ship_id=ship_id,
                    item=display_item,
                    onboard_edition=onboard_edition,
                    current_edition=current_edition,
                    issue_type=IssueType.OUTDATED,
                )
            )

    if deduplicate:
        return _dedupe_issues(issues)
    return issues


def _normalize_item(item: Optional[str], *, case_fold: bool) -> str:
    text = "" if item is None else (item if isinstance(item, str) else str(item))
    normalized = text.strip()
    if case_fold:
        normalized = normalized.casefold()
    return normalized


def _clean_item(item: Optional[str]) -> str:
    text = "" if item is None else (item if isinstance(item, str) else str(item))
    return text.strip()


def _extract_edition(
    record: Mapping[str, Any], *, prefer_keys: tuple[str, ...]
) -> Optional[str]:
    for key in prefer_keys:
        if key in record:
            value = record.get(key)
            if value is None:
                return None
            return value if isinstance(value, str) else str(value)
    return None


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
