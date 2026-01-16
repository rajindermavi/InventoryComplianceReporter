# Detailed Requirements Specification

## AMS Identification
AMS status must be configurable and not hard-coded.

Supported AMS rules:
- Column contains "AMS"
- Column equals specific value
- Boolean column
- Regex match

---

## Matching Rules

### Vessel Matching
- Match by SHIPID
- Trim whitespace
- Case-sensitive by default

### Item Matching
- Match by ITEM
- Case-insensitive (configurable)
- Trim whitespace

---

## Edition Comparison
- Normalize editions before comparison
- Blank or missing editions are flagged
- Missing reference editions are flagged

---

## Reporting Rules
Each report includes:
- Vessel header information
- Run timestamp
- Source file names
- Table of discrepancies
- Clear message if no issues found

---

## Email Rules
- To: Vessel email + office email
- Subject and body templated
- HTML body embeds report
- Optional PDF attachment

---

## Error Handling
- Missing columns → validation error
- Missing data → warning, continue processing
- All errors logged to run log
