# Documentation Guide & Authority

This directory contains the design, specification, and explanatory documents
for the Inventory Compliance Reporter project.

Not all documents are equally authoritative.

This guide explains **which documents define system truth**, which provide
context, and how reviewers should navigate the documentation.

---

## 📌 Reading Order (Recommended)

For reviewers, maintainers, or contributors:

1. **System Contracts**
   - `SYSTEM_CONTRACTS.md`
   - `schemas/`

2. **Architecture Overview**
   - (If present) High-level architecture or overview docs

3. **Implementation Notes**
   - Phase and implementation documents

Historical or exploratory documents may be consulted last.

---

## 🔒 Authoritative Documents (Normative)

The following documents define **binding system guarantees**.
Code is expected to conform to these documents.

### System Contracts
- `SYSTEM_CONTRACTS.md`

Defines:
- Component responsibilities
- Inter-component contracts
- Assumptions and guarantees
- Failure semantics at boundaries

### Schemas
- `schemas/`

Defines:
- Canonical record shapes
- Required vs optional fields
- Field semantics and invariants

If there is a conflict between code and these documents,
**the documents are authoritative**.

---

## 📘 Supporting Documents (Non-Authoritative)

The following documents provide explanation, rationale, or implementation detail,
but do **not** define correctness.

### Implementation / Phase Documents
- Phase-based implementation plans
- Module walkthroughs
- Development notes

These documents describe *how the system was built*, not *what must be true*.

They should not be used as a source of contracts or invariants.

Each such document is marked as **Non-Authoritative**.

---

## 🗂️ Historical / Archival Documents

Some documents may exist solely for historical context
(e.g. early design explorations or abandoned approaches).

These are preserved for reference only and have no normative status.

---

## 🧭 How to Use This Documentation

- When reviewing code:  
  → Check against **System Contracts** and **Schemas**
- When understanding design intent:  
  → Consult implementation docs for context
- When resolving ambiguity:  
  → Contracts override implementation notes

---

## ✍️ Updating Documentation

- Changes to **contracts or schemas** should be intentional and reviewed
- Implementation docs may evolve freely, provided they remain non-authoritative
- New components should update contracts *before* implementation hardening

---

## Summary

- **Contracts define truth**
- **Schemas define structure**
- **Implementation docs explain decisions**
- **Code must obey contracts, not prose**

