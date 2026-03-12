# InventoryComplianceReporter — User Documentation

## Overview

InventoryComplianceReporter (ICR) compares the inventory held onboard a fleet of vessels against a reference inventory from the IC catalog, then generates compliance reports and dispatches them by email to each qualifying ship.

A "run" takes three Excel files as input, processes them, and produces per-ship reports.

---

## Input Files

ICR expects exactly three Excel workbooks. Each is read from the **first worksheet only**.

### 1. IC Inventory (`safe_ic_inventory`)

The **reference catalog** — the authoritative list of items and their current editions.

| Excel Column | Description |
|---|---|
| `item` | Item identifier |
| `edition` | Current (expected) edition |
| `itmdesc` | Item description |
| `plinid` | PLin ID |
| `itmclss` | Item class |
| `upccode` | UPC code |
| `currdate` | Date of this reference data (`MM/DD/YYYY`) |

Stored as: `ic_inventory_row` — one row per item.

---

### 2. Vessels Index (`safe_vessels_index`)

The **ship master list** — which ships exist, their contact details, and whether they participate in AMS reporting.

| Excel Column | Description |
|---|---|
| `shipid` | Ship identifier |
| `shipname` | Ship name |
| `custno` | Customer number |
| `imono` | IMO number |
| `shipstat` | Ship status |
| `email` | Ship email address (used for report dispatch) |
| `note1` | Free-text note |
| `note2` | If this field contains the word `ams` (case-insensitive), the ship is flagged as AMS |
| `note3` | Free-text note |

**AMS flag:** The `ams` field is derived — it is set to `1` when `note2` contains the string `"ams"`, otherwise `0`. Only AMS-flagged ships receive reports.

Stored as: `vessel` — one row per ship.

---

### 3. Vessels Inventory (`safe_vessels_inventory`)

The **onboard stock** — what edition of each item each ship currently holds.

| Excel Column | Description |
|---|---|
| `shipid` | Ship identifier (links to vessels index) |
| `item` | Item identifier (links to IC inventory) |
| `edition` | Edition currently onboard |
| `storeedt` | Store edition |
| `shipname` | Ship name |
| `custno` | Customer number |
| `descrip` | Item description |

Stored as: `vessel_inventory_row` — one row per ship/item combination.

---

## Ingestion Processing

When ICR reads each file it applies the following steps to every row:

### Header normalization
All column headers are lowercased and whitespace-trimmed. If a duplicate header is found, the first occurrence is used and a warning is logged.

### Row-level validation
For each data row:

1. **Blank rows** — rows where every cell is empty are skipped. After 100 consecutive blank rows the file is considered finished.
2. **Required fields** — if a required column value is missing, the row is skipped and a warning is logged.
3. **Warning fields** — if an optional column value is missing, the row is still included but a warning is logged.
4. **Email validation** — ship email addresses are validated against a basic pattern. Semicolon-separated multiple addresses are supported. Invalid format logs a warning but does not drop the row.
5. **Date parsing** — `currdate` is parsed as `MM/DD/YYYY`. Excel date objects are also accepted. A failed parse logs a warning and stores `NULL`.
6. **Duplicate detection** — duplicate ship/item combinations are flagged with a warning. The row is still included.

All warnings are stored in the `validation_errors` table and are visible in the run log.

---

## Comparison Logic

After ingestion, ICR compares each AMS ship's onboard inventory against the reference catalog:

| Result | Condition | Discrepancy |
|---|---|---|
| **OK** | Onboard edition matches the current reference edition | No — may be hidden in the GUI |
| **Outdated** | Onboard edition differs from the current reference edition | Yes |
| **Missing Onboard Edition** | The item is in the reference catalog but the onboard edition field is blank | Yes |
| **Missing Reference Edition** | The item is on the ship but not found in the IC inventory at all | No — may be hidden in the GUI |

The GUI offers two options to filter non-discrepancy results out of the output:

- **Discrepancy Reports Only** — omits OK and Missing Reference items from the per-ship HTML report, showing only Outdated and Missing Onboard items.
- **Ships With Discrepancies Only** — skips vessels entirely if they have no Outdated or Missing Onboard items.

Ships with no inventory rows in the vessels inventory file produce no report.

Ships not flagged as AMS are excluded entirely — no report is generated or sent for them.

---

## Output

For each AMS ship with inventory data, ICR produces:

- An **HTML compliance report** listing each item and its status
- A **summary** (JSON) of the run results
- An **email** dispatched to the ship's address from the vessels index

---

## Export Tab

The Export tab gives access to all runs stored on this machine — not just the current one. The **Past Runs** list shows each run with its ID, timestamp, number of AMS vessels found, and total issue count.

To export, first select a destination folder using the **Browse** button.

| Button | What it does |
|---|---|
| **Export Selected** | Copies all report files from the selected past run into a subfolder (named by run ID) inside the chosen export folder. Requires a run to be selected and a folder to be set. |
| **Export Current** | Same as above but for the run that was just processed in this session, without needing to select it from the list. Requires a folder to be set. |
| **Purge Selected** | Permanently deletes all stored files for the selected run. Asks for confirmation before proceeding. |
| **Purge All** | Permanently deletes all stored runs. Asks for confirmation before proceeding. |

Purging is irreversible. Export first if you need to keep a copy.
