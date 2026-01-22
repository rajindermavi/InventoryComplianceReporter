# P7 – Packaging, Transport, and User-Directed Delivery

## Purpose

Phase 7 defines how **existing output artifacts** are packaged and acted upon
after report generation and email drafting are complete.

Phase 7 is **mandatory** for a complete application, but **all delivery behaviors
are explicitly user-controlled per run**.

This phase does **not** alter report content, comparison logic, or email drafts.
It operates exclusively on artifacts already written to the run workspace.

---

## Boundary Guarantees

Phase 7 enforces the following strict architectural boundaries:

- **Reporting (`backend.reporting`)**
  - Owns per-vessel report data assembly
  - Owns HTML report rendering
  - Owns run-level summary generation related to reporting

- **Emailer (`backend.emailer`)**
  - Owns recipient resolution
  - Owns subject and body templating
  - Owns `.eml` draft creation (optional)
  - Owns run summary updates related to email drafting

- **Phase 7 (`backend.delivery`)**
  - Owns delivery and packaging actions only
  - Consumes existing artifacts without modifying them

Phase 7 **never**:
- re-renders or mutates HTML reports
- drafts or modifies email content
- creates or edits `.eml` drafts
- infers or assumes delivery intent
- alters domain, comparison, or reporting logic

---

## Inputs to Phase 7

At the start of Phase 7, the following artifacts may already exist in the per-run
workspace:

- Per-vessel HTML reports (from `backend.reporting`)
- Optional `.eml` email drafts (from `backend.emailer`)
- Append-only run summary entries describing reporting and drafting actions

Phase 7 **discovers and consumes** these artifacts; it does not create them.

---

## Phase 7A – PDF Generation (Optional Per Run)

### Scope

- Generate PDF versions of existing per-vessel HTML reports
- PDFs may be:
  - Saved to the run directory
  - Attached to outgoing emails (if emails are sent)
- PDF generation is enabled or disabled per run based on explicit user selection

### Responsibilities

Phase 7A is responsible for:

- Locating per-vessel HTML report files written by the reporting subsystem
- Rendering PDFs from those HTML files
- Writing PDF artifacts to the run workspace
- Recording PDF generation outcomes in the run summary

Phase 7A does **not**:
- modify HTML content
- regenerate report data
- influence email drafting decisions

### Rules

- PDF generation must be **deterministic** given:
  - the same HTML input
  - the same rendering engine and version
  - the same static assets
- PDF generation must be **best-effort**:
  - Failure for one vessel must not affect others
  - Failure must not block email export or sending
- Renderer availability must be checked at runtime
- Renderer name and version must be recorded for auditability

---

## Phase 7B – Email Delivery (User-Directed)

### Scope

- Act upon **existing `.eml` drafts** generated earlier in the run
- Support multiple delivery modes per run:
  - Export drafts only
  - Send emails immediately
  - Do both

Phase 7B never drafts, edits, or reserializes email content.

### Delivery Modes

Per run, the user may choose:

1. **Export only**
   - `.eml` drafts remain on disk
   - No network delivery occurs

2. **Send now**
   - Existing `.eml` drafts are sent via a selected transport
   - Sending requires explicit user confirmation

3. **Export + send**
   - Drafts remain on disk
   - Drafts are also sent via transport

### Supported Transports

- SMTP
- Nicemail (preferred, feature-flagged)
- Additional transports may be added without frontend changes

Transport selection occurs at runtime and is never implicit.

### Rules

- Sending emails is **never implicit**
- Explicit user confirmation is required before any send
- Missing `.eml` drafts must be handled gracefully per vessel
- Failures in sending must not block other delivery actions

---

## User-Guided Delivery Selection

At runtime, the frontend is responsible for guiding the user through delivery
choices:

1. Choose report formats:
   - HTML (always generated)
   - PDF (optional)
2. Choose email handling:
   - Export drafts only
   - Send emails now
   - Export and send
3. If sending:
   - Select transport (SMTP, Nicemail, etc.)
   - Explicitly confirm sending action

The frontend:
- Collects user intent
- Validates confirmation
- Passes delivery instructions to the backend
- Does **not** implement delivery logic

---

## Backend Responsibilities (Phase 7)

The backend delivery subsystem must:

- Execute delivery actions strictly according to user intent
- Support multiple delivery actions in a single run
- Fail gracefully per vessel and per delivery mode
- Never assume the presence of other delivery modes
- Append delivery outcomes to the run summary

---

## Auditability Requirements

For each run:

- All generated artifacts must remain on disk
- Delivery actions must be recorded in an append-only manner
- Sent vs. exported emails must be clearly distinguishable
- PDF generation outcomes must be recorded per vessel
- Renderer and transport metadata must be included where applicable

---

## Design Guarantees

- Phase 7 does not modify domain logic, comparison logic, or reporting logic
- Delivery modes are orthogonal and composable
- New transports can be added without frontend refactors
- Nicemail integration does not affect email drafting
- Artifact provenance is preserved end-to-end
