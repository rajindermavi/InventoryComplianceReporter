# P3_DomainLogic.md  
**Phase 3 – Core Domain Logic**

## Purpose

Phase 3 implements the **core, deterministic business logic** for inventory compliance.  
It is responsible for **matching vessels and items**, **normalizing and comparing editions**, and **classifying discrepancies** into well-defined issue types.

This phase is **pure domain logic**:
- No UI
- No I/O
- No email, HTML, or PDF generation
- Fully testable with in-memory data

---

## Scope

Phase 3 is responsible for:

- Identifying AMS-marked vessels (config-driven)
- Matching vessels between AMS index and inventory sources
- Matching inventory items onboard vessels to IC reference inventory
- Normalizing editions prior to comparison
- Classifying inventory discrepancies into issue rows

---

## Inputs (Conceptual)

Phase 3 operates on **already-ingested, structured data**:

- AMS Index records (vessel metadata)
- Onboard inventory records (per vessel)
- IC reference inventory (authoritative editions)
- Configuration flags (case sensitivity, column mappings)

---

## Outputs

- A list of **Issue Rows** per vessel
- Issue rows are later consumed by reporting and delivery layers

---

## Modules

| Module | Responsibility |
|------|---------------|
| `backend/domain/models.py` | Domain models and enums |
| `backend/domain/compare.py` | Matching, normalization, comparison logic |

---

## Domain Models

### IssueRow

Represents a single detected discrepancy.

**Fields**
- `ship_id`
- `item`
- `onboard_edition`
- `current_edition`
- `issue_type`

**Issue Types**
- `OUTDATED`
- `MISSING_ONBOARD`
- `MISSING_REFERENCE`

---

## Matching Rules

### Vessel Matching

- Match vessels by `SHIPID`
- Trim leading/trailing whitespace
- Case-sensitive by default
- Only AMS-marked vessels are eligible (as defined in config)

---

### Item Matching

- Match by `ITEM`
- Trim leading/trailing whitespace
- Case-insensitive by default (configurable)

---

## Edition Normalization

Before comparison, edition strings are normalized using the following rules:

- Strip leading/trailing whitespace
- Collapse multiple internal spaces
- Optional case folding (configurable)

Normalization ensures cosmetic differences do not trigger false positives.

---

## Comparison Logic

For each **selected AMS vessel**:

1. Retrieve all onboard inventory items and their onboard editions
2. For each onboard item:
   - Look up the corresponding reference item in IC inventory
   - Normalize onboard and reference editions
   - Classify the comparison outcome

---

## Comparison Outcomes

Comparison outcomes are mutually exclusive and evaluated in order:

1. **Onboard edition missing**  
   → `MISSING_ONBOARD`

2. **Item missing in IC reference inventory**  
   → `MISSING_REFERENCE`

3. **Editions differ after normalization**  
   → `OUTDATED`

4. **Editions match**  
   → `OK` (not reported)

Only outcomes 1–3 generate issue rows.

---

## Deduplication Rules

Duplicate issue rows **may be removed** prior to reporting.

Deduplication keys:
- `item`
- `onboard_edition`
- `issue_type`

Deduplication behavior is deterministic and side-effect free.

---

## Non-Responsibilities (Explicitly Out of Scope)

Phase 3 **does not**:

- Render HTML or PDFs
- Generate or send emails
- Persist results
- Apply vessel selection UI logic
- Perform Excel ingestion or parsing

These concerns belong to later phases.

---

## Design Principles

- **Pure functions where possible**
- **Config-driven behavior**
- **Deterministic outputs**
- **Fully unit-testable**
- **No dependency on transport or presentation layers**

---

## Notes for Contributors

- All business rules must be encoded here, not duplicated downstream
- If a rule affects *what is considered an issue*, it belongs in Phase 3
- If a rule affects *how issues are displayed or sent*, it belongs later
