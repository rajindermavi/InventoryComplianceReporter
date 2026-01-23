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

## 1. Ingestion Component

### Responsibility

Transform external data sources into canonical internal records suitable
for domain processing.

### Inputs

- User-provided Excel workbooks and worksheets

### Outputs

- Canonical Inventory Records
- Canonical Reference Records

(See schema documents for authoritative field definitions.)

### Guarantees

- All required fields are present
- String fields are normalized according to system rules
- Source-specific column names, aliases, and formats are removed
- Records conform to the canonical schemas

### Non-Guarantees

- Business logic correctness
- Cross-record consistency

### Failure Semantics

- Schema violations halt ingestion with explicit, user-visible errors
- Invalid or malformed records do not proceed to downstream components

### Ownership

- Ingestion owns all schema validation and normalization
- Downstream components may assume these guarantees without re-validation

---

## 2. Domain Comparison Component

### Responsibility

Compare canonical inventory records against canonical reference records
to identify compliance discrepancies.

### Inputs

- Canonical Inventory Records
- Canonical Reference Records

### Assumptions

- Inputs conform to canonical schemas
- No ingestion-specific fields or aliases are present
- All required fields are non-null and semantically valid

### Outputs

- Issue records describing detected discrepancies

### Guarantees

- Comparisons are deterministic
- Issue classifications are mutually exclusive
- Output records conform to the canonical Issue schema

### Non-Guarantees

- Graceful handling of malformed inputs
- Recovery from contract violations

### Failure Semantics

- Violations of input assumptions are treated as contract violations
- Contract violations may raise exceptions or fail fast

### Ownership

- Domain logic owns comparison correctness
- Domain logic does not perform schema validation or normalization

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

