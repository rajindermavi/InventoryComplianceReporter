# Frontend UX Specification (formerly CLI_UX)

## Purpose

This document defines the **user-facing interaction flow** for the Inventory Compliance Reporter.

Although the initial implementation may use a terminal-based interface, this document intentionally avoids “CLI tool” semantics.  
The frontend represents an **application flow for non-technical users**, suitable for execution as a PyInstaller-built Windows executable.

The frontend layer:
- Orchestrates user interaction
- Guides the user through a linear workflow
- Delegates all business logic to the backend
- Does NOT perform data processing itself

---

## Frontend Responsibilities

The frontend is responsible for:

1. Guiding the user through the application workflow
2. Displaying progress and status messages
3. Allowing vessel selection (All / None / Individual)
4. Confirming user intent before execution
5. Displaying success or error messages in user-friendly terms

The frontend must NOT:
- Parse Excel files
- Access SQLite directly
- Compare inventory editions
- Generate reports
- Contain business rules

---

## Entry Point

The application is launched via:

icr.app


The `app.py` module:
- Initializes runtime paths
- Invokes the frontend flow
- Handles top-level error reporting
- Exits cleanly

---

## Frontend Modules

### `frontend/flow.py`
Owns the **primary application workflow**.

Responsibilities:
- Display welcome / intro message
- Request or confirm input file locations (if applicable)
- Trigger AMS vessel discovery (via backend)
- Invoke vessel selection UI
- Confirm execution
- Trigger backend processing
- Display final summary

This module defines the *sequence* of steps, not their implementation.

---

### `frontend/selection.py`
Handles **vessel selection UI**.

Responsibilities:
- Display list of AMS vessels
- Allow:
  - Select All
  - Select None
  - Toggle individual vessels
- Return a list of selected vessel identifiers

Selection logic must be:
- Stateless
- Deterministic
- Fully driven by data provided by backend

---

### `frontend/messages.py`
Centralizes **user-facing text**.

Responsibilities:
- Store all strings shown to users
- Enable future localization or wording changes
- Prevent hard-coded strings scattered across code

This includes:
- Headings
- Prompts
- Confirmation messages
- Error explanations
- Completion summaries

---

## Interaction Flow (Conceptual)

1. Application starts
2. Welcome message displayed
3. Input validation or file discovery step
4. AMS vessels identified
5. Vessel selection screen displayed
6. User confirms selection
7. Processing begins
8. Progress messages displayed
9. Completion message shown with summary
10. Application exits

This flow must be **linear and guided**.

---

## Error Handling UX

### Principles
- Errors must be explained in plain language
- Stack traces must never be shown to end users
- Fatal errors terminate the application gracefully

### Categories
- Configuration errors (e.g., missing files)
- Validation errors (e.g., malformed spreadsheet)
- Unexpected internal errors

Frontend displays:
- Short explanation
- Suggested next action (when possible)

---

## Future UI Evolution

The frontend is intentionally abstracted so that:

- Terminal UI (initial)
- Simple GUI (Tkinter / Qt)
- Wrapper launcher

can all be implemented **without changing backend logic**.

The frontend modules define **what** interactions exist, not **how** they are rendered.

---

## Testing Expectations

Frontend modules should be tested by:
- Verifying flow control decisions
- Verifying correct delegation to backend interfaces

Frontend tests must NOT:
- Assert backend behavior
- Depend on real files
- Depend on real databases

---

## Summary

This document defines the **application frontend contract**.

Anything user-visible belongs here.  
Anything data-related belongs in the backend.

This separation is mandatory for:
- PyInstaller stability
- Testability
- Future UI upgrades
