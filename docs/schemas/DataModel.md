# Data Model — Canonical Tables

This document defines the normalized, post-ingestion domain schemas used throughout the ICR system.

All tables below represent validated and normalized data produced by the ingestion layer.

---

# 1. Vessel

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
