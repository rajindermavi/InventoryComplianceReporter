from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IssueType(Enum):
    """Classification for inventory compliance issues."""
    
    OK = "OK"
    OUTDATED = "OUTDATED"
    MISSING_ONBOARD = "MISSING_ONBOARD"
    MISSING_REFERENCE = "MISSING_REFERENCE"


@dataclass(frozen=True)
class IssueRow:
    """Domain record representing a single compliance issue."""

    ship_id: str
    ship_name: Optional[str]
    item: str
    item_description: Optional[str]
    onboard_edition: Optional[str]
    current_edition: Optional[str]
    issue_type: IssueType
