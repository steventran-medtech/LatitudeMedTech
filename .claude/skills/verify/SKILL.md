# /verify — Design Control V&V Gate

Run the mandatory V&V + Design Control verification pass before closing any task or merging any PR. Execute every step in order. Do not declare a task complete until all checks pass.

---

## Step 1 — Classify the Change (DC-006)

State the classification and all affected UN(s)/DI(s) before writing any code or docs:

| Class | When |
|---|---|
| **C1 Corrective** | Bug fix restoring behavior to an existing VERIFIED DI |
| **C2 Additive** | New feature traced to a new or existing user need |
| **C3 Modifying** | Change to existing behavior that affects a VERIFIED DI |
| **C4 Removing** | Removal of a feature or DI (requires Steven's explicit written waiver) |
| **C5 Emergency** | P0 security fix — Steven verbal OK; full docs required within 24h |

---

## Step 2 — Update DC Documents

**C1:** Write a regression test if none exists; include `DI-NNN-X` in the commit message. No DC doc updates unless a coverage gap is revealed.

**C2 / C3 / C4:** All of the following in the SAME commit as the code change:

1. **`design_control/DC-002`** — Add / update / mark WAIVED all affected DIs (never delete — WAIVED is the evidence)
2. **`design_control/DC-003`** — Add / update DO rows for changed code artifacts (file path + symbol must match implementation)
3. **`design_control/DC-004`** — Update RTM rows, coverage summary counts, and open-gaps table
4. **`design_control/dc_verify.py`** — Add / update `test_DI_NNN_X()` for every new or changed DI; wire into `main()`
5. **`Athena/CHANGELOG.md`** — Add entry under `[Unreleased]`
6. **`Athena/VERSION.json`** — Bump per semver rules (0.x alpha; each feature batch bumps minor)
7. **`CLAUDE.md` `## Recent Changes`** — Update with what shipped

**C5:** Minimum fix only; run Step 3 immediately; complete all doc updates within 24h.

---

## Step 3 — Run dc_verify.py

```powershell
Set-Location C:\Users\huann\LatitudeMedTech
python design_control\dc_verify.py
```

**Required result:** exit 0, 0 FAILURES, 0 ERRORS.  
WARN (exit 0) is acceptable — document in PR description.  
If exit non-zero: fix all failures before proceeding. No commit. No PR.

Report the full output verbatim.

---

## Step 4 — Cross-check UN / PR / Test Cases

For every DI touched by this change:

1. Confirm the change fully satisfies the linked UN — no ambiguity, no gaps
2. Confirm previously passing `test_DI_*` functions still pass — no regressions
3. If UN / DI / test coverage does not exist for the changed area, flag it as a gap now and do not ship without flagging

---

## Step 5 — Anti-Drift Checklist

Check every box before declaring done:

- [ ] Every new behavior is traced to a UN and a DI
- [ ] Every modified DI has its status updated (OPEN → VERIFIED or WAIVED)
- [ ] Every new DI has a `test_DI_NNN_X()` function in `dc_verify.py` wired into `main()`
- [ ] `python design_control\dc_verify.py` exits 0
- [ ] No test was silently disabled or removed without a WAIVED entry in DC-004
- [ ] `CLAUDE.md` `## Recent Changes` is updated
- [ ] `VERSION.json` and `CHANGELOG.md` are updated
- [ ] PR description includes: UNs impacted · DIs added/changed/retired · tests added/changed · dc_verify.py result

**Do not open a PR or report the task complete until all boxes are checked.**
