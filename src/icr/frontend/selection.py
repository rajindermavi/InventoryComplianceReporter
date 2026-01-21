"""Vessel selection interaction logic."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar

from icr.frontend import messages

VesselT = TypeVar("VesselT")


class SelectionIO(Protocol):
    """UI-agnostic interface for vessel selection prompts."""

    def display(self, message: str) -> None:
        """Display a message to the user."""

    def prompt(self, message: str) -> str:
        """Prompt the user and return the response."""


def select_vessels(
    vessels: Sequence[VesselT],
    io: SelectionIO,
    *,
    get_vessel_id: Callable[[VesselT], str] | None = None,
    get_vessel_label: Callable[[VesselT], str] | None = None,
) -> list[str]:
    """Return the selected vessel identifiers based on user interaction."""

    vessel_list = list(vessels)
    if not vessel_list:
        io.display(messages.SELECTION["no_vessels"])
        return []

    id_getter = get_vessel_id or _default_vessel_id
    label_getter = get_vessel_label or _default_vessel_label
    vessel_ids = [id_getter(vessel) for vessel in vessel_list]
    vessel_labels = [label_getter(vessel) for vessel in vessel_list]
    selected_ids: set[str] = set()

    while True:
        _display_selection(
            io,
            vessel_ids=vessel_ids,
            vessel_labels=vessel_labels,
            selected_ids=selected_ids,
        )
        action = io.prompt(messages.SELECTION["prompt_action"]).strip().lower()
        if action in {"a", "all"}:
            selected_ids = set(vessel_ids)
            continue
        if action in {"n", "none"}:
            selected_ids.clear()
            continue
        if action in {"t", "toggle"}:
            selected_ids = _handle_toggle(io, vessel_ids, selected_ids)
            continue
        if action in {"d", "done"}:
            break
        io.display(messages.SELECTION["invalid_action"])

    return [vessel_id for vessel_id in vessel_ids if vessel_id in selected_ids]


def _handle_toggle(io: SelectionIO, vessel_ids: list[str], selected_ids: set[str]) -> set[str]:
    vessel_id = io.prompt(messages.SELECTION["prompt_toggle"]).strip()
    if vessel_id not in vessel_ids:
        io.display(messages.SELECTION["invalid_toggle"].format(vessel_id=vessel_id))
        return selected_ids
    updated = set(selected_ids)
    if vessel_id in updated:
        updated.remove(vessel_id)
    else:
        updated.add(vessel_id)
    return updated


def _display_selection(
    io: SelectionIO,
    *,
    vessel_ids: list[str],
    vessel_labels: list[str],
    selected_ids: set[str],
) -> None:
    io.display(messages.SELECTION["title"])
    io.display(messages.SELECTION["instructions"])
    io.display(messages.SELECTION["list_header"])
    for vessel_id, vessel_label in zip(vessel_ids, vessel_labels, strict=False):
        io.display(
            messages.SELECTION["list_item"].format(
                identifier=vessel_id,
                label=vessel_label,
            )
        )
    io.display(
        messages.SELECTION["selected_count"].format(
            selected_count=len(selected_ids),
            total_count=len(vessel_ids),
        )
    )
    io.display(messages.SELECTION["options_header"])
    io.display(messages.SELECTION["option_all"])
    io.display(messages.SELECTION["option_none"])
    io.display(messages.SELECTION["option_toggle"])
    io.display(messages.SELECTION["option_done"])


def _default_vessel_id(vessel: VesselT) -> str:
    return str(vessel)


def _default_vessel_label(vessel: VesselT) -> str:
    return str(vessel)
