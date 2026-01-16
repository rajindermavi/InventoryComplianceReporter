# Data Model Specification

## Vessel
- ship_id: str
- ship_name: str
- customer_no: str
- imo_no: str
- ship_status: str
- ship_email: str
- office_email: str
- ams: bool

---

## Vessel Inventory Row
- ship_id: str
- item: str
- onboard_edition: str
- store_edition: str
- description: str

---

## IC Inventory Row
- item: str
- current_edition: str
- description: str
- current_date: date

---

## Issue Row
- ship_id
- item
- onboard_edition
- current_edition
- issue_type: OUTDATED | MISSING_ONBOARD | MISSING_REFERENCE

---

## Vessel Report
- vessel
- issues[]
- generated_at
- source_files
