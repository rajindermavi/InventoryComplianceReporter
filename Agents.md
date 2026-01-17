
# Agent Instructions

## Guidelines
Before making any changes:
- Read Design.md in full
- Review any relevant files in docs/ related to the area being modified

## Change Rules
- Do not violate goals or non-goals defined in Design.md
- Preserve public APIs unless explicitly instructed
- Keep changes scoped to the requested area
- Do not introduce insecure storage or auth behavior
- Do not silently downgrade security or provider guarantees
- Keep a changelog.md. For each update action, add a corresponding line to the changelog.

## Documentation
- Update docs/ when behavior changes
- Do not modify Design.md unless explicitly instructed
- Add changes to changelog.md

## Uncertainty
- If a change conflicts with Design.md, stop and ask

## Raw Input files
- This project relies on user supplied input files
- These files must never be moved, altered, or overwritten under any circumstances.
- See docs/RawInputs.md for details on these files.

## Guardrail: Runtime Paths Are Never Computed Outside paths.py

All filesystem paths used by InventoryComplianceReporter **must originate from**
`backend/persistence/paths.py`.

### Mandatory Rules

- No module may:
  - Construct filesystem paths manually
  - Use `Path.home()`, `os.getcwd()`, or hard-coded directories
  - Assume knowledge of the application directory layout
- No database, ingestion, or reporting code may:
  - Decide where files are stored
  - Create ad-hoc directories
  - Write outside the run directory

### Required Pattern

- A runtime paths object is created once during initialization
- This object is passed explicitly to downstream modules
- All filesystem writes and reads use paths from this object

Example (conceptual):

```python
paths = RuntimePaths.create()
db = Database(paths.db_path)
```
### Prohibited Pattern
```
# Not allowed
db_path = Path.home() / ".inventory_reporter" / "data.db"
```