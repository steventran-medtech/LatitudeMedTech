## Summary
<!-- 1–3 bullets describing what this PR does and why -->
-

## Change Classification (DC-006)
<!-- Mark one -->
- [ ] C1 — Corrective (bug fix restoring a VERIFIED DI)
- [ ] C2 — Additive (new feature traced to a new/existing UN)
- [ ] C3 — Modifying (changes existing VERIFIED behavior)
- [ ] C4 — Removing (feature removal — written waiver required)
- [ ] C5 — Emergency (P0 security; verbal OK from Steven; full docs within 24 h)

## Traceability
<!-- List every UN and DI this PR touches. If none, explain why. -->
| User Need | Design Input(s) | Status |
|-----------|-----------------|--------|
| UN-XXX    | DI-XXX-X        | OPEN → VERIFIED |

## Authentication Header Checklist
<!-- Every new or modified fetch() call must be checked. -->
> **Root cause of DI-013-D/E/F (2026-06-05):** `loadData()` sent the
> `/api/dashboard` request without `authHdr()`, returning 401 on every load.
> A parallel `useEffect` also caused a startup race before the session token
> was available. This checklist prevents recurrence.

- [ ] Every **new** `fetch()` call to a protected API endpoint includes `{ headers: authHdr() }`
- [ ] Every **modified** `fetch()` call still includes `{ headers: authHdr() }`
- [ ] No new `useEffect` calls `loadData()` or any other data-fetch function _before_ the auth token is set
- [ ] If a new function fetches data on mount, it is called _inside_ the auth-token `useEffect` (after `setToken()`), not in a parallel effect
- [ ] `GET`-only fetches that do **not** require auth (e.g. `/api/auth/token`, `/api/version`) are explicitly excluded from the above

## Verification
```powershell
python design_control\dc_verify.py
```
- [ ] `dc_verify.py` exits 0 (all tests PASS)
- [ ] DI-013-D, DI-013-E, DI-013-F all show `OK` in the output

## Design Control Documents Updated
- [ ] DC-002 — Design Inputs: new/modified DIs added or status updated
- [ ] DC-003 — Design Outputs: affected file/symbol rows updated
- [ ] DC-004 — Traceability Matrix: new DI rows added; coverage summary updated
- [ ] `dc_verify.py` — new `test_DI_NNN_X()` function(s) added for every new DI
- [ ] `CHANGELOG.md` — entry added under `[Unreleased]`
- [ ] `VERSION.json` — bumped per semver rules in CLAUDE.md
- [ ] `CLAUDE.md` — `## Recent Changes` section updated

## Test Plan
<!-- Bullets of what to verify manually after merge -->
-

## Steven's Approval
- [ ] Steven has reviewed and approved this PR
