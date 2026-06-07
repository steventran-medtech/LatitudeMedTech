# /change-order — Design Control Change Order

Full-cycle command for adding or changing User Needs (UN) and Product Requirements (DI). Runs the complete DC-006 process: define → document → implement → verify → human gate → merge.

**Usage:**
```
/change-order <description of the change>
```

If no args are provided, ask: "What is the change? Describe the user need or requirement you want to add or modify."

---

## Risk Tier — Run This First

Before any other step, classify the change by risk tier and wait for confirmation.

### T-A: Map the change

List every file or area the change touches.

### T-B: Protected path check (auto Tier 3)

If **any** touched file appears below, classify **Tier 3 — no exceptions:**

| Protected Path | Examples |
|---|---|
| Compliance / SME gate | `compliance.md`, hard-stop blocks, RAC/regulatory review gates |
| Audit trail | `review_queue`, `audit_log`, `submit_for_review()`, `Memory` write paths |
| Auth / session | `.athena.key`, auth middleware, session token logic, `authHdr()` |
| Data isolation | Client data scoping, `kb_annotations.client_id` |
| Orchestrator routing | `orchestrator.py`, `voice_bridge.py` dispatch, `tool_use` routing, agent `MAP` in `App.jsx` |

### T-C: Classify (if no protected path hit)

| Tier | Definition | Examples |
|---|---|---|
| **Tier 1 — Cosmetic** | No logic, no branching, no data path | CSS value, label text, comment, icon, version string |
| **Tier 2 — Localized Functional** | Affects one module; no shared contracts changed | Single-agent prompt, new isolated API route, self-contained UI component |
| **Tier 3 — Core / Shared / Critical** | Touches shared utilities, cross-module behavior, or any VERIFIED DI | Shared helper, cross-agent behavior, DC-002 DI change, any file with an existing `test_DI_*` |

When uncertain between two tiers, assign the higher one.

### T-D: State and wait

State the tier and your reasoning. **STOP — do not proceed until Steven confirms.**

### T-E: Execute only the tier's steps

**Tier 1 — Cosmetic:**
1. Implement
2. If the changed file is referenced by any `test_DI_*`, run `python design_control\dc_verify.py --di <that-prefix>`; otherwise skip
3. Commit to current branch

**Tier 2 — Localized Functional:**
1. Implement
2. `python design_control\dc_verify.py --di <affected-DI-prefix>`
3. Run all DIs under the same UN: `python design_control\dc_verify.py --di <UN-prefix>`
4. Fix any failures, then commit to current branch

**Tier 3 — Core / Shared / Critical:**
Continue through Steps 0–11 below in full.

---

## Step 0 — Parse and Clarify

Read the args. Before writing anything, state back:

1. **What** is being changed (user need, requirement, or both)
2. **Why** (the business or operational reason)
3. **Scope** (is this a new UN, a new DI under an existing UN, or a modification to an existing UN/DI?)

If any of these are ambiguous, ask one focused question. Then proceed — do not ask multiple questions in sequence.

---

## Step 1 — Classify the Change

Read `design_control/DC-006_change_control.md` and assign exactly one class:

