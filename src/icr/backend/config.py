"""Minimal hardcoded configuration for Phase 1 testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AMSRule:
    source_column: str = "note2"
    match_type: Literal["contains"] = "contains"
    match_value: str = "AMS"


@dataclass(frozen=True)
class EmailConfig:
    default_office_email: str | None = None
    subject_template: str = "Inventory Compliance - {SHIPNAME}"
    from_email: str = "compliance@example.com"
    include_pdf: bool = False


@dataclass(frozen=True)
class Config:
    ams_rule: AMSRule
    email: EmailConfig


def get_config() -> Config:
    """Return hardcoded configuration."""
    return Config(
        ams_rule=AMSRule(),
        email=EmailConfig(),
    )