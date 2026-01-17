"""Frontend workflow orchestration placeholders."""

from icr.frontend import messages, selection


def run_flow() -> None:
    """
    Orchestrate the application flow.

    Implementation deferred to Phase 6.
    """
    steps = [
        (messages.get_welcome_message, ()),
        (messages.get_input_prompt, ()),
        (selection.select_all, ([],)),
        (selection.select_none, ([],)),
        (selection.toggle_vessel, ([], "")),
        (messages.get_confirmation_prompt, ()),
        (messages.get_completion_message, ()),
    ]

    for step, args in steps:
        try:
            step(*args)
        except NotImplementedError:
            pass

    raise NotImplementedError("Implemented in Phase 6")
