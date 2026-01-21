"""Frontend workflow orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol, TypeVar

import icr.backend
from icr.frontend import messages, selection

VesselT = TypeVar("VesselT")


class FrontendIO(Protocol):
    """UI-agnostic IO surface for the frontend workflow."""

    def display(self, message: str) -> None:
        """Display a message to the user."""

    def prompt(self, message: str) -> str:
        """Prompt the user and return the response."""

    def confirm(self, message: str) -> bool:
        """Prompt for confirmation and return the response."""


class ConsoleIO:
    """Terminal-based IO implementation for the frontend."""

    def display(self, message: str) -> None:
        print(message)

    def prompt(self, message: str) -> str:
        return input(message)

    def confirm(self, message: str) -> bool:
        while True:
            response = self.prompt(message).strip().lower()
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            self.display(messages.PROMPTS["confirm_retry"])


def run_flow(
    *,
    backend: Any | None = None,
    io: FrontendIO | None = None,
    get_vessel_id: Callable[[VesselT], str] | None = None,
    get_vessel_label: Callable[[VesselT], str] | None = None,
) -> None:
    """Run the linear frontend workflow."""

    resolved_io = io or ConsoleIO()
    resolved_backend = backend or icr.backend

    try:
        if not _has_callable(resolved_backend, "discover_ams_vessels") or not _has_callable(
            resolved_backend, "process_vessels"
        ):
            _display_error(resolved_io, messages.ERRORS["backend_unavailable"])
            return

        resolved_io.display(messages.WELCOME["title"])
        resolved_io.display(messages.WELCOME["body"])

        input_check = _get_callable(
            resolved_backend,
            ("confirm_inputs", "validate_inputs", "validate_input_files"),
        )
        if input_check is not None:
            resolved_io.display(messages.PROGRESS["validating_inputs"])
            if not _call_backend(resolved_io, input_check, messages.ERRORS["input_validation"]):
                return

        resolved_io.display(messages.PROGRESS["discovering_vessels"])
        vessels = _call_backend_with_result(
            resolved_io,
            resolved_backend.discover_ams_vessels,
            messages.ERRORS["discover_vessels"],
        )
        if vessels is None:
            return
        if not vessels:
            resolved_io.display(messages.SELECTION["no_vessels"])
            return

        selected_ids = selection.select_vessels(
            vessels,
            resolved_io,
            get_vessel_id=get_vessel_id,
            get_vessel_label=get_vessel_label,
        )
        if not selected_ids:
            resolved_io.display(messages.STATUS["selection_empty"])
            return

        confirm_prompt = messages.PROMPTS["confirm_selection"].format(count=len(selected_ids))
        if not resolved_io.confirm(confirm_prompt):
            resolved_io.display(messages.STATUS["selection_cancelled"])
            return

        resolved_io.display(messages.PROGRESS["processing"])
        summary = _call_backend_with_result(
            resolved_io,
            lambda: resolved_backend.process_vessels(selected_ids),
            messages.ERRORS["processing"],
        )
        if summary is None:
            return

        resolved_io.display(messages.COMPLETION["success"])
        _display_summary(resolved_io, summary)
    except Exception:
        _display_error(resolved_io, messages.ERRORS["unexpected"])


def _display_summary(io: FrontendIO, summary: object) -> None:
    if not isinstance(summary, Mapping):
        return
    if "run_id" in summary:
        io.display(messages.COMPLETION["run_id"].format(run_id=summary["run_id"]))
    if "vessels_processed" in summary:
        io.display(
            messages.COMPLETION["vessels_processed"].format(
                vessels_processed=summary["vessels_processed"],
            )
        )
    if "vessels_with_issues" in summary:
        io.display(
            messages.COMPLETION["vessels_with_issues"].format(
                vessels_with_issues=summary["vessels_with_issues"],
            )
        )
    if "total_issue_rows" in summary:
        io.display(
            messages.COMPLETION["total_issue_rows"].format(
                total_issue_rows=summary["total_issue_rows"],
            )
        )


def _display_error(io: FrontendIO, error: Mapping[str, str]) -> None:
    io.display(error["title"])
    io.display(error["body"])
    io.display(error["next_step"])


def _call_backend(
    io: FrontendIO,
    func: Callable[[], Any],
    error: Mapping[str, str],
) -> bool:
    try:
        func()
    except Exception:
        _display_error(io, error)
        return False
    return True


def _call_backend_with_result(
    io: FrontendIO,
    func: Callable[[], VesselT],
    error: Mapping[str, str],
) -> VesselT | None:
    try:
        return func()
    except Exception:
        _display_error(io, error)
        return None


def _has_callable(backend: Any, name: str) -> bool:
    return callable(getattr(backend, name, None))


def _get_callable(backend: Any, names: Sequence[str]) -> Callable[[], Any] | None:
    for name in names:
        if callable(getattr(backend, name, None)):
            return getattr(backend, name)
    return None
