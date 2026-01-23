# Phase 6 – Frontend Workflow Integration (P6)

## Purpose

Phase 6 defines the **user-facing application flow** for the Inventory Compliance Reporter (ICR).

This phase introduces a frontend orchestration layer responsible for guiding a **non-technical user** through a linear, confirmation-driven workflow while delegating all data processing and business logic to backend phases.

The frontend is intentionally abstracted from any specific UI technology (CLI, GUI, launcher wrapper).
It defines **what interactions exist and in what order**, not how they are rendered.

---

## Scope

Phase 6 covers:

* End-to-end application flow wiring
* Vessel selection user interaction
* Progress and status messaging
* User confirmation and intent validation
* Graceful error reporting

Out of scope:

* Excel ingestion
* SQLite access
* Inventory comparison
* Report generation
* Email drafting or sending
* Business rules or domain logic

---

## Design Principles

### 1. Linear, Guided Flow

The application proceeds step-by-step with no branching complexity exposed to the user.

### 2. Frontend as Orchestrator

The frontend coordinates actions but never performs data processing itself.

### 3. User-Safe Error Handling

Errors are translated into plain language and never expose stack traces or internal details.

### 4. Backend Independence

Frontend modules depend only on **backend interfaces**, not concrete implementations.

### 5. UI-Agnostic Design

Terminal UI is an implementation detail, not a design constraint.

---

## Entry Point

### `icr.app`

The application is launched via the `icr.app` module.

Responsibilities:

* Initialize runtime paths
* Initialize configuration
* Invoke the frontend workflow
* Catch and report fatal errors
* Exit cleanly

No user interaction logic resides here beyond top-level error handling.

---

## Frontend Module Overview

```
frontend/
├── flow.py
├── selection.py
└── messages.py
```

---

## `frontend/flow.py`

### Responsibility

Owns the **primary application workflow**.

This module defines the *sequence* of user-visible steps and delegates all actual work to backend or helper frontend modules.

### Core Responsibilities

* Display welcome / introduction message
* Validate or confirm input files (if required)
* Trigger AMS vessel discovery
* Invoke vessel selection UI
* Confirm user intent before execution
* Trigger backend processing
* Display completion summary
* Handle fatal errors gracefully

### Key Design Constraint

`flow.py` must not:

* Contain UI-specific rendering logic
* Perform validation or domain reasoning
* Assume how messages are displayed

It only **coordinates** actions.

---

## `frontend/selection.py`

### Responsibility

Handles **vessel selection interaction**.

This module presents AMS vessels and captures user selection intent in a deterministic and stateless manner.

### Selection Capabilities

* Select All vessels
* Select None
* Toggle individual vessels

### Input / Output Contract

Input:

* List of AMS vessel descriptors from backend

Output:

* List of selected vessel identifiers

### Design Constraints

* No global state
* No backend access
* No side effects
* Deterministic behavior based solely on input data and user interaction

---

## `frontend/messages.py`

### Responsibility

Central repository for **all user-facing text**.

This module exists to:

* Prevent hard-coded strings in logic
* Enable future localization
* Allow wording changes without touching flow logic

### Contents Include

* Headings and section titles
* Prompts and confirmations
* Progress messages
* Error explanations
* Completion summaries

No logic lives here—only strings.

---

## Conceptual Interaction Flow

1. Application starts
2. Welcome message displayed
3. Input validation or file discovery step
4. AMS vessels identified
5. Vessel selection screen displayed
6. User confirms selection
7. Processing begins
8. Progress messages displayed
9. Completion summary shown
10. Application exits

This flow is **linear and enforced**.

---

## Error Handling UX

### Principles

* Errors are explained in plain language
* Stack traces are never shown
* Fatal errors terminate the application cleanly

### Error Categories

* Configuration errors (missing files, invalid paths)
* Validation errors (malformed spreadsheets)
* Unexpected internal errors

### Frontend Behavior

For each error:

* Display a short explanation
* Suggest a next action when possible
* Exit gracefully on fatal errors

---

## Testing Expectations

Frontend tests should focus on:

* Correct sequencing of workflow steps
* Correct delegation to backend interfaces
* Correct handling of user confirmation paths
* Correct error propagation and messaging

Frontend tests must not:

* Depend on real files
* Access SQLite
* Assert backend behavior
* Validate domain logic

Mocks and stubs are expected.

---

## Future UI Evolution

The frontend abstraction supports:

* Terminal-based UI (initial implementation)
* Simple GUI (Tkinter / Qt)
* External launcher or wrapper

No backend changes should be required to support future UI upgrades.

---

## Phase 6 Deliverables

* Frontend workflow orchestration (`flow.py`)
* Vessel selection interaction layer (`selection.py`)
* Centralized message catalog (`messages.py`)
* Frontend unit tests validating flow control

---

## Summary

Phase 6 defines the **application frontend contract**.

Anything user-visible belongs here.
Anything data-related belongs in the backend.

This separation is mandatory for:

* PyInstaller stability
* Testability
* Long-term UI evolution
