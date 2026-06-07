# DC-005 — Verification Protocol
**Document:** DC-005 · Version 1.6 · 2026-06-07  
**Approved by:** Steven Tran

---

## Purpose

This document defines the procedures for executing and interpreting all
design input verification tests. Tests are implemented in `dc_verify.py`
(same directory). This document explains *why* each test exists, *what* it
checks, and *what to do* when it fails.

---

## Test Execution Modes

| Mode | Command | Scope | When to Run |
|---|---|---|---|
| Static | `python design_control\dc_verify.py` | No server required | Before every commit |
| Live | `python design_control\dc_verify.py --live` | Requires server on :8000 | Before every PR merge |
| Full | `python design_control\dc_verify.py --full` | Live + agent dry-run | Before any Alpha release |
| Targeted | `python design_control\dc_verify.py --di DI-015` | Single DI prefix | After targeted change |

Exit code: `0` = all active tests pass. `1` = one or more FAIL. `2` = configuration error.

---

## Pre-Commit Gate (Mandatory)

The following static tests must pass before `git commit` on any code change:

```
DI-001-C  Disclaimer constant present in orchestrator.py
DI-001-D  Label constant present in orchestrator.py
DI-015-A  No secrets in source tree
DI-015-B  No shell=True in subprocess calls
DI-015-D  Security headers present in server.py
DI-016-A  DISCLAIMER string in orchestrator.py
DI-016-B  LABEL string in orchestrator.py
DI-016-C  Label value is a permitted readiness label
```

If any of these fail, the commit must be blocked until fixed.

---

## Test Descriptions and Failure Guidance

### DI-001 — Coaching Brief

**test_DI_001_C** — Readiness label in orchestrator  
Check: `LABEL` constant in `orchestrator.py` is non-empty.  
Fail action: Add `LABEL = "Alpha — Steve Review Required"` to orchestrator.py.

**test_DI_001_D** — Disclaimer in orchestrator  
Check: `DISCLAIMER` constant in `orchestrator.py` contains the canonical text.  
Fail action: Restore the canonical disclaimer from `compliance.md`.

---

### DI-002 — Human Review Gate

**test_DI_002_A** — Review queue route exists  
Check: `POST /api/review` or equivalent pending-list route in `server.py`.  
Fail action: Review was removed or renamed — restore or update route.

**test_DI_002_B** — Approve route  
Check: `POST /api/review/{item_id}/approve` or `{id}/approve` in `server.py`.  
Fail action: Approve endpoint missing; gate is broken — restore immediately (P0).

**test_DI_002_C** — Reject route  
Check: `POST /api/review/{item_id}/reject` in `server.py`.  
Fail action: Same as approve — restore immediately (P0).

**test_DI_002_D** — Edit route  
Check: `POST /api/review/{item_id}/edit` in `server.py`.  
Fail action: Edit feature removed; P1 — restore in current sprint.

**test_DI_002_E** — Approved filter uses `/api/documents`  
Check: `ReviewView.jsx` contains a `fetch` to `/api/documents` for the Approved tab.  
Fail action: Add `loadApproved()` fetching `GET /api/documents` and call it when `tab === "approved"` in ReviewView.jsx.

**test_DI_002_F** — Document Queue three-state filter  
Check: `ReviewView.jsx` uses `useState("pending")` as initial tab state; `"approved"` and `"rejected"` appear as tab keys; legacy `useState("queue")` is absent.  
Fail action: Change `useState("queue")` → `useState("pending")`; replace tab array `["queue","Pending"],["history","History"]` with `["pending","Pending"],["approved","Approved"],["rejected","Rejected"]`.

**test_DI_002_G** — Navigation MAP consolidation  
Check: `App.jsx` `NAV_ITEMS` contains `id:"queue"` and does NOT contain `id:"documents"` or `id:"review"`.  
Fail action: Remove the `documents` and `review` entries from `NAV_ITEMS`; add a single `{id:"queue", label:"Document Queue"}` entry.

---

### DI-003 — Knowledge Base

**test_DI_003_A** — KBQuery importable  
Check: `kb_query.py` exists and `KBQuery` class is defined.  
Fail action: File missing or class removed — check git history for last good state.

**test_DI_003_B** — KB subdirectories exist  
Check: `knowledge_base/FDA`, `knowledge_base/EU_MDR`, `knowledge_base/IMDRF` exist.  
Fail action: Directory missing — create it and run `run_rag.bat` to populate.

---

### DI-004 — Voice Interface

