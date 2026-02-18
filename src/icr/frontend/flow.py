"""Frontend workflow orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
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


class AppFlow:
    """Step-by-step frontend workflow usable by both GUI and console."""

    def __init__(
        self,
        *,
        backend: Any | None = None,
        io: FrontendIO | None = None,
        get_vessel_id: Callable[[Any], str] | None = None,
        get_vessel_label: Callable[[Any], str] | None = None,
    ) -> None:
        self._backend = backend or icr.backend
        self._io = io or ConsoleIO()
        self._get_vessel_id = get_vessel_id
        self._get_vessel_label = get_vessel_label
        self._vessels: list[Mapping[str, Any]] = []

    def initialize(
        self,
        ic_inventory: Any,
        vessels_index: Any,
        vessels_inventory: Any,
    ) -> bool:
        """Initialize the backend with input file paths.

        Returns True on success, False on failure (error already displayed).
        """
        try:
            self._backend.initialize_workflow(
                ic_inventory=ic_inventory,
                vessels_index=vessels_index,
                vessels_inventory=vessels_inventory,
            )
            return True
        except Exception:
            _display_error(self._io, messages.ERRORS["initialization_failure"])
            return False

    def fetch_vessels(self) -> list[Mapping[str, Any]] | None:
        """Discover AMS vessels via the backend.

        Returns the vessel list on success, None on failure (error already displayed).
        Stores the result internally for use by run().
        """
        self._io.display(messages.PROGRESS["discovering_vessels"])
        vessels = _call_backend_with_result(
            self._io,
            self._backend.discover_ams_vessels,
            messages.ERRORS["discover_vessels"],
        )
        if vessels is not None:
            self._vessels = vessels
        return vessels

    def process(self, vessel_ids: Sequence[str]) -> Mapping[str, Any] | None:
        """Process the selected vessels via the backend.

        Intended to be called from a background thread when used in a GUI.
        Returns the summary mapping on success, None on failure (error already displayed).
        """
        self._io.display(messages.PROGRESS["processing"])
        summary = _call_backend_with_result(
            self._io,
            lambda: self._backend.process_vessels(vessel_ids),
            messages.ERRORS["processing"],
        )
        if summary is not None:
            self._io.display(messages.COMPLETION["success"])
            _display_summary(self._io, summary)
        return summary

    def list_runs(self) -> list[Mapping[str, Any]]:
        """List all past runs."""
        return self._backend.list_runs()

    def export_run(self, run_id: str, export_folder: str | Path) -> None:
        """Export a specific run to the given folder."""
        self._backend.export_run(run_id, export_folder)

    def export_current_run(self, export_folder: str | Path) -> None:
        """Export the current run to the given folder."""
        self._backend.export_current_run(export_folder)

    def purge_run(self, run_id: str) -> None:
        """Purge a specific run."""
        self._backend.purge_run(run_id)

    def purge_all_runs(self) -> None:
        """Purge all past runs."""
        self._backend.purge_all_runs()

    def run(self) -> None:
        """Run the complete linear workflow.

        Chains initialize (if available), fetch, select, confirm, and process
        in sequence. Suitable for console use.
        """
        try:
            if not _has_callable(self._backend, "discover_ams_vessels") or not _has_callable(
                self._backend, "process_vessels"
            ):
                _display_error(self._io, messages.ERRORS["backend_unavailable"])
                return

            self._io.display(messages.WELCOME["title"])
            self._io.display(messages.WELCOME["body"])

            input_check = _get_callable(
                self._backend,
                ("confirm_inputs", "validate_inputs", "validate_input_files"),
            )
            if input_check is not None:
                self._io.display(messages.PROGRESS["validating_inputs"])
                if not _call_backend(self._io, input_check, messages.ERRORS["input_validation"]):
                    return

            vessels = self.fetch_vessels()
            if vessels is None:
                return
            if not vessels:
                self._io.display(messages.SELECTION["no_vessels"])
                return

            selected_ids = selection.select_vessels(
                vessels,
                self._io,
                get_vessel_id=self._get_vessel_id,
                get_vessel_label=self._get_vessel_label,
            )
            if not selected_ids:
                self._io.display(messages.STATUS["selection_empty"])
                return

            confirm_prompt = messages.PROMPTS["confirm_selection"].format(count=len(selected_ids))
            if not self._io.confirm(confirm_prompt):
                self._io.display(messages.STATUS["selection_cancelled"])
                return

            self.process(selected_ids)
        except Exception:
            _display_error(self._io, messages.ERRORS["unexpected"])


def run_flow(
    *,
    backend: Any | None = None,
    io: FrontendIO | None = None,
    get_vessel_id: Callable[[VesselT], str] | None = None,
    get_vessel_label: Callable[[VesselT], str] | None = None,
) -> None:
    """Run the linear frontend workflow."""
    AppFlow(
        backend=backend,
        io=io,
        get_vessel_id=get_vessel_id,
        get_vessel_label=get_vessel_label,
    ).run()


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
