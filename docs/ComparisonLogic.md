# Inventory Comparison Logic

## Normalization
- Strip whitespace
- Collapse multiple spaces
- Optional case folding

---

## Comparison Outcomes

1. Onboard edition missing → MISSING_ONBOARD
2. Item missing in IC → MISSING_REFERENCE
3. Editions differ → OUTDATED
4. Editions match → OK (not reported)

---

## Deduplication
Duplicate issue rows may be removed based on:
- item
- onboard edition
- issue type
