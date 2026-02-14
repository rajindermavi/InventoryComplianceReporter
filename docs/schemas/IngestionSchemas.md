

# Ingestion Layer — Input Table Schemas

This document defines the formal schema contract for all raw Excel inputs to the ICR ingestion layer.

Only the **first worksheet** of each Excel file is read.  
Extra columns are ignored.

---

# 1. SAFE_IC_INVENTORY

## File Pattern
SAFE_IC_INVENTORY_YYYYMMDD*.XLSX


## Required Columns (Header-Level Validation)

| Column   | Required |
|----------|----------|
| ITEM     | Yes |
| ITMDESC  | Yes |
| PLINID   | Yes |
| ITMCLSS  | Yes |
| UPCCODE  | Yes |
| EDITION  | Yes |
| CURRDATE | Yes |

If any required column is missing → **File Error (ingestion stops).**

---

## Required Fields (Row-Level Validation)

| Column  | Required | Failure Type |
|----------|----------|--------------|
| ITEM     | Yes | Row Error |
| EDITION  | Yes | Row Error |

If a required field is empty after trimming → **Row Error.**

---

## Warning Conditions

| Column   | Warning Condition |
|----------|------------------|
| CURRDATE | Missing OR invalid date format (MM/DD/YYYY) |

Rows with warnings are ingested but flagged.

---

## Raw Data Types

All fields are read as strings.

Special parsing rule:

- `CURRDATE` must parse as `MM/DD/YYYY`
- If parsing fails → Warning

---

## Raw Schema Definition
SAFE_IC_INVENTORY

ITEM:       string (required, non-empty)
ITMDESC:    string
PLINID:     string
ITMCLSS:    string
UPCCODE:    string
EDITION:    string (required, non-empty)
CURRDATE:   string (parsed to date)


---

# 2. SAFE_VESSELS_INDEX

## File Pattern
SAFE_VESSELS_INDEX_YYYYMMDD*.XLSX

## Required Columns (Header-Level Validation)

| Column   | Required |
|----------|----------|
| SHIPID   | Yes |
| SHIPNAME | Yes |
| CUSTNO   | Yes |
| IMONO    | Yes |
| SHIPSTAT | Yes |
| EMAIL    | Yes |
| NOTE1    | Yes |
| NOTE2    | Yes |
| NOTE3    | Yes |

If any required column is missing → **File Error (ingestion stops).**

---

## Required Fields (Row-Level Validation)

| Column | Required | Failure Type |
|--------|----------|--------------|
| SHIPID | Yes | Row Error |
| EMAIL  | Yes | Row Error |
| NOTE2  | Must exist (may be empty string) | Row Error if missing |

---

## Warning Conditions

| Column   | Warning Condition |
|----------|------------------|
| SHIPNAME | Empty |
| CUSTNO   | Empty |
| EMAIL    | Invalid email format |

Rows with warnings are ingested but flagged.

---

## Derived Field

### AMS Flag

AMS = True if "AMS" (case-insensitive) appears in NOTE2
AMS = False otherwise


NOTE2 may be empty.

---

## Raw Data Types

All fields are read as strings.

Special validation rule:

- `EMAIL` must match basic email format
- Invalid format → Warning

---

## Raw Schema Definition

SAFE_VESSELS_INDEX

SHIPID:     string (required, non-empty)
SHIPNAME:   string
CUSTNO:     string
IMONO:      string
SHIPSTAT:   string
EMAIL:      string (required, valid format)
NOTE1:      string
NOTE2:      string (required column; may be empty)
NOTE3:      string


---

# 3. SAFE_VESSELS_INVENTORY

## File Pattern

SAFE_VESSELS_INVENTORY_YYYYMMDD*.XLSX


## Required Columns (Header-Level Validation)

| Column   | Required |
|----------|----------|
| SHIPID   | Yes |
| SHIPNAME | Yes |
| CUSTNO   | Yes |
| ITEM     | Yes |
| EDITION  | Yes |
| STOREEDT | Yes |
| DESCRIP  | Yes |

If any required column is missing → **File Error (ingestion stops).**

---

## Required Fields (Row-Level Validation)

| Column | Required | Failure Type |
|--------|----------|--------------|
| SHIPID | Yes | Row Error |
| ITEM   | Yes | Row Error |

---

## Warning Conditions

| Column  | Warning Condition |
|----------|------------------|
| EDITION  | Empty |

Rows with warnings are ingested but flagged.

---

## Raw Data Types

All fields are read as strings.

No special parsing required.

---

## Raw Schema Definition


SAFE_VESSELS_INVENTORY

SHIPID:     string (required, non-empty)
SHIPNAME:   string
CUSTNO:     string
ITEM:       string (required, non-empty)
EDITION:    string
STOREEDT:   string
DESCRIP:    string


---

# Global Ingestion Rules

## String Handling

- Leading/trailing whitespace trimmed
- Empty strings treated as empty

---

## Hard Fail Conditions

- Required header missing
- Required row field empty

---

## Warning Conditions

- Date parsing failure
- Invalid email format
- Missing non-required but expected business fields

Warnings do not stop ingestion.

---

# Ingestion Guarantee

If ingestion succeeds:

- All required headers exist
- All required row fields populated
- Dates parsed where applicable
- Emails validated
- AMS flag derived deterministically
- No rows silently dropped
