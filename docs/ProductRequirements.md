

# Goal

Automate monthly (or on-demand) reporting to customers/vessels whose onboard inventory item editions are outdated relative to a central “current edition” catalog. Generate per-vessel reports and prepare emails to vessel and office contacts.

# Inputs

Three Excel files (first worksheet only as described in RawInputs.md):

* SAFE_VESSELS_INDEX_YYYYMMDD*.XLSX
    - Contains vessel list and whether the vessel is in AMS scope.
* SAFE_VESSELS_INVENTORY_YYYYMMDD*.XLSX
    - Contains onboard inventory items + edition per vessel.
* SAFE_IC_INVENTORY_YYYYMMDD*.XLSX
    - Contains authoritative “current edition” per item.

# High-level workflow

* Load all three spreadsheets (sheet 1 only).
* Filter vessels to AMS-marked vessels in the Index file (column mapping defined in config).
* Present a vessel selection UI: All / None / select vessels.
* For each selected vessel:
    - Find all its onboard inventory items + onboard edition.
    - For each onboard item, lookup the “current edition” in IC inventory.
    - If editions do not match, record an “outdated” row for that vessel.
    - Generate a vessel-specific report (HTML + optional PDF).
    - Create an email draft addressed to vessel email + office email.
    - If no outdated items, email states “no items out of date per our records”.
* Prepare to send: either (a) generate .eml files, (b) send via SMTP, or (c) integrate with an email API (future).

# Primary user stories

* Ops user runs the program, selects vessels, and produces ready-to-send emails.
* Ops user can run monthly without manual spreadsheet comparisons.
* Ops user can audit outputs: see which items were flagged and why.

# Functional requirements

* FR1: Parse three spreadsheets (first sheet only).
* FR2: Identify AMS vessels from Index file.
* FR3: Vessel selection interface (All / None / per vessel).
* FR4: Compare onboard edition vs current edition for each item.
* FR5: Generate per-vessel report in HTML; optionally render PDF.
* FR6: Build email drafts per vessel using ship email + office email.
* FR7: If no outdated items, produce “All up to date” email.
* FR8: Batch processing across selected vessels.
* FR9: Logging and run summary (counts, errors, skipped rows).

# Non-functional requirements

* NFR1: Deterministic outputs: same inputs => same results.
* NFR2: Clear audit trail: run folder contains copies of inputs’ filenames, selection list, generated reports/emails, and summary JSON.
* NFR3: Robust to messy data (blank cells, whitespace, case differences).
* NFR4: Handle large files (thousands of rows) within reasonable time on a laptop.
* NFR5: No secrets embedded in repo (email credentials via env/secret store).
* NFR6: Unit tests for parsing, matching, and report generation.

# Out of scope (initial version)

* Two-way confirmation tracking (customers replying and updating state).
* Automatic update of inventory databases.
* UI beyond minimal (CLI + simple TUI/GUI). (We can add later.)

# Acceptance criteria (MVP)

* Given sample input files:
    - Correct AMS filtering.
    - Correct per-vessel outdated item detection.
    - Generates an HTML report + email draft per selected vessel.
    - Produces a run summary that lists vessels processed and number of mismatches.
    - No crash on missing/blank editions; instead logs and continues.