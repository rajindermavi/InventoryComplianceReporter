import importlib

from icr.frontend import messages


def _iter_message_values(value: object):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _iter_message_values(item)
        return
    raise AssertionError(f"Unexpected message container type: {type(value)!r}")


def test_messages_are_strings_and_non_empty() -> None:
    for name, value in vars(messages).items():
        if name.startswith("_"):
            continue
        assert not callable(value)
        assert isinstance(value, (str, dict))
        for message in _iter_message_values(value):
            assert isinstance(message, str)
            assert message.strip()


def test_messages_have_no_callables() -> None:
    for name, value in vars(messages).items():
        if name.startswith("_"):
            continue
        assert not callable(value)


def test_messages_import_has_no_side_effects(capsys) -> None:
    snapshot = {
        name: value
        for name, value in vars(messages).items()
        if not name.startswith("_")
    }

    importlib.reload(messages)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    reloaded = {
        name: value
        for name, value in vars(messages).items()
        if not name.startswith("_")
    }
    assert reloaded == snapshot
