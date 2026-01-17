# Implementation Task List

This document defines the **ordered implementation phases** for the Inventory Compliance Reporter.
Phases are intentionally narrow to support incremental development, agent execution, and
a PyInstaller-based Windows application.

---

## Phase 1A – Backend Repository Scaffolding (COMPLETED)

Scope:
- Core package layout under `src/icr/`
- Backend module structure
- Domain, ingestion, reporting, email, persistence placeholders
- Design- and architecture-aligned boundaries

Status:
- Completed
- No functional logic implemented

---

## Phase 1B – Frontend & Application Scaffolding

Scope:
- `app.py` executable entry point
- Frontend orchestration layer under `frontend/`
- User-facing flow, selection, and message placeholders
- Top-level error handling boundaries

Deliverables:
- `icr.app` imports cleanly
- Frontend modules exist with documented responsibilities
- No backend logic invoked yet

---

## Phase 2A – Runtime Infrastructure

Scope:
- Windows-safe runtime path resolution
- Per-user application data directory
- Per-run directory creation
- Logging destination setup

Modules:
- `backend/persistence/paths.py`
- Supporting utilities as needed

---

## Phase 2B – Database Lifecycle & Schema

Scope:
- SQLite database creation per run
- Schema initialization
- Connection management
- Auditability guarantees

Modules:
- `backend/persistence/db.py`

---

## Phase 2C – Excel Ingestion

Scope:
- Read Excel spreadsheets (first sheet only)
- Normalize and validate columns
- Load data into SQLite tables
- Input validation and error reporting

Modules:
- `backend/ingest/excel_reader.py`

---

## Phase 3 – Core Domain Logic

Scope:
- AMS vessel identification (config-driven)
- Inventory matching (vessel ↔ IC)
- Edition normalization and comparison
- Issue classification

Modules:
- `backend/domain/models.py`
- `backend/domain/compare.py`

---

## Phase 4 – Reporting & Output Generation

Scope:
- Per-vessel report data assembly
- HTML report rendering
- Run summary generation
- Output artifact layout per run

Modules:
- `backend/reporting/html.py`

---

## Phase 5 – Email Drafting

Scope:
- Email recipient resolution
- Subject and body templating
- HTML embedding
- Optional `.eml` file generation

Modules:
- `backend/emailer/draft.py`

---

## Phase 6 – Frontend Workflow Integration

Scope:
- End-to-end application flow wiring
- Vessel selection UI integration
- Progress and status messaging
- User confirmation handling

Modules:
- `frontend/flow.py`
- `frontend/selection.py`
- `frontend/messages.py`

---

## Phase 7 – Output Delivery & User-Directed Actions

- Phase 7 is mandatory; delivery behaviors are user-selected per run.
- Reports are always generated in HTML.
- PDF generation is optional and user-controlled.
- Email drafts (`.eml`) can always be exported.
- Sending emails is never implicit and requires user confirmation.
- Users choose delivery mode: export only, send now, or both.
- Multiple email transports are supported (Nicemail preferred, SMTP optional).
- Transport selection occurs at runtime.
- Delivery failures must not block other outputs.
- All delivery actions are logged for auditability.


---

## Phase Dependencies (Summary)

- Phase 1A → Phase 1B
- Phase 1B → Phase 2A
- Phase 2A → Phase 2B → Phase 2C
- Phase 2C → Phase 3
- Phase 3 → Phase 4 → Phase 5
- Phase 4 & 5 → Phase 6
- Phase 6 → Phase 7

---

## Implementation Rules

- Each phase must be independently testable
- No phase may assume implementation details of a later phase
- Frontend must never contain business logic
- Backend must remain UI-agnostic
- Windows + PyInstaller constraints apply to all phases

---
