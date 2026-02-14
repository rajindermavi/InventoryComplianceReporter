# System Contracts

This document defines the **authoritative contracts** between the major
components of the Inventory Compliance Reporter system.

These contracts specify **assumptions, guarantees, and failure semantics**
at component boundaries. They are independent of implementation details
(files, functions, phases).

All code is expected to conform to these contracts.

---

## Scope and Intent

This document:
- Defines what must be true at component boundaries
- Assigns ownership of validation, normalization, and failure handling
- Establishes where defensive checks belong — and where they do not

This document does NOT:
- Describe implementation details
- Enumerate internal helper behavior
- Specify UI or storage mechanisms

---

## Terminology

- **Canonical Record**  
  A record that conforms to an authoritative schema and contains no
  source-specific or ingestion-specific artifacts.

- **Contract Violation**  
  A situation where an assumption defined in this document is not met.
  Contract violations are treated as programmer or system errors, not
  recoverable data issues, unless explicitly stated otherwise.

---

## Component Overview

The system is composed of the following conceptual components:

1. Ingestion
2. Domain Comparison
3. Issue Classification
4. Reporting
5. Delivery (Export / Email / PDF)

Contracts are defined only at the boundaries between these components.

---

# 1. Ingestion Component

## Responsibility

Transform external Excel data sources into canonical internal domain records suitable for downstream processing.

The ingestion component performs:

- Header validation
- Row-level required field validation
- Type enforcement
- Email validation
- Date parsing
- String normalization
- Canonical schema transformation

---

## Inputs

- User-provided Excel workbooks
- First worksheet only
- Files matching supported SAFE_* patterns

---

## Outputs

- Canonical `Vessel` records
- Canonical `VesselInventoryRow` records
- Canonical `ICInventoryRow` records

(See Data Model schema documents for authoritative field definitions.)

---

## Guarantees

Upon successful completion of ingestion:

- All required headers are present
- All required row-level fields are populated
- All non-date fields are stored as strings
- All date fields are parsed into native date types
- Email fields are validated for proper format
- String fields are normalized according to system rules
- Source-specific column names, aliases, and formats are removed
- Derived fields (e.g., `ams`) are deterministically computed
- All records conform strictly to canonical domain schemas

---

## Type Enforcement Rules

- All fields are stored as strings after normalization **except date fields**
- Date fields must be parsed into native `date` types
- Email fields must conform to a valid email format
- Boolean fields are derived explicitly by ingestion logic

If a date fails parsing or an email fails validation:

- The row is flagged with a warning
- The row may proceed unless a required field is missing

---

## Non-Guarantees

The ingestion component does not guarantee:

- Business logic correctness
- Cross-record consistency
- Referential integrity across files
- Compliance determinations

---

## Failure Semantics

Ingestion halts with explicit, user-visible errors if:

- A required header column is missing
- A required row-level field is empty after normalization
- A record cannot be transformed into a canonical schema

Rows with:

- Invalid date formats
- Invalid email formats
- Missing non-required business fields

are ingested with warnings unless they violate required field constraints.

No invalid records proceed silently.

---

## Ownership

The ingestion component exclusively owns:

- Schema validation
- Type enforcement
- Email validation
- Date parsing
- Field normalization
- Canonical schema transformation

Downstream components may assume these guarantees without re-validation.

---
# 2. Domain Comparison Component

## Responsibility

Compare canonical vessel inventory records against canonical IC reference records to identify compliance discrepancies.

This component performs pure domain comparison logic only.

---

## Inputs

- Canonical `VesselInventoryRow` records
- Canonical `ICInventoryRow` records
- Canonical `Vessel` records

---

## Assumptions

- All inputs conform strictly to canonical schemas
- All required fields are present and non-null
- All non-date fields are normalized strings
- All date fields are native date types
- No ingestion-specific fields, aliases, or raw source columns exist
- Email and date validation has already been performed
- `ams` flags are already derived

No normalization, trimming, parsing, or validation is performed in this component.

---

## Comparison Semantics

Comparisons are performed using:

- `ship_id` as vessel identity key
- `item` as inventory identity key
- `onboard_edition` compared against `current_edition`

Comparison rules are:

- Exact string comparison (case-sensitive unless specified elsewhere)
- No fuzzy matching
- No alias resolution
- No format correction

---

## Outputs

- Canonical `Issue` records describing detected discrepancies

Each issue record includes:

- ship_id
- item
- onboard_edition
- current_edition
- issue_type

---

## Guarantees

- All comparisons are deterministic
- No randomness or ordering effects influence outcomes
- Issue classifications are mutually exclusive
- Each discrepancy produces exactly one issue record
- Output records conform strictly to the canonical Issue schema

---

## Non-Guarantees

This component does not guarantee:

- Graceful handling of malformed inputs
- Recovery from contract violations
- Cross-file reconciliation beyond defined comparison rules
- Business rule interpretation beyond defined compliance logic

---

## Failure Semantics

Violations of input assumptions are treated as contract violations.

If canonical invariants are violated:

- The component may raise exceptions
- The component may fail fast
- No attempt is made to repair or normalize data

---

## Ownership

The Domain Comparison Component exclusively owns:

- Comparison logic correctness
- Compliance classification rules
- Deterministic issue generation

It does not own:

- Schema validation
- Type enforcement
- String normalization
- Email validation
- Date parsing
- Data repair

---

## 3. Issue Classification Component

### Responsibility

Assign standardized classifications to detected discrepancies.

### Inputs

- Raw comparison results produced by the Domain Comparison component

### Outputs

- Classified Issue records

### Assumptions

- Input discrepancies are complete and internally consistent

### Guarantees

- Each issue receives exactly one classification
- Classifications are stable and documented

### Failure Semantics

- Ambiguous or incomplete inputs are treated as contract violations

---

## 4. Reporting Component

### Responsibility

Transform classified issue records into human-readable reports.

### Inputs

- Classified Issue records

### Outputs

- Structured report representations (e.g. HTML-ready data)

### Assumptions

- Input issues conform to the Issue schema
- No Optional or partially populated fields unless explicitly documented

### Guarantees

- Reports faithfully represent issue data
- No additional business logic is introduced

### Failure Semantics

- Contract violations result in explicit failures, not silent omissions

---

## 5. Delivery Component

### Responsibility

Deliver generated reports via supported mechanisms (export, email, PDF).

### Inputs

- Rendered report representations

### Outputs

- Files or messages delivered to user-selected destinations

### Assumptions

- Inputs are complete and renderable

### Guarantees

- Delivery mechanisms do not alter report content

### Failure Semantics

- Delivery failures are surfaced to the user
- Delivery failures do not corrupt report data

---

## Contract Enforcement Philosophy

- Contracts are enforced at component boundaries
- Internal helpers may assume upstream guarantees
- Defensive programming inside core logic is discouraged

---

## Change Management

- Changes to this document are **architectural changes**
- Schema changes must be reflected here if they alter guarantees
- Implementation changes must not weaken stated contracts

---

## Summary

- Contracts define system truth
- Schemas define structure
- Components trust upstream guarantees
- Violations fail fast and visibly

