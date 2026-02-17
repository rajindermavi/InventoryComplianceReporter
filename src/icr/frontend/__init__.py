"""Frontend package for user interaction scaffolding.
* End-to-end application flow wiring
* Vessel selection user interaction
* Progress and status messaging
* User confirmation and intent validation
* Graceful error reporting
* GUI (tkinter) frontend
"""

from .flow import ConsoleIO, FrontendIO, run_flow
from .gui import run_gui
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
    "run_gui",
    "select_vessels",
]
