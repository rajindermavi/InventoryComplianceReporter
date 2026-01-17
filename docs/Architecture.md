

# System Architecture

## Overview
The system is a batch-oriented data processing pipeline with interactive selection and deterministic outputs.

---

## Components

### Ingestion
- Reads Excel files
- Validates schemas
- Normalizes fields

### Domain Logic
- AMS filtering
- Inventory comparison
- Issue classification

### Reporting
- HTML report rendering
- Optional PDF generation

### Email
- Draft email generation
- Optional SMTP delivery

### UX
- CLI with interactive selection

---

## Data Flow
Excel → Parsed Records → Domain Models → Reports → Email Drafts → Run Summary

---

## Technology Stack (Recommended)
- Python 3.12+
- openpyxl
- Jinja2
- reportlab (optional PDF)
- standard library email module
- sqlite3

---

## Mangaged Data
SQLite is used as a transient runtime datastore to normalize inputs, manage selection state, and support auditable querying.

---

## Directory Structure


inventory-compliance-reporter/
├── DESIGN.md               
├── README.md               
├── pyproject.toml         
├── docs/                 
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── ingest/
│   │   ├── __init__.py
│   │   └── excel_reader.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── compare.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── html.py
│   ├── emailer/
│   │   ├── __init__.py
│   │   └── draft.py
│   └── utils/
│       ├── __init__.py
│       ├── db.py
│       └── logging.py
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   ├── test_compare.py
│   └── test_reporting.py
└── runs/
    └── .gitkeep