**test_DI_004_A** — Wake threshold ≤ 0.35  
Check: `WAKE_THRESHOLD` or equivalent constant in `voice_bridge.py` ≤ 0.35.  
Fail action: Value was increased — revert to ≤ 0.35 per CAPA-Voice-001 resolution.

**test_DI_004_B** — Whisper load present  
Check: `whisper.load_model` or `whisper_model` initialisation in `voice_bridge.py`.  
Fail action: Whisper removed; voice cannot transcribe — restore.

**test_DI_004_D** — Intent dispatch present  
Check: `tool_use` or `tools=` in voice_bridge.py dispatch logic.  
Fail action: Routing logic removed; all voice queries go to default — restore.

**test_DI_004_E** — SILENCE_DURATION = 1.5  
Check: `SILENCE_DURATION` constant equals 1.5 (float or int).  
Fail action: Value changed outside approved range. Values < 0.8 cause cut-off;
values > 2.0 cause unacceptable latency. Restore to 1.5 unless CAPA-approved.

---

### DI-005 — Task Notifications

**test_DI_005_A** — Notify endpoint  
Check: `POST /api/voice/notify` in `server.py`.  
Fail action: Endpoint removed — spoken task completions will stop working.

**test_DI_005_B** — Notification queue guarded  
Check: `_notification_queue` in `voice_bridge.py`.  
Fail action: Queue removed — notifications may fire when voice is not active.

---

### DI-006 — Persistent Voice Session

**test_DI_006_A** — useVoiceSession is app-level  
Check: `useVoiceSession` imported in `App.jsx`, NOT in any individual view file.  
Fail action: Hook was moved to a tab view — session will reset on navigation.

**test_DI_006_B** — VoiceStatusBadge in App.jsx header  
Check: `VoiceStatusBadge` present in `App.jsx`.  
Fail action: Badge removed from header — users lose live voice state visibility.

---

### DI-007 — Content Generation

**test_DI_007_B** — title_from_body exists  
Check: `title_from_body` function defined in `content_agent.py`.  
Fail action: Function removed — titles will be raw model output (may contain non-Latin).

**test_DI_007_C** — Banned phrases in system prompt  
Check: At least one banned phrase (e.g., "leverage", "robust", "synergy") appears
in the system prompt string in `content_agent.py`.  
Fail action: System prompt replaced or truncated — content quality controls removed.

**test_DI_007_D** — clean_title exists  
Check: `clean_title` function defined in `content_agent.py`.  
Fail action: Function removed — non-Latin characters will appear in filenames and slugs.

---

### DI-009 — Slide Decks

**test_DI_009_B** — Brand palette constants  
Check: `LM_BLACK`, `LM_SLATE`, `LM_BLUE` constants in `deck_agent.py` with correct hex values.  
Fail action: Constants renamed or removed — decks will not render Latitude branding.

**test_DI_009_C** — Deck routes  
Check: `/api/documents/decks` in `server.py`.  
Fail action: Deck gallery will be empty; download broken.

---

### DI-010 — ISO Coach

**test_DI_010_A** — ISO coach agent exists  
Check: `iso_coach_agent.py` exists and is importable.  
Fail action: File removed — ISO coaching feature down.

**test_DI_010_B** — No --all from UI  
Check: The `--all` flag handling code is absent from the ISO coach's API route
handler (i.e., `--all` is only accessible via CLI, not via the API endpoint).  
Fail action: Flag exposed in API — UI could generate all clauses at once.

---

### DI-011 — M&A Intelligence

**test_DI_011_A** — QARA in M&A agent  
Check: "QARA" appears in `ma_intelligence_agent.py` or `.claude/agents/ma-intelligence-agent.md`.  
Fail action: QARA framework removed — deal analysis will miss integration risk dimension.

---

### DI-012 — Regulatory Briefings

**test_DI_012_B** — submit_for_review in briefing_agent  
Check: `submit_for_review` called in `briefing_agent.py`.  
Fail action: Briefings bypass review queue — human gate broken for briefings.

---

### DI-013 — Dashboard

**test_DI_013_A** — Dashboard route  
Check: `/api/dashboard` in `server.py`.  
Fail action: Dashboard will not load.

**test_DI_013_B** — Timeseries route  
Check: `/api/dashboard/timeseries` in `server.py`.

**test_DI_013_C** — Knowledge growth route  
Check: `/api/dashboard/knowledge-growth` in `server.py`.

---

### DI-014 — Learning & Skills

**test_DI_014_A** — last_learning stamp  
Check: `last_learning` string appears in `agent_learning.py` logic (not just comments).  
Fail action: Stamp removed — agent health indicators will stay stuck red/yellow.

**test_DI_014_B** — skills_profile.py exists  
Check: `skills_profile.py` exists and `SKILLS.md` route in `server.py`.

