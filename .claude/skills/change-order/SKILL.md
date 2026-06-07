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

### T-A2: In-flight CO overlap check

Run immediately after mapping files. This surfaces collision risk before any work begins.

**Step 1 — Find in-flight CO branches:**
```powershell
git fetch origin
git branch -r | Select-String "^  origin/(feat|fix|chore)/"
```

**Step 2 — For each in-flight branch, get its changed files:**
```powershell
git diff --name-only origin/main...origin/<branch-name>
```

**Step 3 — Compare against the files listed in T-A:**

| Situation | Action |
|---|---|
| No overlap | Proceed — note the in-flight branches in the PR description |
| Overlap on a non-protected path | Warn: "CO `<branch>` also touches `<file>`. Merging both will require a rebase. Acknowledge before I continue." STOP until acknowledged. |
| Overlap on any protected path | HARD BLOCK — state: "CO `<branch>` is in-flight and already touches protected path `<file>`. This CO cannot proceed until that one lands on main." Do not continue under any circumstances. |

If no in-flight branches exist, state "No in-flight COs detected" and proceed.

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

| Tier | Definition | Model | Examples |
|---|---|---|---|
| **Tier 1 — Cosmetic** | No logic, no branching, no data path | Haiku | CSS value, label text, comment, icon, version string |
| **Tier 2 — Localized Functional** | Affects one module; no shared contracts changed | Sonnet | Single-agent prompt, new isolated API route, self-contained UI component |
| **Tier 3 — Core / Shared / Critical** | Touches shared utilities, cross-module behavior, or any VERIFIED DI | Sonnet (high) or Opus | Shared helper, cross-agent behavior, DC-002 DI change, any file with an existing `test_DI_*` |

When uncertain between two tiers, assign the higher one.

### T-D: State and wait

State the tier, the assigned model, and your reasoning. **STOP — do not proceed until Steven confirms.**

Example: "This is **Tier 2 — Localized Functional** (model: Sonnet). Reason: touches only the coaching-agent prompt, no shared contracts. Confirm to proceed."

### T-E: Execute only the tier's steps

**Tier 1 — Cosmetic** *(Haiku · low effort · lint-and-commit · push direct, no PR)*
1. Implement with Haiku — keep the change minimal and literal
2. Run `git diff --check` to catch whitespace/lint issues
3. If the changed file is referenced by any `test_DI_*`, run `python design_control\dc_verify.py --di <that-prefix>`; otherwise skip
4. Commit to the current branch
5. Push directly to main (no PR, no review gate — cosmetic changes carry no functional risk):
   ```powershell
   git push origin main
   ```
6. Report the pushed commit SHA. Done.

**Tier 2 — Localized Functional** *(Sonnet · medium effort · test-affected-area · push only on confirm)*
1. Implement with Sonnet
2. `python design_control\dc_verify.py --di <affected-DI-prefix>`
3. Run all DIs under the same UN: `python design_control\dc_verify.py --di <UN-prefix>`
4. Fix any failures
5. Commit to current branch
6. **STOP — show Steven the diff and the verify output. Wait for explicit "push" instruction before pushing.**
7. On confirm: push and open a PR per Step 11C. Merge only after Steven approves.

**Tier 3 — Core / Shared / Critical** *(Sonnet high or Opus · full V&V · PR required · never auto-merges)*
- Use Sonnet with extended thinking, or switch to Opus if the change spans more than three files or modifies a protected path.
- Continue through Steps 0–11 below in full.
- Tests must be written **before** the implementation (failing-test-first): write `test_DI_NNN_X`, confirm it fails, then implement until it passes.
- A PR is always required — no direct commits to main.
- **Never merge to main without Steven's explicit written approval in the PR conversation.** Even if all checks pass, stop at Step 11D and wait.

---

## Step 0 — Assign CO ID, Parse, and Clarify

### 0A — Assign CO ID

Read `design_control/DC-006_change_control.md` → Change Order Register. Take the **Next available ID**, add a new row to the register with today's date and status OPEN, and update the "Next available ID" line.

State the assigned ID immediately: "Opening **CO-NNN**."

This ID is used in branch names, commit messages, and the PR title throughout the rest of this CO.

### 0B — Parse and clarify

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

Branch naming includes the CO ID so every branch is traceable back to the register:

