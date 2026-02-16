# Data Model — Canonical Tables

This document defines the normalized, post-ingestion domain schemas used throughout the ICR system.

All tables below represent validated and normalized data produced by the ingestion layer.

---

# 1. Vessel

## Name
vessel

## Required Fields

| Field       | Type    | Required |
|-------------|---------|----------|
| ship_id     | string  | Yes |
| ship_email  | string  | Yes |
| ams         | boolean | Yes |

## Optional Fields

| Field        | Type   | Required |
|--------------|--------|----------|
| ship_name    | string | No |
| customer_no  | string | No |
| imo_no       | string | No |
| ship_status  | string | No |
| office_email | string | No |

---

## Schema Definition

Vessel

ship_id:        string (required)
ship_name:      string
customer_no:    string
imo_no:         string
ship_status:    string
ship_email:     string (required, validated email)
office_email:   string
ams:            boolean (required)


---

# 2. VesselInventoryRow

## Name
vessel_inventory_row

## Required Fields

| Field   | Type   | Required |
|---------|--------|----------|
| ship_id | string | Yes |
| item    | string | Yes |

## Optional Fields

| Field            | Type   | Required |
|------------------|--------|----------|
| onboard_edition  | string | No |
| store_edition    | string | No |
| description      | string | No |

---

## Schema Definition

VesselInventoryRow

ship_id:            string (required)
item:               string (required)
onboard_edition:    string
store_edition:      string
description:        string


---

# 3. ICInventoryRow

## Name
ic_inventory_row

## Required Fields

| Field            | Type | Required |
|------------------|------|----------|
| item             | string | Yes |
| current_edition  | string | Yes |

## Optional Fields

| Field         | Type | Required |
|---------------|------|----------|
| description   | string | No |
| current_date  | date   | No |

---

## Schema Definition


ICInventoryRow

item:               string (required)
current_edition:    string (required)
description:        string
current_date:       date


---

# 4. IssueRow

## Name
issue_row


## Required Fields

| Field            | Type   | Required |
|------------------|--------|----------|
| ship_id          | string | Yes |
| item             | string | Yes |
| issue_type       | enum   | Yes |

## Optional Fields

| Field            | Type   | Required |
|------------------|--------|----------|
| onboard_edition  | string | No |
| current_edition  | string | Conditional |

---

## Allowed Values — issue_type

OK
OUTDATED
MISSING_ONBOARD
MISSING_REFERENCE


---

## Schema Definition

IssueRow

ship_id:            string (required)
item:               string (required)
onboard_edition:    string
current_edition:    string | null (required unless issue_type == MISSING_REFERENCE)
issue_type:         enum (required)

Rule:
- If `issue_type == MISSING_REFERENCE`, `current_edition` must be `null`.
- Otherwise, `current_edition` must be a non-empty string.

enum IssueType:
OK
OUTDATED
MISSING_ONBOARD
MISSING_REFERENCE


---

# 5. VesselReport

## Name
vessel_report


## Required Fields

| Field         | Type              | Required |
|---------------|-------------------|----------|
| vessel        | Vessel            | Yes |
| issues        | list[IssueRow]    | Yes |
| generated_at  | datetime          | Yes |
| source_files  | list[string]      | Yes |

---

## Schema Definition

VesselReport

vessel:         Vessel (required)
issues:         list[IssueRow] (required)
generated_at:   datetime (required)
source_files:   list[string] (required)
