# Inventory Compliance Reporter — Design Orchestration Document

## Purpose
This document defines how developers should navigate, interpret, and implement the project using the supporting documentation in the `docs/` directory.

This file intentionally **does not restate requirements**.  
It provides **binding instructions** for how the other documents work together and how implementation decisions should be made.

---

## Canonical Document Order (READ IN THIS ORDER)

Developers **must read and follow** the documents below in sequence.  
Later documents refine or constrain earlier ones.

1. **docs/ProjectRequirements.md**
   - Defines *what the system must do*
   - Business goals, scope, and acceptance criteria
   - No technical decisions should contradict this document

2. **docs/RequirementsSpec.md**
   - Defines *exact operational rules*
   - AMS detection rules
   - Matching and comparison semantics
   - Error handling expectations

3. **docs/Architecture.md**
   - Defines *system boundaries and component responsibilities*
   - Implementation must respect component separation
   - No cross-layer shortcuts unless explicitly justified

4. **docs/Data_Model.md**
   - Defines *domain objects and terminology*
   - Field names here should map cleanly to code models
   - This is the authoritative vocabulary for the system

5. **docs/Comparison_Logic.md**
   - Defines *inventory comparison semantics*
   - Edition normalization rules
   - Issue classification logic
   - This logic must be unit tested

6. **docs/Config.md**
   - Defines *all runtime configuration*
   - AMS logic, column mappings, output rules
   - No hard-coded column names or AMS rules in code

7. **docs/CLI_UX.md**
   - Defines *user interaction model*
   - CLI commands and interactive selection flow
   - UI decisions must conform to this contract

8. **docs/Run_Summary_Spec.md**
   - Defines *run output manifest*
   - Summary fields are required and auditable

9. **docs/Testing.md**
   - Defines *verification strategy*
   - Tests must map directly to earlier documents

10. **docs/Implementation.md**
    - Defines *implementation milestones*
    - Use as task decomposition guidance

---

## Design Principles (Binding)

The following principles are **non-negotiable**:

### 1. Configuration-Driven Logic
- AMS detection
- Column mapping
- Email behavior
- Comparison rules  
**Must be defined in config, not code**

### 2. Deterministic Batch Runs
- Same inputs → same outputs
- All artifacts written to a single run directory
- No hidden state across runs

### 3. Auditability First
- Every run must produce:
  - Selection record
  - Summary JSON
  - Per-vessel outputs
- No silent skips

### 4. Graceful Degradation
- Missing data ≠ crash
- Errors are logged and surfaced in summary
- Processing continues where possible

### 5. Separation of Concerns
Implementation must preserve these boundaries:

| Layer | Responsibility |
|-----|----------------|
| Ingestion | Reading & validating Excel |
| Domain | Matching & comparison logic |
| Reporting | HTML/PDF generation |
| Email | Drafting / sending |
| UX | CLI & selection |
| Persistence | Run outputs & logs |

### 6. Intermediate state may be persisted in a per-run SQLite database

---

## File Ownership Map (Code ↔ Docs)

Developers should align code modules to documents as follows:

| Code Area | Governing Doc |
|--------|--------------|
| `ingest/` | Requirements_Spec.md |
| `domain/models.py` | Data_Model.md |
| `domain/compare.py` | Comparison_Logic.md |
| `reporting/` | PRD.md + Architecture.md |
| `emailer/` | Requirements_Spec.md |
| `cli.py` | CLI_UX.md |
| `config.py` | Config.md |
| `tests/` | Testing.md |

---

## Implementation Guardrails

Developera **must not**:
- Hardcode column names
- Assume AMS logic structure
- Skip vessels silently
- Combine parsing, comparison, and reporting into a single function
- Send emails by default without a feature flag

Developers **should**:
- Create small, composable functions
- Prefer pure functions for comparison logic
- Log decisions (especially skips and mismatches)
- Emit structured JSON summaries

---

## Change Management

If a conflict arises:
1. **PRD.md** overrides all
2. **Requirements_Spec.md** overrides Architecture
3. **Data_Model.md** overrides inferred field names
4. Config overrides defaults but not logic

Any deviation must be:
- Documented in code comments
- Logged at runtime

---

## Developer Instruction Summary (TL;DR)

> Treat `docs/` as the source of truth.  
> Implement a deterministic, auditable batch system.  
> Configuration controls behavior.  
> Comparison logic must be explicit, testable, and explainable.  