---

### DI-015 — Security

**test_DI_015_A** — No secrets in source  
Check: Grep all `.py`, `.js`, `.jsx`, `.json`, `.md` files (excluding `venv/`,
`node_modules/`, `.gitignore`-excluded paths) for patterns:
`ANTHROPIC_API_KEY=sk-`, `TAVILY_API_KEY=tvly-`, `BRAVE_API_KEY=BSA`, `HF_TOKEN=hf_`.  
Fail action: **STOP ALL WORK.** Remove the secret immediately, rotate the key, and
force-push with git history rewrite if already committed.

**test_DI_015_B** — No shell=True  
Check: Grep all `.py` files for `shell=True` or `shell = True`.  
Fail action: **P0 security fix required.** Every subprocess call must use `shell=False`.

**test_DI_015_C** — Rate limiting in server.py  
Check: `SlowAPI` import or `rate_limit` or `RateLimiter` in `server.py`.  
Fail action: Rate limiter removed — API is open to abuse. Restore before next deploy.

**test_DI_015_D** — Security headers  
Check: `X-Frame-Options` and `X-Content-Type-Options` and `Content-Security-Policy`
referenced in `server.py` middleware.  
Fail action: Security headers removed — browser XSS/clickjacking protections degraded.

**test_DI_015_E** — Path traversal protection  
Check: `..` or `path_traversal` or `resolve()` check present in file-serving routes.  
Fail action: File endpoints vulnerable to directory traversal.

---

### DI-016 — Output Labeling

**test_DI_016_A** — DISCLAIMER constant  
Check: `DISCLAIMER = ` present in `orchestrator.py` and contains "AI assistant" and "internal review".

**test_DI_016_B** — LABEL constant  
Check: `LABEL = ` present in `orchestrator.py` and is non-empty string.

**test_DI_016_C** — Label is a permitted value  
Check: The value of LABEL is one of: `Demo`, `Alpha`, `Beta`, `Production` (substring match).

---

### DI-017 — Audit Logs

**test_DI_017_A** — Voice sessions log path referenced  
Check: `sessions.jsonl` appears in `voice_bridge.py` (the log write call).

**test_DI_017_B** — Athena sessions log path referenced  
Check: `athena_sessions.jsonl` appears in `stop_athena.ps1`.

---

### DI-019 — Startup Splash Screen

**test_DI_019_A** — Bar positioned at bottom edge  
Check: `.bar-wrap` in `start_splash.hta` has `position:absolute`, `bottom`, and `left`/`right` spanning full width.  
Fail action: Restore absolute positioning on `.bar-wrap` in `start_splash.hta`.

**test_DI_019_B** — Spectrum percentage label  
Check: `start_splash.hta` contains an element with `id="pct"`, a `pctEl.innerText` assignment in VBScript, and `float:right` in `.pct-text` CSS.  
Fail action: Add the `#pct` element, Tick VBScript assignment, and `float:right` CSS per Adobe Spectrum progress bar guidelines.

**test_DI_019_C** — Milestone-gated close  
Check: `start_splash.hta` has a `PollChromeReady` routine that sets `targetVal = 100` on `.athena_ready`; `readyToClose` flag gates `window.close()` until `stepVal >= 99.5`.  
Fail action: Restore `PollChromeReady`, `readyToClose = True`, and the `stepVal >= 99.5` close-gate in `start_splash.hta`.

**test_DI_019_F** — Smooth asymptotic easing  
Check: `start_splash.hta` Tick sub contains an asymptotic easing expression `(targetVal - stepVal) * 0.N` and a minimum floor `If inc < N Then inc = N`.  
Fail action: Restore the asymptotic factor and minimum floor in the Tick Sub so the bar always advances visibly. Removing either causes the bar to stall or jump.

**test_DI_019_G** — Splash-to-Chrome gap < 3 s  
Check: `start_athena.ps1` `Start-Sleep -Milliseconds` value is ≤ 2500.  
Fail action: Reduce `Start-Sleep -Milliseconds` in `start_athena.ps1` to ≤ 2500. Values > 2500 produce a blank-screen gap exceeding the 3-second product requirement (accounting for ~500 ms of splash close animation).

