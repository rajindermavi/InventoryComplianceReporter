## Phase 7 – Output Delivery & User-Directed Actions

Phase 7 defines how generated outputs are **delivered or acted upon**.
This phase is required for a complete application, but all delivery behaviors
are **explicitly user-controlled**.

The system must support multiple delivery modes without requiring changes
to core logic or report generation.

---

### Phase 7A – PDF Generation (Optional Per Run)

Scope:
- Render PDF versions of vessel reports from HTML
- PDFs may be:
  - Saved to the run directory
  - Attached to outgoing emails
- PDF generation is enabled or disabled per run based on user selection

Rules:
- PDF generation must be deterministic
- Failure to generate a PDF must not block other delivery modes
- PDF generation must not alter HTML output

---

### Phase 7B – Email Delivery (User-Directed)

Scope:
- Deliver generated email content according to user choice
- Support multiple delivery modes:
  - Export `.eml` email files only
  - Send emails immediately via a transport
  - Do both

Delivery transports:
- SMTP
- Nicemail (preferred, feature-flagged)
- Additional transports may be added later

Rules:
- Email delivery is never implicit
- The user must explicitly confirm sending
- Export-only mode must always be available
- Transport selection occurs at runtime

---

### User-Guided Delivery Selection

At runtime, the frontend must guide the user through delivery choices:

1. Choose report formats:
   - HTML (always generated)
   - PDF (optional)
2. Choose email handling:
   - Export email drafts only (`.eml`)
   - Send emails now
3. If sending:
   - Choose transport (e.g., Nicemail, SMTP)
   - Confirm action before execution

The frontend:
- Collects user intent
- Passes delivery instructions to the backend
- Does NOT implement delivery logic

---

### Backend Responsibilities

The backend must:
- Support all delivery modes independently
- Allow multiple delivery actions in a single run
- Fail gracefully per vessel and per delivery mode
- Log all delivery actions for auditability

No delivery mode may assume the presence of another.

---

### Auditability Requirements

For each run:
- All generated artifacts must be saved
- Delivery actions must be recorded in the run summary
- Sent vs exported emails must be distinguishable

---

### Design Guarantees

- Phase 7 does not change report or comparison logic
- Delivery modes are orthogonal and composable
- New transports can be added without frontend refactors
- Nicemail integration does not affect draft generation

---
