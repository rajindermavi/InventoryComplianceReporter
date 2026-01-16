

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

inventory_compliance_reporter/
  src/icr/
    __init__.py
    cli.py
    config.py
    ingest/
      __init__.py
      excel_reader.py
      schemas.py
    domain/
      __init__.py
      models.py
      matcher.py
      compare.py
    reporting/
      __init__.py
      html.py
      pdf.py
      templates/
        report.html.j2
        email.html.j2
    emailer/
      __init__.py
      draft.py
      smtp_sender.py   # optional
    utils/
      logging.py
      paths.py
  tests/
  docs/
  pyproject.toml
