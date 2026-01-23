# Phase 4 – Reporting & Output Generation

## Purpose

Phase 4 is responsible for transforming **classified domain results** into
human-readable, durable output artifacts.

This phase produces **report files**, not emails.  
Email delivery (if any) is handled later by a separate delivery phase.

The primary output format in Phase 4 is **HTML**, which serves as the canonical
representation of a compliance report for a single run.

---

## Scope

Phase 4 includes:

- Per-vessel report data assembly
- HTML report rendering
- Run-level summary generation
- Output artifact layout on disk

Out of scope:

- Email message creation
- SMTP / Graph / Gmail integration
- PDF generation (handled in later phases)

---

## Inputs

Phase 4 consumes:

- Classified comparison results from Phase 3
- Normalized vessel metadata
- Runtime metadata:
  - Run timestamp
  - Source file names
  - Configuration identifiers (if applicable)

No database writes occur in this phase.

---

## Outputs

Phase 4 produces **filesystem artifacts** only.

Typical outputs per run:

```
output/
└── run_YYYYMMDD_HHMMSS/
├── summary.html
├── vessels/
│ ├── VESSEL_001.html
│ ├── VESSEL_002.html
│ └── ...
└── metadata.json
```


HTML files are treated as the **canonical report artifacts** and may later be:

- Viewed directly
- Embedded into emails
- Converted to PDF
- Archived for audit/compliance

---

## Reporting Rules

Each per-vessel report MUST include:

- Vessel header information
- Run timestamp
- Source file names
- Table of discrepancies
- Clear message when no issues are found

Reports must be readable without any external context.

---

## Module Responsibilities

### `backend/reporting/html.py`

This module is responsible for:

- Translating structured report data into HTML
- Ensuring consistent layout and styling
- Rendering:
  - Per-vessel reports
  - Run summary report
- Producing deterministic output given the same inputs

The module MUST NOT:

- Send emails
- Construct `email.message` objects
- Perform filesystem traversal beyond writing known output paths
- Access databases directly

---

## HTML as the Canonical Format

HTML is used because it:

- Is transport-agnostic
- Is easy to inspect and debug
- Supports rich tables and structured layouts
- Can be reused across multiple output channels
- Enables future PDF generation without redesign

Email delivery treats HTML as **input**, not as the source of truth.

---

## Design Principles

Phase 4 follows these principles:

- **Separation of concerns**  
  Reporting is independent of delivery.
- **Deterministic output**  
  Same inputs → same HTML.
- **Auditability**  
  Artifacts are stored per run.
- **Extensibility**  
  Additional formats (PDF, email) can be layered later.

---

## Testing Expectations

Phase 4 should be tested via:

- Snapshot tests of generated HTML
- Validation of required sections
- Verification of “no issues found” states
- Run-level directory structure checks

Email delivery tests belong to a later phase.

---

## Future Extensions

Planned future enhancements include:

- HTML → PDF rendering
- Optional email embedding or attachment
- User-selectable output formats
- Theming or branding support

None of these require changes to Phase 4’s core responsibilities.

---

## Summary

Phase 4 converts domain results into **clear, durable reports**.
It defines *what* is reported and *how it looks*, but not *how it is sent*.

HTML is the canonical reporting artifact.
Delivery is a downstream concern.