**test_DI_019_H** — No stall > 1 s; mathematical bound + premature 100% prevention  
Check five conditions in `start_splash.hta`:  
1. Tick sub has `If inc < N Then inc = N` floor — parse `min_floor` value.  
2. PollChromeReady has `If adv < N Then adv = N` floor.  
3. PollChromeReady cap `If targetVal > CAP` where CAP ≤ 98.  
4. Tick display uses `Int(stepVal)` not `CInt(stepVal)`.  
5. Mathematical bound: `(99.5 − cap) / min_floor × 16 ms < 1000 ms` — proves Tick can traverse from the cap to the 99.5 close-trigger in under 1 second at worst-case minimum frame rate.  
Fail action: Missing floors → stalling. Cap > 98 → premature "100%" for minutes during model loading. Mathematical bound failure → bar provably cannot close within 1 s even with correct guards. Restore all five conditions in `start_splash.hta`.

**test_DI_019_I** — Athena title font-size is 101px in both splash implementations  
Check: (1) `start_splash.hta` `.name` CSS contains `font-size:101px`. (2) `electron/main.js` `.name` CSS contains `font-size:clamp(61px,7vw,101px)`.  
Fail action: Set `font-size:101px` on `.name` in `Athena/ui/start_splash.hta`. Set `font-size:clamp(61px,7vw,101px)` on `.name` in `Athena/electron/main.js`.

**test_DI_019_J** — `#dots` element cycles via VBScript `TickDots` at ≤ 500 ms/state; hidden on completion  
Preconditions: `start_splash.hta` on disk.  
Check: (1) File contains a `TickDots` sub (or equivalent cycling sub) that assigns to `dotsEl.innerText`. (2) File contains `setInterval("TickDots", N)` where N ≤ 500. (3) File contains `dotsEl.style.display = "none"` on loading completion. (4) The `#dots` HTML element uses a single span (not three individual `.dot` sub-spans).  
Fail action: Replace 3-span CSS-animated dots in `start_splash.hta` with a single `<span id="dots">.</span>` and add the `TickDots` VBScript cycling sub with a `setInterval` ≤ 500 ms.

---

### DI-023 — Historical Data Depth

**test_DI_023_A** — RAG pipeline has no hard date cutoff that blocks sources older than 50 years  
Check: (1) `rag_agent.py` contains no `cutoff_year`, `min_year`, `year >=`, or equivalent expression that would exclude documents older than 50 years. (2) The KB seed query list includes at least one term not anchored to a specific recent year.  
Live verification: Manual audit — confirm that the ingestion pipeline can accept a pre-1990 document without rejection, or that at least one historical source is present in the KB after a full RAG run.  
Fail action: Remove any hard year filter from `rag_agent.py`. Add at least one historically-scoped query (e.g., "FDA medical device regulatory history", "ISO 9001 origins quality management") to the seed query list.

---

## Interpreting Results

| Test Result | Action |
|---|---|
| PASS | No action required. |
| FAIL (P0) | Block commit/PR. Fix immediately before any other work. |
| FAIL (P1) | Fix within current sprint. Document in CAPA if 3+ P1 failures. |
| WARN | Investigate; resolve within one sprint or document as accepted risk. |
| SKIP | Test was skipped due to missing dependency. Investigate and re-enable. |

### DI-030 — McKinsey/Latitude Brand Formatting Standard

**test_DI_030_A** — All deck types include exec_summary  
Check: All 6 `_DECK_GUIDES` entries in `deck_agent.py` ("strategy", "pitch", "regulatory", "coaching", "ma", "briefing") contain "exec_summary" in their slide-sequence string.  
Fail action: Add `exec_summary` after `cover` in the missing `_DECK_GUIDES` entry. The pitch deck was originally missing this slide; add it as the second slide after cover.

**test_DI_030_B** — McKinsey quality directive in all deliverable agents  
Check: Each of `content_agent.py`, `briefing_agent.py`, `ma_intelligence_agent.py`, `regulatory_strategy_agent.py`, `sow_agent.py`, `deck_agent.py` contains at least one of "McKinsey", "Big 4", "pyramid", "SCQA" in its source text.  
Fail action: Add a quality directive to the missing agent's system prompt constant: e.g., `"Quality standard: McKinsey/Big 4 management consulting register."`.

**test_DI_030_C** — Latitude MedTech LLC brand identity in agent_base.py  
Check: `agent_base.py` contains "Latitude MedTech LLC" and a system prompt construction pattern (a `parts` list, `build_system_prompt`, or equivalent function).  
Fail action: Ensure `agent_base.py` injects "Latitude MedTech LLC" into the shared system prompt prefix so all agents carry the brand identity.

---

## CAPA Trigger

If `dc_verify.py` produces 3 or more FAIL results in a single run, open a CAPA:
```
Athena/ops/hr/CAPA-DC-NNN.md
```
Use the CAPA template in `ops/hr/`. Steven must approve before work resumes on
the failing area. Reference this document as the governing requirement source.
