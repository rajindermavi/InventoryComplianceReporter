"""Application entry point for Inventory Compliance Reporter.

Responsibilities:
- Invoke the frontend (GUI or console flow)
- Handle top-level exceptions
"""

import sys

from icr.frontend.gui import run_gui


def app_main() -> None:
    """Run the GUI application."""
    try:
        run_gui()
    except Exception as exc:
        print(f"Application error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    app_main()
