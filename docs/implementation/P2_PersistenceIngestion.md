# Phase 2 – Persistence & Ingestion Core

**Purpose:**  
Phase 2 establishes the *runtime backbone* of the system: where data lives, how it is persisted, and how source spreadsheets are ingested in a reproducible, auditable way. All downstream logic (matching, classification, reporting, email) assumes Phase 2 guarantees **determinism, isolation, and traceability**, while still allowing user discretion when recoverable issues occur.

---

## Phase 2A – Runtime Infrastructure

### Goals
- Windows-safe, cross-platform path resolution
- Per-user application data directory
- Self-contained per-run workspace
- Early, consistent logging destination setup

### Design Principles
- No hard-coded paths
- No global mutable state
- Each run is fully reproducible from its run directory
- Paths are resolved once and injected everywhere else

### Responsibilities
Handled by `backend/persistence/paths.py` (already implemented):

- Resolve base application directory (per-user)
- Create a unique run directory (timestamp + optional suffix)
- Expose canonical subdirectories:
  - `data/` – SQLite database, raw artifacts
  - `logs/` – structured logs
  - `output/` – reports, exports
  - `tmp/` – scratch/intermediate files

### Runtime Contract
Downstream modules **must not compute paths themselves**.  
They receive a runtime paths object and write only inside it.

Conceptual example:

```python
paths = RuntimePaths.create()
paths.db_path
paths.log_dir
paths.output_dir
```

### Logging Setup

- Logging destination determined here
- Logging initialized before database creation
- All modules write to the same run-scoped sink
- Warnings generated during ingestion must be surfaced in logs in a user-facing manner

## Phase 2B – Database Lifecycle & Schema

### Goals
- One SQLite database per run
- Schema-first initialization
- Strong auditability and provenance
- Explicit, safe connection management

### Database Model
- SQLite database stored at the path provided by `paths.py`
- One database file per run
- No shared databases between runs
- No schema mutation after initialization
- SQLite WAL mode enabled by default

### Responsibilities
Implemented in `backend/persistence/db.py`.

#### Database Creation
- Create the SQLite database file if it does not exist
- Use the database path supplied by runtime paths
- Enable WAL mode on initialization
- Fail fast if schema initialization fails
- Initialize database metadata immediately

#### Schema Initialization
The database schema must be fully initialized before any ingestion occurs.

Minimum schema includes:

1. **metadata**
   - `run_id`
   - `created_at` (UTC)
   - `app_version`
   - `git_commit`
   - `build_date`
   - `input_fingerprint` (hash of the input Excel file)

2. **raw_excel_rows**
   - Faithful representation of normalized Excel input
   - Original Excel row number preserved
   - Rows are append-only and never mutated

3. **validation_errors**
   - `row_number`
   - `column`
   - `error_type`
   - `message`
   - `severity` (e.g., warning, fatal)
   - Rows are append-only and never mutated

Additional domain-specific tables may be added in later phases.

#### Connection Management
- Database connections are created explicitly
- No global or singleton connections
- Connections are short-lived and context-managed
- Callers are responsible for connection scope

Example pattern:

```python
with db.connect() as conn:
    conn.execute(...)
```

### Auditability Guarantees

- Each run produces a distinct database file
- All raw input data is preserved exactly as ingested
- Validation warnings and errors are fully recorded
- No destructive updates to raw or validation tables
- Downstream phases may only append derived data or reference existing rows

## Phase 2C – Excel Ingestion

### Goals
- Deterministic ingestion of Excel input
- Early normalization and validation of data
- Faithful preservation of raw input
- Clear, actionable validation warnings and errors
- User-controlled continuation when recoverable issues are present

### Responsibilities
Implemented in `backend/ingest/excel_reader.py`.

### Input Assumptions
- Only the first worksheet in the Excel file is processed
- A header row must be present
- Column names are normalized using case-folding and whitespace trimming

---

### Ingestion Pipeline

#### 1. Load Excel
- Attempt to read the Excel file
- Fail with a fatal error if the file is unreadable
- Fail if the file contains no rows

#### 2. Normalize Columns
- Trim leading and trailing whitespace
- Convert column names to a normalized case
- Apply known column alias mappings (extensible in later phases)

#### 3. Handle Duplicate Headers
- Duplicate headers after normalization generate a warning
- The first occurrence of a duplicated column is used
- Subsequent duplicate columns are ignored
- All duplicate-header events are logged and recorded as warnings

#### 4. Validate Schema
- Verify required columns are present
- Missing non-negotiable required columns result in a fatal error
- Schema-level issues that are recoverable are recorded as warnings

#### 5. Row-Level Validation
- Each row is validated independently
- Empty rows or rows missing key fields (e.g., email addresses):
  - Are logged as warnings
  - Are recorded in the `validation_errors` table
- Invalid rows do not halt ingestion
- Valid rows are inserted into `raw_excel_rows`
- Original Excel row numbers are preserved

#### 6. Persistence
- Ingestion occurs within a database transaction
- Row order is preserved
- All validation diagnostics are persisted before commit

---

### Error Handling and User Control

- **Fatal errors**
  - Unreadable Excel file
  - Missing header row
  - Missing required non-negotiable columns

- **Warnings**
  - Empty rows
  - Missing emails or optional fields
  - Duplicate headers
  - Row-level validation failures

If any warnings are generated:
- The run is marked as having warnings
- The user must be given an opportunity to:
  - Abort the run and correct the input, or
  - Explicitly proceed with warnings acknowledged

No automatic progression to subsequent phases occurs without this decision.

---

## Phase 2 Outputs

At completion of Phase 2:

- A run-specific directory exists with all expected subdirectories
- A SQLite database exists at the path provided by `paths.py`
- The database contains:
  - Run metadata
  - Raw normalized Excel input
  - Recorded validation warnings and errors
- Logs clearly surface any warnings requiring user attention
- The system pauses at a decision boundary if warnings are present

This state forms the entry point for **Phase 3 – Matching and Classification**.

---

## Explicit Non-Goals (Phase 2)

- No business rule evaluation
- No AMS matching logic
- No report, PDF, or email generation
- No cross-run aggregation or persistence

---
