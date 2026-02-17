

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
├── Design.md
├── README.md
├── LICENSE
├── main.py
├── pyproject.toml
├── uv.lock
├── docs/
│   ├── Architecture.md
│   ├── CLIUX.md
│   ├── ComparisonLogic.md
│   ├── Config.md
│   ├── ProductRequirements.md
│   ├── README.md
│   ├── RequirementsSpec.md
│   ├── REVIEW_CHARTER.md
│   ├── SYSTEM_CONTRACTS.md
│   ├── Testing.md
│   ├── implementation/
│   │   ├── Implementation.md
│   │   ├── P2_PersistenceIngestion.md
│   │   ├── P3_DomainLogic.md
│   │   ├── P4_Reporting.md
│   │   ├── P5_EmailDrafting.md
│   │   ├── P6_Frontend.md
│   │   └── P7_PackagingTransport.md
│   └── schemas/
│       ├── DataModel.md
│       ├── IngestionSchemas.md
│       └── RunSummarySpec.md
├── src/
│   └── icr/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── frontend/
│       │   ├── __init__.py
│       │   ├── flow.py
│       │   ├── gui.py
│       │   ├── messages.py
│       │   └── selection.py
│       ├── backend/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── orchestrator.py
│       │   ├── ingest/
│       │   │   ├── __init__.py
│       │   │   └── excel_reader.py
│       │   ├── domain/
│       │   │   ├── __init__.py
│       │   │   ├── compare.py
│       │   │   ├── models.py
│       │   │   └── queries.py
│       │   ├── reporting/
│       │   │   ├── __init__.py
│       │   │   └── html.py
│       │   ├── emailer/
│       │   │   ├── __init__.py
│       │   │   └── draft.py
│       │   ├── delivery/
│       │   │   ├── __init__.py
│       │   │   ├── email/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── dispatch.py
│       │   │   │   ├── models.py
│       │   │   │   └── transports/
│       │   │   │       ├── __init__.py
│       │   │   │       ├── base.py
│       │   │   │       └── smtp.py
│       │   │   └── pdf/
│       │   │       ├── __init__.py
│       │   │       ├── engine.py
│       │   │       └── render.py
│       │   └── persistence/
│       │       ├── __init__.py
│       │       ├── db.py
│       │       └── paths.py
│       └── utils/
│           ├── __init__.py
│           └── logging.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_compare.py
│   ├── test_email_draft.py
│   ├── test_html_run_summary.py
│   ├── test_html_vessel_report.py
│   ├── test_ingest.py
│   ├── test_persistence_db.py
│   ├── test_persistence_integration.py
│   ├── test_persistence_paths.py
│   ├── test_reporting.py
│   ├── backend/
│   │   └── delivery/
│   │       ├── test_email_delivery.py
│   │       └── test_pdf_generation.py
│   └── frontend/
│       ├── test_flow.py
│       ├── test_messages.py
│       └── test_selection.py
├── scripts/
│   └── run_demo.py
├── samples/
│   ├── sample_1/
│   │   └── ...
│   └── sample_2/
│       └── ...
└── runs/
    └── .gitkeep
