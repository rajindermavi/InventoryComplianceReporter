# Phase 5 – Email Drafting

## Purpose

Phase 5 is responsible for **constructing draft email artifacts** based on
rendered reports and run metadata.

This phase prepares emails for review or downstream delivery, but **does not
send email**.

Email drafting is treated as a **pure transformation step**:
structured inputs → draft email outputs.

---

## Scope

Phase 5 includes:

- Email recipient resolution
- Subject and body templating
- HTML report embedding
- Optional `.eml` draft file generation
- Run summary updates related to email drafting

Out of scope:

- Email sending (SMTP / Graph / Gmail)
- Credential handling
- User interaction or approval flows

---

## Inputs

Phase 5 consumes:

- Per-vessel HTML reports from Phase 4
- Vessel contact metadata
- Office / compliance email address
- Run metadata (run_id, timestamps, source files)
- Optional PDF attachments (if available)

It may also read and update:

- `summary.json` (run summary specification)

---

## Outputs

Phase 5 produces **draft email artifacts**, not sent messages.

Typical outputs per run:

```
output/
└── run_YYYYMMDD_HHMM/
├── emails/
│ ├── VESSEL_001.eml
│ ├── VESSEL_002.eml
│ └── ...
└── summary.json
```


Draft emails may be:
- `.eml` files
- In-memory draft objects returned to the caller
- Later handed off to a delivery layer (e.g., Nicemail)

---

## Email Rules

Each drafted email MUST follow these rules:

- **To:**  
  - Vessel email address  
  - Office / compliance email address
- **Subject:**  
  - Templated and deterministic
- **Body:**  
  - HTML body embeds the per-vessel report
- **Attachments:**  
  - Optional PDF attachment (if available)

Email drafts must be readable in standard email clients without external assets.

---

## Error Handling Rules

Phase 5 applies **non-fatal error handling** where possible.

- Missing required columns  
  → Validation error, email draft not created
- Missing optional data  
  → Warning logged, continue processing
- All errors and warnings  
  → Recorded in the run log and reflected in `summary.json`

Phase 5 must not silently drop vessels or recipients.

---

## Run Summary Integration

Phase 5 updates `summary.json` according to the **Run Summary Specification**:

```json
{
  "run_id": "YYYYMMDD_HHMM",
  "ams_vessels_found": 0,
  "vessels_selected": 0,
  "vessels_processed": 0,
  "vessels_with_issues": 0,
  "total_issue_rows": 0,
  "errors": []
}
```

Phase 5 responsibilities include:

- Incrementing `vessels_processed` when one or more draft emails are successfully generated for a vessel
- Appending email-related validation or drafting errors to the `errors` array in `summary.json`
- Preserving all prior summary fields populated by earlier phases

Phase 5 must **not overwrite** summary data from earlier phases. It may only:
- Read existing fields
- Increment counters where explicitly allowed
- Append new error or warning entries

---

## Summary Update Semantics

When updating `summary.json`, Phase 5 must follow these rules:

- `run_id`  
  - Must already exist  
  - Never modified by Phase 5

- `ams_vessels_found`, `vessels_selected`  
  - Read-only in Phase 5

- `vessels_processed`  
  - Incremented once per vessel for which email drafting is attempted  
  - Incremented even if warnings occur  
  - Not incremented if drafting fails due to validation errors

- `vessels_with_issues`, `total_issue_rows`  
  - Read-only in Phase 5  
  - Derived from earlier domain/reporting phases

- `errors`  
  - Phase 5 may append new entries  
  - Existing entries must be preserved  
  - Entries should clearly indicate:
    - Phase (`phase: "email_drafting"`)
    - Vessel identifier (if applicable)
    - Error or warning message

---

## Error vs Warning Semantics

Phase 5 distinguishes between **errors** and **warnings**:

### Validation Errors
- Missing required columns
- Missing required recipient addresses
- Invalid email address formats

Behavior:
- Draft email is not generated for the affected vessel
- An error entry is appended to `summary.json`
- Processing continues for other vessels

### Warnings
- Missing optional data (e.g., missing PDF attachment)
- Non-critical template substitutions

Behavior:
- Draft email is still generated
- Warning is logged and appended to `summary.json`
- No counters are rolled back

---

## Determinism and Idempotency

Phase 5 must be deterministic:

- Given the same inputs and existing `summary.json`, repeated runs produce:
  - Identical draft email artifacts
  - Identical summary updates (no duplicate error entries)

Callers are responsible for ensuring Phase 5 is not applied multiple times to the same run directory unless explicitly intended.

---

## Phase Boundary Guarantees

Phase 5 guarantees that:

- No summary fields unrelated to email drafting are modified
- No email is sent
- No credentials are accessed
- No transport decisions are made

Downstream phases may safely assume that all drafted emails are complete, self-contained artifacts ready for delivery.

---
