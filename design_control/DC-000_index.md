# Athena Design Control Framework
**System:** Athena · Latitude MedTech LLC  
**Version:** 1.0 · 2026-06-05  
**Owner:** Steven Tran (Managing Partner/CEO)  
**Status:** Alpha — Internal Use Only

---

## Purpose

This framework enforces disciplined traceability from user needs through
design inputs, design outputs, verification tests, and change control.  
It prevents three failure modes that cause consulting software to drift and
degrade: (1) features added without requirement backing, (2) requirements
with no corresponding tests, and (3) changes that silently break passing tests.

Governed by ISO 13485:2016 §7.3 (Design and Development) and 21 CFR Part
820 Subpart C (Design Controls) principles, applied to the Athena AI platform.

---

## Document Index

| # | Document | Purpose |
|---|---|---|
| DC-001 | [Intended Use & User Needs](DC-001_intended_use.md) | What Athena is, who uses it, under what constraints, and the enumerated user needs |
| DC-002 | [Design Inputs](DC-002_design_inputs.md) | Specific, verifiable requirements derived from each user need |
| DC-003 | [Design Outputs](DC-003_design_outputs.md) | Code artifacts, APIs, and data structures that implement each design input |
| DC-004 | [Traceability Matrix](DC-004_traceability_matrix.md) | End-to-end linkage: UN → DI → Design Output → Verification Test |
| DC-005 | [Verification Protocol](DC-005_verification_protocol.md) | Procedures, pass/fail criteria, and run instructions for each test |
| DC-006 | [Change Control](DC-006_change_control.md) | Mandatory process for adding, modifying, or removing features |
| dc_verify.py | [Automated Verifier](dc_verify.py) | Executable Python script — each test function maps to a DI number |

---

## Quick-Start: Running Verification

```powershell
# From LatitudeMedTech root — activate venv first
cd "C:\Users\huann\LatitudeMedTech"
.\Athena\venv\Scripts\activate

# Static checks (no server required)
python design_control\dc_verify.py

# Full check including live API (server must be running)
python design_control\dc_verify.py --live

# Single DI (e.g., after changing a specific feature)
python design_control\dc_verify.py --di DI-010
```

Exit code 0 = all active tests pass. Non-zero = failures; see summary.

---

## Framework Maintenance Rules

1. **Every PR must update this framework** if it adds, removes, or changes a
   functional behavior. See DC-006 for the full change control process.
2. **Every DI must have at least one test** in `dc_verify.py` before the
   implementing PR may merge.
3. **Traceability matrix is the arbiter** — if a behavior is not in DC-004,
   it is undocumented scope and must be added or removed.
4. **CAPA triggers apply** — 3+ DI failures on any run → open a CAPA in
   `Athena/ops/hr/CAPA-DC-NNN.md` per the CAPA protocol in CLAUDE.md.
5. **Version bump required** on any schema change to this framework (new UN,
   new DI, retired DI). Update the version line at the top of this file.

---

## Status Legend

| Symbol | Meaning |
|---|---|
| VERIFIED | Automated test passes; design output confirmed |
| PARTIAL | Manual verification only; automated test pending |
| OPEN | Requirement defined; no design output yet (planned work) |
| WAIVED | Requirement deferred with documented rationale |
