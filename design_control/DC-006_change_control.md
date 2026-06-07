# DC-006 — Change Control
**Document:** DC-006 · Version 1.2 · 2026-06-07  
**Approved by:** Steven Tran

---

## Change Order Register

Every CO gets a unique ID at kickoff. Assign the next available CO-NNN here before any other step.

| CO ID | Date | Class | Tier | Branch | DIs Affected | Status |
|---|---|---|---|---|---|---|
| CO-001 | 2026-06-05 | C2 | — | chore/add-change-order-skill | — | MERGED |
| CO-002 | 2026-06-07 | C3 | 2 | feat/co-002-change-order-overlap-models-co-ids | — | MERGED |
| CO-003 | 2026-06-07 | C2 | 3 | feat/co-003-un-003-023-rag-reports-historical | DI-003-C, DI-003-D, DI-023-B, DI-023-C | MERGED (PR #89) |

| CO-004 | 2026-06-07 | C2 | 2 | feat/co-004-un-031-tab-singleton | DI-031-A, DI-031-B | MERGED (4f20d0e, PR #92) |
| CO-005 | 2026-06-07 | C3 | 3 | chore/co-005-un-002-document-queue | DI-002-E (mod), DI-002-F, DI-002-G | MERGED |
| CO-006 | 2026-06-07 | C2 | 2 | feat/co-006-consulting-learning-reports | DI-032-A, DI-032-B, DI-023-D | MERGED (register corrected 2026-06-07 — branch showed zero diff vs main) |

| CO-007 | 2026-06-07 | C3 | 1 | chore/co-007-intro-exit-variations | — | MERGED |
| CO-008 | 2026-06-07 | C3 | 3 | feat/co-008-un-019-startup-under-10s | DI-019-K (new) | MERGED (1a7525b, PR #91) |
| CO-009 | 2026-06-07 | C2 | 1 | feat/co-009-un-034-progress-bar-no-backward | — | MERGED |
| CO-010 | 2026-06-07 | C2/C3 | 3 | feat/co-008-un-033-voice-ready-latency | UN-033 (new), UN-034 (new), DI-033-A/B/C (VERIFIED), DI-030-D/E (new), DI-034-A-F (new) | MERGED |
| CO-011 | 2026-06-07 | C2 | 3 | feat/co-011-un-033-process-integrity | UN-034 (formal registration), DI-034-A (corrected test), DI-034-B, DI-034-C, DI-034-D, DI-034-E, DI-034-F | MERGED |

| CO-012 | 2026-06-07 | C3 | 2 | co-011-fresh | DI-007-F (new, VERIFIED), DI-002-H (new, VERIFIED), DI-002-I (new, VERIFIED) | MERGED (0fc5b41, PR #100) |
| CO-013 | 2026-06-07 | C2 | 2 | feat/co-013-un-019-splash-done-signal | DI-019-L (new, P0), DI-019-G (verification method update) | MERGED (200e91a, PR #104) |
| CO-014 | 2026-06-07 | C1 | 2 | fix/co-014-di-002-j-reviewview-duplicate-import | DI-002-J (new, VERIFIED) | MERGED (dcff017, PR #102) |
| CO-015 | 2026-06-07 | C1 | 2 | fix/co-015-di-002-k-reviewview-approved-close-paren | DI-002-K (new, VERIFIED) | MERGED (68b5ae8, PR #103) |

| CO-016 | 2026-06-07 | C2/C3 | 3 | feat/co-016-multi-requirement-batch | DI-003-C (mod), DI-007-G, DI-007-H, DI-008-C, DI-011-C, DI-022-A (mod), DI-035-A, DI-036-A, DI-036-B, DI-036-C | MERGED |
| CO-017 | 2026-06-07 | C2/C3 | 3 | feat/co-017-approval-gate-audit | DI-035-A (mod), DI-036-A (verified), DI-036-B (verified), DI-036-C (verified), DI-036-D (new), DI-036-E (new); DC-002 bulk status sync; test_DI_036_D, test_DI_036_E added | MERGED (PR #106) |
| CO-018 | 2026-06-07 | C1/C2 | 3 | chore/co-018-gap-closure-partial-open | DI-007-A, DI-008-A, DI-008-B, DI-010-C, DI-015-F (PARTIAL→VERIFIED: new static tests); DI-019-K, DI-019-L, DI-022-A, DI-023-B/C/D, DI-032-A/B (OPEN→VERIFIED or PARTIAL); iso.org removed from rag_agent.py Tavily include_domains; DI-032-B test bug fixed (wrong di id); DC-002 v3.6, DC-004 v3.4 bulk sync; manual verification protocol created | OPEN |

**Status values:** OPEN · MERGED · ABANDONED  
**Next available ID:** CO-019

---

## Purpose

This document defines the mandatory process for any change to Athena that
affects a functional behavior — adding a feature, modifying an existing one,
or removing one. Its goal is to ensure that no change is made without
traceability, no requirement is added without a test, and no test is removed
without a documented rationale.

"Change" means any of: new agent, new API route, modified behavior, changed
constant, removed feature, or updated system prompt.

---

## Change Classifications

| Class | Definition | Approval Required |
|---|---|---|
| **C1 — Corrective** | Bug fix that restores behavior to match an existing DI | Steven (standard review) |
| **C2 — Additive** | New feature traced to a new or existing user need | Steven (full DC process) |
| **C3 — Modifying** | Change to existing behavior that affects a VERIFIED DI | Steven (full DC process + re-verification) |
| **C4 — Removing** | Removal of a feature or DI | Steven (explicit written waiver) |
| **C5 — Emergency** | P0 security fix that cannot wait for full process | Steven verbal OK; full docs within 24h |

---

## Full Change Control Process (C2, C3, C4)

Follow these steps in order. Do not skip or reorder.

### Step 1 — Impact Assessment

Before writing a single line of code, answer:

1. Which **User Need(s)** (UN-xxx) does this change serve?
   - If none: the change is undocumented scope. Either find the UN it belongs to,
     add a new UN to DC-001, or reject the change.
2. Which existing **Design Inputs** (DI-xxx) are affected?
   - List all DIs that will CHANGE or be RETIRED.
3. Which existing **Verification Tests** will be affected?
   - List all `test_DI_xxx_Y` functions that will need updating.

Record this in the PR description before any review.

### Step 2 — Update Design Inputs (DC-002)

For each affected DI:
- **Modifying**: Update the requirement statement to reflect the new behavior.
  Change status to OPEN until the test passes.
- **Retiring**: Mark status WAIVED with a rationale line. Do NOT delete — a
  retired DI is evidence that the requirement was intentionally removed.
- **Adding**: Assign the next available DI-NNN-X ID. Set status to OPEN.

### Step 3 — Update Design Outputs (DC-003)

For each new or changed code artifact:
- Add or update the row in the relevant DO section.
- File path and symbol must match the actual implementation.

### Step 4 — Write or Update Verification Tests

For every new or changed DI, there must be a test function in `dc_verify.py`:
```python
def test_DI_NNN_X():
    """DI-NNN-X: <one-line description of what is being checked>"""
    ...
    # Fail with a clear message that names the DI and explains the fix
```

The test must:
- Run without the server (static mode) unless impossible.
- Produce a specific, actionable failure message.
- Pass on the first run after implementation.

### Step 5 — Update Traceability Matrix (DC-004)

Add, update, or mark WAIVED the affected rows. Verify:
- Every new DI has a row.
- Every new row has a test function name.
- Coverage summary numbers are updated.
- Open traceability gaps table is current.

### Step 6 — Run dc_verify.py

```powershell
python design_control\dc_verify.py
```

All tests must PASS before the PR is created. No exceptions for P0 items.
PARTIAL items must be documented in the PR description.

### Step 7 — Version and Changelog

- Bump `Athena/VERSION.json` per the semver rules in CLAUDE.md.
- Add an entry to `Athena/CHANGELOG.md` under `[Unreleased]`.
- Update the `## Recent Changes` section of CLAUDE.md.
- Update the design control document versions if structural changes were made.

### Step 8 — PR Review and Merge

- PR description must include: UN(s) impacted, DIs added/changed/retired, tests added/changed, verification result.
- Steven reviews and approves.
- dc_verify.py runs clean in the PR environment.
- Merge to main.

---

## Corrective Fix Process (C1)

For bug fixes that restore a behavior to match an existing VERIFIED DI:

1. Identify the DI that was violated by the bug.
2. Write a regression test if one does not exist.
3. Fix the bug.
4. Run `dc_verify.py --di <DI-ID>` to confirm the fix.
5. Include DI reference in the commit message: `fix: restore DI-015-B shell=False enforcement`.
6. No DC document updates required unless the bug reveals a gap in the test coverage.

---

## Emergency Fix Process (C5)

For P0 security issues only:

1. Get Steven's verbal approval.
2. Make the minimum fix.
3. Run `python design_control\dc_verify.py --di DI-015` immediately.
4. Within 24 hours: document the change in DC-002/DC-003/DC-004, write or update tests, update CHANGELOG.
5. Note: Emergency use ≥ 3 times → process gap; open a CAPA.

---

## Anti-Drift Checklist

Before any PR merge, confirm:

- [ ] Every new behavior is traced to a UN and DI.
- [ ] Every modified DI has its status updated.
- [ ] Every new DI has a `test_DI_NNN_X` function in `dc_verify.py`.
- [ ] `python design_control\dc_verify.py` exits 0.
- [ ] No test was silently disabled or removed without a WAIVED entry in DC-004.
- [ ] CLAUDE.md `## Recent Changes` section is updated.
- [ ] VERSION.json and CHANGELOG.md are updated.

---

## Prohibited Actions

These actions are never permitted regardless of urgency:

| Action | Why |
|---|---|
| Merging a PR that causes `dc_verify.py` to exit non-zero | Breaks verified traceability |
| Deleting a test function without a WAIVED entry in DC-004 | Silent coverage loss |
| Adding a feature without a traced UN | Undocumented scope — cannot be verified or maintained |
| Changing `DISCLAIMER` or `LABEL` constants without DC process | Output integrity controls |
| Raising `WAKE_THRESHOLD` above 0.35 without a new CAPA | Reverts CAPA-Voice-001 fix |
| Setting `SILENCE_DURATION` below 0.8 or above 2.0 without a new CAPA | Voice quality regression |
| Using `shell=True` in any subprocess call | Security violation |

---

## New Agent Onboarding Checklist

When adding a new agent:

1. Add a row to the Agent Roster table in `.claude/rules/agents.md`.
2. Create `.claude/agents/<agent-name>.md` persona file.
3. Register in `AGENT_DISPLAY`, `AGENT_ETA_SECONDS`, and `AGENT_TAB` in `App.jsx`.
4. Register in the `MAP` in `AgentsView` (short-id to full WS name).
5. Add the agent to `agent_learning.py` learning sources.
6. Add the agent to `learning_sources.py`.
7. Wire `submit_for_review()` on any output the agent generates.
8. Stamp `last_learning` at end of every learn run.
9. Identify which UN(s) this agent serves and add DIs to DC-002.
10. Add verification tests to `dc_verify.py`.
11. Update DC-003, DC-004.
12. Run `dc_verify.py` — must pass before merging.
