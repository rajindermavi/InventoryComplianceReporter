"""Delivery-layer models for Phase 7B."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailDeliveryPlan:
    """User-directed delivery intent for a single run."""

    send_now: bool
    confirm_send: bool
    transport: str | None
    transport_config: object | None = None


@dataclass(frozen=True)
class EmailDeliveryResult:
    """Per-vessel email delivery outcome."""

    vessel_id: str
    status: str
    reason: str | None
    transport: str | None
    provider_message_id: str | None