| Class | When |
|---|---|
| **C1 — Corrective** | Bug fix restoring behavior to an existing VERIFIED DI |
| **C2 — Additive** | New feature or capability — adds a new UN and/or DI |
| **C3 — Modifying** | Changes existing verified behavior — modifies an existing UN or DI |
| **C4 — Removing** | Retires a UN or DI (requires Steven's explicit written waiver) |
| **C5 — Emergency** | P0 security fix — Steven verbal OK; full docs required within 24h |

State the class and which existing UN(s)/DI(s) are affected before proceeding.

**C4 hard stop:** Do not retire a UN or DI without Steven's explicit written approval in this conversation. State: "C4 changes require your explicit written approval. Please confirm the UN/DI to retire and your rationale before I continue."

---

## Step 2 — Read Current Design Control State

Read the following files to determine the next available IDs and verify context:

```powershell
# Read to find highest existing UN-NNN
Get-Content design_control\DC-001_intended_use.md

# Read to find highest existing DI-NNN-X  
Get-Content design_control\DC-002_design_inputs.md

# Read to understand current traceability state
Get-Content design_control\DC-004_traceability_matrix.md
```

Report:
- Highest existing UN number (e.g., "Current max: UN-022 → next will be UN-023")
- Highest existing DI number and letter for the affected UN
- Any existing UNs or DIs this change overlaps with (flag if a new UN is redundant with an existing one)

---

## Step 3 — Draft New / Updated UN and DI Entries

**For C2 (Additive) or C3 (Modifying):**

Draft the entries before writing them to files. Present them to Steven as a table:

### New User Need (if adding a new UN):

| Field | Value |
|---|---|
| ID | UN-0XX (next available) |
| User Need | "I need to…" — stated from user perspective |
| Priority | P0 / P1 / P2 |

### New Design Inputs (for every new UN or modified UN):

| ID | Source | Requirement Statement | Verification Method | Priority | Status |
|---|---|---|---|---|---|
| DI-0XX-A | UN-0XX | Specific, testable "shall" statement | How dc_verify.py will check this | P0/P1 | OPEN |
| DI-0XX-B | UN-0XX | … | … | … | OPEN |

Rules for DI statements:
- Use "shall" not "should" or "may"
- Testable without ambiguity — a reader must be able to determine pass or fail
- Each DI covers one behavior, not multiple
- Verification method must be achievable by dc_verify.py (static or live)

**For C1 (Corrective):** Skip Step 3. Go directly to Step 5 with the existing DI reference.

**For C3 (Modifying):** Show both the OLD and NEW statement for each changed DI. Steven must explicitly confirm each modification.

---

## Step 4 — Update Design Control Documents

Update all of the following in order. All edits go into the SAME commit as the code changes (Step 6).

### 5A — DC-001 (if new UN)
Edit `design_control/DC-001_intended_use.md`:
- Add the new UN row to the correct business-line table
- Increment the document version number (e.g., 1.3 → 1.4)
- Update the date to today

### 5B — DC-002 (always for C2/C3)
Edit `design_control/DC-002_design_inputs.md`:
- **C2:** Add a new `### UN-0XX — <Title>` section with all new DI rows
- **C3:** Update the existing DI rows; change status to OPEN until tests pass; never delete — use WAIVED with rationale if retiring
- Increment the document version and update the date

### 5C — DC-003
Edit `design_control/DC-003_design_outputs.md`:
- Add placeholder rows for code artifacts that WILL be created or modified
- Update after implementation (Step 6) with exact file paths and symbols
- Increment version and date

### 5D — DC-004 (Traceability Matrix)
Edit `design_control/DC-004_traceability_matrix.md`:
- Add new RTM rows: UN → DI → Design Output → Test function name (placeholder `TBD` until tests written)
- Update the coverage summary counts
- If a gap exists, add it to the open-gaps table
- Update `TBD` placeholders after Step 6
- Increment version and date

### 5E — DC-005 (Verification Protocol)
Edit `design_control/DC-005_verification_protocol.md`:
- Add a test procedure entry for each new DI: test ID, DI reference, preconditions, steps, expected result
- Increment version and date

---

## Step 6 — Write Verification Tests

Add a `test_DI_NNN_X()` function to `design_control/dc_verify.py` for **every new or changed DI**. Every test must be written to the standards below before the file is saved.

---

### 6A — Test Structure (AAA)

Every test follows **Arrange → Act → Assert**:

```python
def test_DI_NNN_X():
    """DI-NNN-X: <one-line statement of what pass/fail means>"""
    # ARRANGE — set up any inputs, paths, or state needed
    target_file = Path(__file__).parent.parent / "Athena" / "path" / "to" / "file.py"

    # ACT — perform the check
    content = target_file.read_text(encoding="utf-8")
    result = "expected_symbol_or_string" in content

    # ASSERT — fail with a message that names the DI, states what's wrong, and says how to fix it
    assert result, (
        "FAIL DI-NNN-X: <what is missing or wrong>\n"
        "Fix: <exact action to take to make this pass>"
    )
    return True
```

**Non-negotiable rules:**
- One test per DI — never check two DIs in one function
- Always `return True` at the end (dc_verify.py `main()` counts truthy returns)
- Docstring must be: `"DI-NNN-X: <what is being checked>"` — no multi-line, no vague descriptions
- Function name is exactly `test_DI_NNN_X` (underscores, no dashes, no camelCase)

---

### 6B — Static-First Hierarchy

Choose the lowest tier that can verify the DI. Do not reach for a live check when a static one suffices.

| Tier | When to use | Example |
|------|-------------|---------|
| **T1 — Constant / config** | DI specifies a value (threshold, timeout, flag) | Read the source file, assert the constant equals the required value |
| **T2 — Symbol existence** | DI specifies that a function, class, or route exists | Import the module or grep the source for the symbol name |
| **T3 — Source pattern** | DI specifies structural behavior expressed in code | Read the file, assert a required string or pattern is present |
| **T4 — File / artifact** | DI specifies that a file or directory must exist | `assert Path(...).exists()` |
| **T5 — Live API / DB** | DI can only be verified with the server running | Wrap with `if not LIVE_MODE: return True` — must pass static mode too |

If a DI requires T5, add `if not LIVE_MODE: return True` so the test is skippable in static mode but still wired into `main()`. Document the live-only requirement in the DC-005 test procedure entry.

---

### 6C — Assertion Message Standard

Every `assert` failure message must answer three questions in order:

```
"FAIL DI-NNN-X: <what is wrong — be specific, name the file/symbol/value>\n"
"Fix: <what to add, change, or set to make this pass>"
```

Bad (vague, unhelpful):
```python
assert result, "FAIL DI-012-A: check failed"
```

Good (specific, actionable):
```python
assert result, (
    "FAIL DI-012-A: WAKE_THRESHOLD in voice_bridge.py is above 0.35\n"
    "Fix: Set WAKE_THRESHOLD = 0.35 or lower in Athena/voice/voice_bridge.py"
)
```

For multi-condition checks, one assert per condition so the failure message is unambiguous:

```python
assert target_file.exists(), (
    "FAIL DI-015-A: voice_bridge.py not found at expected path\n"
    "Fix: Confirm Athena/voice/voice_bridge.py exists"
)
content = target_file.read_text(encoding="utf-8")
assert "shell=False" in content or "shell" not in content, (
    "FAIL DI-015-A: shell=True detected in voice_bridge.py\n"
    "Fix: Replace shell=True with shell=False in all subprocess calls"
)
```

---

### 6D — Determinism Requirements

Tests must produce the same result on every run regardless of environment state:

- **No time-dependent assertions** — do not assert on timestamps, file ages, or `datetime.now()`
- **No randomness** — do not assert on outputs that vary by run
- **No network calls in static mode** — static tests must work offline
- **No state mutation** — tests must not write files, modify the DB, or call destructive endpoints
- **Absolute paths via `Path(__file__)`** — never hardcode `C:\Users\...`; always anchor to the repo root relative to the script's own location

```python
# Correct — portable
REPO_ROOT = Path(__file__).parent.parent
target = REPO_ROOT / "Athena" / "server.py"

# Wrong — machine-specific
target = Path(r"C:\Users\huann\LatitudeMedTech\Athena\server.py")
```

---

### 6E — Edge Case Coverage

Each test covers the DI's **boundary condition**, not just the happy path. Ask: "What is the smallest violation that would still pass this test?" Close that gap.

Examples:

| DI type | Happy path only (insufficient) | With boundary (correct) |
|---------|--------------------------------|------------------------|
| Constant ≤ 0.35 | Assert `WAKE_THRESHOLD` exists | Assert `WAKE_THRESHOLD <= 0.35` — value must be within the required range, not just present |
| String present in output | Assert `"LABEL"` is in the file | Assert the exact required label string, not a substring that could match something unrelated |
| Endpoint exists | Assert route is defined | Assert route method signature matches spec (POST not GET, etc.) |
| File must exist | Assert file exists | Assert file is non-empty and importable (if Python) |

---

### 6F — Wiring into main()

After writing the function, add it to `main()` using the same pattern as existing tests:

```python
def main():
    ...
    run_test("DI-NNN-X: <short label>", test_DI_NNN_X)
    ...
```

The `run_test` call must appear in DI numeric order within `main()`. Do not append to the end if there are lower-numbered DIs after the insertion point.

---

### 6G — Final Self-Check Before Saving

Before saving `dc_verify.py`, verify each new test against this checklist:

- [ ] Docstring matches `"DI-NNN-X: <what is being checked>"`
- [ ] Function name is `test_DI_NNN_X` (underscores, no dashes)
- [ ] Follows AAA structure — Arrange, Act, Assert are clearly separated
- [ ] Uses the lowest viable tier (T1–T4 preferred over T5)
- [ ] Every assert has a DI-named failure message with a Fix line
- [ ] No hardcoded absolute paths — uses `Path(__file__).parent.parent`
- [ ] No state mutation — test is read-only
- [ ] Returns `True` on pass
- [ ] Wired into `main()` in DI numeric order
- [ ] DC-004 TBD placeholder updated with the actual function name

Update DC-004 `TBD` placeholders with the actual function names after all tests are written.

---

## Step 7 — Implement Code Changes

Make the code changes required to satisfy all new DIs. Follow the constraints in `.claude/rules/`:
- No `shell=True` in subprocess calls (DC-006 prohibited action)
- No DISCLAIMER or LABEL constant changes without DC process
- Follow the architecture rules in `.claude/rules/architecture.md`

Update DC-003 with the exact file paths and symbol names of all new or changed artifacts.

---

## Step 8 — Update Ancillary Files

### 8A — CHANGELOG
Edit `Athena/CHANGELOG.md`:
- Add an entry under `[Unreleased]` with the UNs and DIs addressed

### 8B — VERSION
Edit `Athena/VERSION.json`:
- Bump per semver rules: new UN/feature = minor bump (0.5.2 → 0.5.3); bug fix = patch bump

### 8C — CLAUDE.md
Edit `CLAUDE.md`:
- Update `## Recent Changes` with what shipped

---

## Step 9 — Run dc_verify.py

```powershell
Set-Location C:\Users\huann\LatitudeMedTech
python design_control\dc_verify.py
```

**Required result:** exit 0, 0 FAILURES, 0 ERRORS.

Report the full output verbatim.

If exit non-zero: fix all failures before proceeding. No commit. No PR.

WARN (exit 0) is acceptable — document in the PR description.

---

## Step 10 — Anti-Drift Checklist

Check every box:

- [ ] Every new UN is stated from the user's perspective ("I need to…")
- [ ] Every new DI has a "shall" statement that is testable as pass/fail
- [ ] Every new DI is linked to a UN in DC-004
- [ ] Every new DI has a `test_DI_NNN_X()` function in `dc_verify.py` wired into `main()`
- [ ] Every modified DI has its status updated (OPEN until test passes, then VERIFIED)
- [ ] No DI or test was deleted — retired items use WAIVED with rationale
- [ ] `python design_control\dc_verify.py` exits 0 with 0 FAILURES
- [ ] DC-001, DC-002, DC-003, DC-004, DC-005 all have updated version numbers and dates
- [ ] CHANGELOG.md has an [Unreleased] entry
- [ ] VERSION.json is bumped
- [ ] CLAUDE.md `## Recent Changes` is updated

Report each box as checked ✅ or blocked ❌ with reason.

---

## Step 11 — Branch, Commit, PR, and Merge

### 11A — Create branch
```powershell
# Branch naming: feat/un-NNN-<kebab-description> for C2
# fix/di-NNN-<kebab-description> for C1
# chore/modify-un-NNN-<kebab-description> for C3
git checkout -b feat/un-NNN-<short-description>
```

### 11B — Stage and commit all changes together

Stage all DC documents, code files, CHANGELOG, VERSION, CLAUDE.md in one commit:

```powershell
git add design_control/DC-001_intended_use.md
git add design_control/DC-002_design_inputs.md
git add design_control/DC-003_design_outputs.md
git add design_control/DC-004_traceability_matrix.md
git add design_control/DC-005_verification_protocol.md
git add design_control/dc_verify.py
git add Athena/CHANGELOG.md
git add Athena/VERSION.json
git add CLAUDE.md
# Add all changed code files
git add <code files>
```

Commit message format:
```
feat(un-NNN): <short description of the user need>

UNs: UN-NNN — <title>
DIs: DI-NNN-A (OPEN→VERIFIED), DI-NNN-B (OPEN→VERIFIED)
Tests: test_DI_NNN_A, test_DI_NNN_B added
dc_verify.py: exit 0, 0 FAILURES

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### 11C — Push, open PR, and merge

```powershell
git push -u origin feat/un-NNN-<short-description>
```

PR description must include:
- **User Needs impacted:** UN-NNN — title
- **Design Inputs added/changed/retired:** table of DI IDs and status changes
- **Tests added/changed:** list of `test_DI_NNN_X` functions
- **dc_verify.py result:** full output (copy verbatim)
- **Anti-drift checklist:** all boxes checked

```powershell
gh pr create --title "feat(un-NNN): <short description>" --body "..."
```

### 11D — Merge to main

Squash-merge immediately after the PR is created:

```powershell
gh pr merge --squash --delete-branch
```

Report the merge commit SHA and confirm the branch is deleted.

---

## Quick Reference

| Step | Action | Gate |
|---|---|---|
| 0 | Parse and clarify | — |
| 1 | Classify C1–C5 | — |
| 2 | Read current DC state | — |
| 3 | Draft UN/DI entries | — |
| 4 | Update DC-001–005 | — |
| 5 | Write verification tests | — |
| 6 | Implement code | — |
| 7 | Update CHANGELOG/VERSION/CLAUDE.md | — |
| 8 | Run dc_verify.py | Exit 0 required |
| 9 | Anti-drift checklist | All boxes |
| 10 | Branch, commit, PR, merge | dc_verify exit 0 |
