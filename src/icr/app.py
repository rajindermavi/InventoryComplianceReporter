"""Application entry point for Inventory Compliance Reporter.

Responsibilities:
- Invoke the frontend flow
- Handle top-level exceptions

Implementation deferred to Phase 6.
"""

from icr.frontend import flow


def main() -> None:
    """Run the application frontend flow."""
    try:
        flow.run_flow()
    except NotImplementedError:
        raise
    except Exception as exc:
        raise RuntimeError("Frontend execution failed.") from exc


if __name__ == "__main__":
    main()
