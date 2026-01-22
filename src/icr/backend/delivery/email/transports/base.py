"""Base transport contracts for Phase 7B."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TransportResult:
    """Result of a transport send attempt."""

    success: bool
    provider_message_id: str | None
    error: str | None


class EmailTransport(Protocol):
    """Minimal transport interface.

    Implementations must treat .eml files as opaque bytes and never modify
    or parse their contents.
    """

    name: str

    def send(self, eml_path: Path) -> TransportResult: ...
