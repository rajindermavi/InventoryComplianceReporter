from unittest.mock import Mock, call, patch

from icr.frontend import flow, messages


def _make_io(confirm_responses: list[bool]) -> Mock:
    io = Mock()
    io.display = Mock()
    io.prompt = Mock()
    io.confirm = Mock(side_effect=confirm_responses)
    return io


def _make_backend() -> Mock:
    backend = Mock()
    backend.confirm_inputs = Mock()
    backend.discover_ams_vessels = Mock(return_value=[{"ship_id": "SHIP123"}])
    backend.process_vessels = Mock(return_value={"vessels_processed": 1})
    return backend


def test_flow_happy_path() -> None:
    backend = _make_backend()
    io = _make_io([True])

    with patch("icr.frontend.flow.selection.select_vessels", return_value=["SHIP123"]) as selector:
        flow.run_flow(backend=backend, io=io, get_vessel_id=lambda vessel: vessel["ship_id"])

    io.display.assert_any_call(messages.WELCOME["title"])
    io.display.assert_any_call(messages.WELCOME["body"])
    io.display.assert_any_call(messages.COMPLETION["success"])
    io.confirm.assert_called_once_with(messages.PROMPTS["confirm_selection"].format(count=1))
    assert backend.mock_calls[:3] == [
        call.confirm_inputs(),
        call.discover_ams_vessels(),
        call.process_vessels(["SHIP123"]),
    ]
    selector.assert_called_once()
    args, kwargs = selector.call_args
    assert args[0] == backend.discover_ams_vessels.return_value
    assert args[1] is io
    assert kwargs["get_vessel_id"] is not None
    assert kwargs["get_vessel_label"] is None


def test_flow_user_cancels_confirmation() -> None:
    backend = _make_backend()
    io = _make_io([False])

    with patch("icr.frontend.flow.selection.select_vessels", return_value=["SHIP123"]):
        flow.run_flow(backend=backend, io=io)

    io.confirm.assert_called_once_with(messages.PROMPTS["confirm_selection"].format(count=1))
    backend.process_vessels.assert_not_called()
    io.display.assert_any_call(messages.STATUS["selection_cancelled"])


def test_flow_no_ams_vessels_skips_selection() -> None:
    backend = _make_backend()
    backend.discover_ams_vessels.return_value = []
    io = _make_io([True])

    with patch("icr.frontend.flow.selection.select_vessels") as selector:
        flow.run_flow(backend=backend, io=io)

    selector.assert_not_called()
    io.display.assert_any_call(messages.SELECTION["no_vessels"])
    io.confirm.assert_not_called()
    backend.process_vessels.assert_not_called()


def test_flow_discovery_error_shows_message() -> None:
    backend = _make_backend()
    backend.discover_ams_vessels.side_effect = RuntimeError("boom")
    io = _make_io([])

    with patch("icr.frontend.flow.selection.select_vessels") as selector:
        flow.run_flow(backend=backend, io=io)

    selector.assert_not_called()
    backend.process_vessels.assert_not_called()
    io.confirm.assert_not_called()
    io.display.assert_any_call(messages.ERRORS["discover_vessels"]["title"])


def test_flow_processing_error_shows_message() -> None:
    backend = _make_backend()
    backend.process_vessels.side_effect = RuntimeError("boom")
    io = _make_io([True])

    with patch("icr.frontend.flow.selection.select_vessels", return_value=["SHIP123"]):
        flow.run_flow(backend=backend, io=io)

    backend.process_vessels.assert_called_once_with(["SHIP123"])
    io.confirm.assert_called_once_with(messages.PROMPTS["confirm_selection"].format(count=1))
    io.display.assert_any_call(messages.ERRORS["processing"]["title"])


def test_flow_missing_backend_functions() -> None:
    backend = Mock()
    backend.discover_ams_vessels = None
    backend.process_vessels = None
    io = _make_io([])

    flow.run_flow(backend=backend, io=io)

    io.display.assert_any_call(messages.ERRORS["backend_unavailable"]["title"])
