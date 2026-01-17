"""User-facing message placeholders."""

WELCOME_TITLE = "Inventory Compliance Reporter"
WELCOME_BODY = "Welcome to the Inventory Compliance Reporter."
INPUT_PROMPT = "Provide required input locations."
SELECTION_PROMPT = "Select vessels to include in this run."
CONFIRMATION_PROMPT = "Confirm the selection and continue."
COMPLETION_MESSAGE = "Processing complete."
FATAL_ERROR_MESSAGE = "An unexpected error occurred."


def get_welcome_message() -> str:
    """
    Retrieve the welcome message shown at startup.

    Implementation deferred to Phase 6.
    """
    raise NotImplementedError("Implemented in Phase 6")


def get_input_prompt() -> str:
    """
    Retrieve the input discovery prompt.

    Implementation deferred to Phase 6.
    """
    raise NotImplementedError("Implemented in Phase 6")


def get_selection_prompt() -> str:
    """
    Retrieve the vessel selection prompt.

    Implementation deferred to Phase 6.
    """
    raise NotImplementedError("Implemented in Phase 6")


def get_confirmation_prompt() -> str:
    """
    Retrieve the user confirmation prompt.

    Implementation deferred to Phase 6.
    """
    raise NotImplementedError("Implemented in Phase 6")


def get_completion_message() -> str:
    """
    Retrieve the completion message shown after processing.

    Implementation deferred to Phase 6.
    """
    raise NotImplementedError("Implemented in Phase 6")


def get_fatal_error_message() -> str:
    """
    Retrieve the fatal error explanation for end users.

    Implementation deferred to Phase 6.
    """
    raise NotImplementedError("Implemented in Phase 6")
