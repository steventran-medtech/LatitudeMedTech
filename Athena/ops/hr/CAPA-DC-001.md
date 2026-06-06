# CAPA-DC-001 — Unauthenticated Frontend API Fetch Calls

**Date opened:** 2026-06-06  
**Status:** OPEN — Preventive actions in progress  
**Type:** Preventive (systemic pattern; no client impact at Alpha)  
**Trigger:** dc_verify.py DI-020-B/C/E failed 3× during session — mandatory CAPA threshold  
**Raised by:** Athena / reviewed by Steven Tran  

---

## Problem Statement

During the Phase 2C review-queue fix session, `dc_verify.py` reported 3 failures
(DI-020-B, DI-020-C, DI-020-E) because GET fetch calls in `ReviewView.jsx` were
missing the `X-Athena-Key` authentication header. The server's `AuthMiddleware`
returned `{"error":"Unauthorized"}` on each call; the frontend's `.catch(() => {})`
silently swallowed the response; and the review queue and document viewer appeared
empty despite 42 items present in the database.

Post-fix audit identified the same naked-GET pattern across **8 additional frontend
source files**, indicating a systemic gap rather than an isolated incident.

---

## Scope

**Files with at least one unauthenticated GET fetch to a protected `/api/` endpoint
(as of 2026-06-06 audit):**

| File | Naked GET fetch count (approx.) |
|---|---|
| `App.jsx` | 10 |
| `ClientsView.jsx` | 3 |
| `DeckView.jsx` | 2 |
| `FileViewer.jsx` | 1 |
| `HRView.jsx` | 4 |
| `ISOView.jsx` | 2 |
| `MarketingView.jsx` | 3 |
| `SettingsView.jsx` | 1 |
| `useVoiceSession.js` | 2 |
| `ReviewView.jsx` | 0 (corrected in PR #70) |

**Legitimately exempt** (no auth required by `AuthMiddleware`):
- `GET /api/auth/token` — token issuance endpoint
- `GET /api/version` — health/version check

---

## Root Cause Analysis (5-Why)

| # | Why | Finding |
|---|---|---|
| 1 | Why did dc_verify fail 3×? | GET fetch calls in `ReviewView.jsx` were missing `authHdr()` |
| 2 | Why were they missing? | POST calls require `Content-Type` headers, making auth headers visible in the options object; GET calls have no such forcing function — they silently omit auth |
| 3 | Why does the linter not catch this? | No ESLint rule or project-level lint config enforces `authHdr()` on `/api/` fetch calls; the formatter treats `fetch(url)` and `fetch(url, { headers: authHdr() })` as stylistically equivalent |
| 4 | Why does dc_verify not catch it across all files? | DI-020-B/C/E check only `ReviewView.jsx`; no test scans the full frontend source tree for this pattern |
| 5 | Why was the code written this way originally? | The frontend auth standard was not documented as a formal design requirement until UN-020/DI-020 were created today; developers (and Claude) wrote GET calls by analogy with unprotected APIs |

**Primary root cause:** Missing design standard — no stated, enforced requirement that
*every* fetch call to `/api/` (except exempt endpoints) must carry `authHdr()`.
The CAPA trigger was a symptom; the disease is absent lint enforcement and absent
automated cross-file coverage in `dc_verify.py`.

**Contributing factors:**
- Silent failure: `.catch(() => {})` swallows 401s, making the defect invisible at runtime
- POST calls masked the gap: auth headers were consistently applied to mutating calls because they always needed `Content-Type`; GET calls were never scrutinized

---

## Corrective Actions (completed)

| ID | Action | File | PR | Status |
|---|---|---|---|---|
| CA-1 | Add `authHdr()` to `/api/review/pending` fetch in `load()` | `ReviewView.jsx` | #70 | ✓ Done |
| CA-2 | Add `authHdr()` to `/api/review/history` fetch in `loadHistory()` | `ReviewView.jsx` | #70 | ✓ Done |
| CA-3 | Add `authHdr()` to `/api/review/{id}/content` fetch in `loadContent()` | `ReviewView.jsx` | #70 | ✓ Done |
| CA-4 | Add `authHdr()` to `/api/review/{id}/google-view` fetch in `loadContent()` | `ReviewView.jsx` | #70 | ✓ Done |

---

## Preventive Actions

| ID | Action | Owner | Due | Status |
|---|---|---|---|---|
| PA-1 | Extend `dc_verify.py` with `test_DI_015_G` — scan all `.jsx`/`.js` files for naked `fetch(${API}/api/` calls lacking `authHdr()`, excluding exempt endpoints | Steven / Claude | Phase 2C close | OPEN |
| PA-2 | Fix all remaining naked GET fetches identified in the scope audit above (CA-1–4 covered `ReviewView.jsx`; 9 files remain) | Steven / Claude | Phase 2C close | OPEN |
| PA-3 | Add `DI-015-G` to DC-002 and RTM: *"All fetch calls to non-exempt `/api/` endpoints in the frontend shall include `authHdr()` in the request headers"* | Steven / Claude | Phase 2C close | OPEN |
| PA-4 | Add to `CLAUDE.md` §Frontend Standards: *"Every `fetch(\`${API}/api/...\`)` call must include `{ headers: authHdr() }` unless the endpoint is in the auth-exempt list (`/api/auth/token`, `/api/version`). No exceptions. GET calls are not exempt."* | Steven / Claude | Phase 2C close | OPEN |
| PA-5 | Audit `.catch(() => {})` usage across frontend — replace with error state that surfaces auth failures visibly rather than silently emptying the UI | Steven / Claude | Phase 2D | OPEN |

---

## Verification Criteria

This CAPA is **CLOSED** when:

1. `test_DI_015_G` passes in `dc_verify.py` with zero naked-fetch violations across the full frontend source tree
2. PA-2 PR is merged and `dc_verify.py` full suite exits 0
3. `DI-015-G` status is VERIFIED in DC-002 and DC-004
4. `CLAUDE.md` frontend standard added and reviewed by Steven

---

## Expected Outcome

No future session introduces or re-introduces a naked `/api/` fetch call.
Any such call is caught immediately by `dc_verify.py` before merge, not
discovered through a silent runtime failure.

---

*Alpha — Steve Review Required*
