from unittest.mock import Mock

from icr.frontend import messages, selection


def _make_vessels() -> list[dict[str, str]]:
    return [
        {"ship_id": "SHIP123", "name": "Example Vessel"},
        {"ship_id": "SHIP456", "name": "Second Vessel"},
        {"ship_id": "SHIP789", "name": "Third Vessel"},
    ]


def _make_io(responses: list[str]) -> Mock:
    io = Mock()
    io.display = Mock()
    io.prompt = Mock(side_effect=responses)
    return io


def test_select_vessels_all() -> None:
    vessels = _make_vessels()
    io = _make_io(["a", "d"])

    selected = selection.select_vessels(
        vessels,
        io,
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert selected == ["SHIP123", "SHIP456", "SHIP789"]


def test_select_vessels_none() -> None:
    vessels = _make_vessels()
    io = _make_io(["n", "d"])

    selected = selection.select_vessels(
        vessels,
        io,
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert selected == []


def test_select_vessels_subset() -> None:
    vessels = _make_vessels()
    io = _make_io(["t", "SHIP456", "d"])

    selected = selection.select_vessels(
        vessels,
        io,
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert selected == ["SHIP456"]


def test_select_vessels_deterministic() -> None:
    vessels = _make_vessels()

    selected_first = selection.select_vessels(
        vessels,
        _make_io(["t", "SHIP123", "t", "SHIP789", "d"]),
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )
    selected_second = selection.select_vessels(
        vessels,
        _make_io(["t", "SHIP123", "t", "SHIP789", "d"]),
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert selected_first == selected_second


def test_select_vessels_no_mutation() -> None:
    vessels = _make_vessels()
    snapshot = [dict(vessel) for vessel in vessels]
    io = _make_io(["a", "d"])

    selection.select_vessels(
        vessels,
        io,
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert vessels == snapshot


def test_select_vessels_output_is_identifiers() -> None:
    vessels = _make_vessels()
    io = _make_io(["t", "SHIP123", "d"])

    selected = selection.select_vessels(
        vessels,
        io,
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert selected == ["SHIP123"]


def test_select_vessels_no_results_message() -> None:
    io = _make_io([])

    selected = selection.select_vessels(
        [],
        io,
        get_vessel_id=lambda vessel: vessel["ship_id"],
        get_vessel_label=lambda vessel: vessel["name"],
    )

    assert selected == []
    io.display.assert_any_call(messages.SELECTION["no_vessels"])