```powershell
# C2 — Additive:   feat/co-NNN-un-NNN-<kebab-description>
# C1 — Corrective: fix/co-NNN-di-NNN-<kebab-description>
# C3 — Modifying:  chore/co-NNN-un-NNN-<kebab-description>
git checkout -b feat/co-NNN-un-NNN-<short-description>
```

Update the CO register row in DC-006 with the branch name.

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
feat(co-NNN/un-NNN): <short description of the user need>

CO: CO-NNN
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

**One CO lands at a time. Follow every sub-step in order.**

**Step 1 — Check for concurrent merge activity:**
```powershell
gh pr list --state open --json number,title,headRefName,createdAt
```

If any other open CO is lower-risk (lower tier) or was opened earlier at the same tier, STOP:
> "PR #NNN (`<title>`) should land first — it is lower-risk or opened earlier. Merge that one before this CO."

Merge order within the queue: Tier 1 before Tier 2 before Tier 3; ties broken by earliest-opened.

**Step 2 — Rebase onto current main:**
```powershell
git fetch origin
git rebase origin/main
```

If the rebase exits cleanly, proceed to Step 3.

If there are conflicts, **DO NOT auto-resolve**. Stop and report each conflict in plain language:

> "Conflict in `<filename>` near line NNN: this CO changes `<description of this CO's change>`, but main now has `<description of what main changed>`. Choose: (A) keep this CO's version, (B) keep main's version, (C) write a merged version — tell me which."

Wait for explicit instruction on every conflicting file before resolving. After resolving all conflicts:
```powershell
git rebase --continue
```

**Step 3 — Run tier-appropriate post-rebase verification:**

| Tier | Command | Required result |
|---|---|---|
| Tier 1 | Skip (unless T-E requires it) | — |
| Tier 2 | `python design_control\dc_verify.py --di <affected-DI-prefix>` | Exit 0 |
| Tier 3 | `python design_control\dc_verify.py` | Exit 0, 0 FAILURES |

Do not proceed to Step 4 if verification fails.

**Step 4 — Force-push the rebased branch:**
```powershell
git push --force-with-lease origin <branch-name>
```

**Step 5 — Squash-merge and delete branch:**
```powershell
gh pr merge --squash --delete-branch
```

Report the merge commit SHA and confirm the branch is deleted.

**Step 6 — Close the CO in the register:**

Update the CO-NNN row in `design_control/DC-006_change_control.md` → Change Order Register: set Status to **MERGED**. Commit the register update directly to main:
```powershell
git add design_control/DC-006_change_control.md
git commit -m "chore(co-NNN): close CO-NNN — merged"
git push origin main
```

---

## Failed Tests Outside an Open CO

If `dc_verify.py` exits non-zero and **no open CO already covers the failing DI**, treat the failure as a defect report and open a remediation CO immediately:

1. **Stop all other work.** Do not commit, push, or continue an unrelated CO until the broken DI is addressed.
2. **Open a C1 Corrective CO** by invoking `/change-order` with the description:
   > "C1 remediation: DI-NNN-X failing — `<verbatim failure message from dc_verify.py>`"
3. The C1 CO gets its own **CO-NNN ID** from the register. Branch: `fix/co-NNN-di-NNN-<short-description>`.
4. The C1 process is lightweight (Steps 1, 2 read-only, Steps 6 → 8 → 11 only — no new UN, no DC-001/DC-005 edits unless the test itself was wrong).
5. Once CO-NNN merges and `dc_verify.py` is green, resume the work that was interrupted.

**If the failure was caused by the current CO's rebase** (post-rebase verify in Step 11D fails): do not open a new CO — fix it in the current branch before merging.

---

## Quick Reference

| Step | Action | Model | Gate |
|---|---|---|---|
| T-A | Map touched files | — | — |
| T-A2 | In-flight CO overlap check | — | Block on protected-path overlap |
| T-B/C/D | Risk tier classification | — | Steven confirms tier + model |
| T-E (Tier 1) | Implement → lint → commit → push direct | **Haiku** | No PR required |
| T-E (Tier 2) | Implement → test-affected → commit | **Sonnet** | Steven confirms push |
| T-E (Tier 3) | Failing-test-first → full V&V → PR | **Sonnet high / Opus** | Steven approves merge |
| 0–9 | Full DC process (Tier 3 only) | Sonnet high / Opus | dc_verify exit 0; all boxes |
| 11D | Rebase → verify → merge (one-at-a-time, lowest-risk first) | — | No conflicts unresolved; post-rebase verify passes; Steven's say-so for Tier 3 |
