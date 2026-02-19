
# Sample Submission Scenarios

## InventoryComplianceReporter Behavior Demonstration

This folder contains a curated set of sample submission files designed to illustrate how **InventoryComplianceReporter (ICR)** responds to different data conditions.

The purpose of these examples is to provide transparency into:

* How the system behaves when data is complete and well-formed
* How it handles realistic but imperfect data
* How it responds to structurally invalid or broken submissions
* What output reports are generated in each scenario

For every submission example, we provide:

1. The input files as submitted
2. A brief description of the data condition being demonstrated
3. The resulting system response (including generated report output or validation behavior)

These examples are intended to be representative of the kinds of input conditions 
that can occur in real-world workflows.

---

# SAMPLES

## SAMPLE 1

* 3 ships
    * ship 01: AMS
    * ship 02: AMS
    * ship 03: Not AMS

* Scenario
    * ship 01: 3 OK
    * ship 02: 1 OK, 2 outdated, 1 missing reference edition
        * item 4: compass, no edition number
    * ship 03: No Report

## SAMPLE 2

* 3 ships
    * ship 01: AMS
    * ship 02: AMS
    * ship 03: Not AMS

* Scenario
    * ship 01: 3 OK
    * ship 02: 1 Missing Onboard Edition, 2 outdated, 1 missing reference edition
        * item 1: Vessel inventory edition number empty
        * item 4: compass, missing from ic inventory
    * ship 03: No Report

## SAMPLE 3

* 3 ships
    * ship 01: AMS
    * ship 02: AMS
    * ship 03: AMS
    * ship 04: Missing from vessels index

* Scenario
    * ship 01: 2 items - vessel inventory duplicates
        * item 01: vessel inventory - duplicated item both editions up to date
        * item 03: vessel inventory - duplicated item. One edition up to date. One edition out of date.
    * ship 02: 2 items - ic inventory duplicates
        * item 2: book - first sorted edition matches: OK
        * item 2: regulation - first sorted edition does not match: Outdated
    * ship 03: No inventory items
    * ship 04: No Report


