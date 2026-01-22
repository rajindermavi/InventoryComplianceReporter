"""Frontend package for user interaction scaffolding.
* End-to-end application flow wiring
* Vessel selection user interaction
* Progress and status messaging
* User confirmation and intent validation
* Graceful error reporting
"""

from .flow import ConsoleIO, FrontendIO, run_flow
from .messages import COMPLETION, ERRORS, PROGRESS, PROMPTS, SELECTION, STATUS, WELCOME
from .selection import SelectionIO, select_vessels

__all__ = [
    "COMPLETION",
    "ConsoleIO",
    "ERRORS",
    "FrontendIO",
    "PROGRESS",
    "PROMPTS",
    "SELECTION",
    "STATUS",
    "SelectionIO",
    "WELCOME",
    "run_flow",
    "select_vessels",
]
