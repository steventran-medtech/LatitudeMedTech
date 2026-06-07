# DC-002 — Design Inputs
**Document:** DC-002 · Version 1.8 · 2026-06-06  
**Approved by:** Steven Tran

Design inputs are specific, verifiable requirements derived from the user
needs in DC-001. Each input is stated so that it can be objectively tested
as pass or fail. Every design input must be linked to at least one user need
and at least one verification test in DC-005.

---

## Format

Each entry:  
**DI-NNN-X** | Source UN | Statement | Verification Method | Priority | Status

---

## Coaching Business Line

### UN-001 — Client Briefing Generation

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-001-A | UN-001 | System shall generate a coaching brief when given only a client name | `POST /api/agents/briefing` returns a non-empty brief body | P0 | VERIFIED |
| DI-001-B | UN-001 | Generated brief shall be queued in the review system with a unique review ID and status "pending" | Review DB entry created with `status = pending` | P0 | VERIFIED |
| DI-001-C | UN-001 | Brief shall include a readiness label ("Alpha — Steve Review Required") in the output | Label string present in generated brief text | P0 | VERIFIED |
| DI-001-D | UN-001 | Brief shall include the regulatory disclaimer text | Disclaimer string present in generated output | P0 | VERIFIED |

### UN-002 — Human Review Gate

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-002-A | UN-002 | All agent-generated outputs shall enter a review queue before finalization or delivery | Review queue endpoint `GET /api/review` returns pending items after any agent run | P0 | VERIFIED |
| DI-002-B | UN-002 | Review queue shall support approve action that marks item final | `POST /api/review/{id}/approve` sets status to "approved" | P0 | VERIFIED |
| DI-002-C | UN-002 | Review queue shall support reject action that halts delivery | `POST /api/review/{id}/reject` sets status to "rejected" | P0 | VERIFIED |
| DI-002-D | UN-002 | Review queue shall support edit-and-rewrite via natural language instruction | `POST /api/review/{id}/edit` rewrites content at consulting quality | P1 | VERIFIED |
| DI-002-E | UN-002 | Only approved items shall appear in the Documents hub — items with any other review status (pending, rejected, or not yet submitted) shall be excluded | `GET /api/documents` cross-references `review_queue` approved set via `get_approved_reviews()` | P0 | VERIFIED |

### UN-003 — Knowledge Base

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-003-A | UN-003 | Knowledge base shall be searchable by all agents via `KBQuery.search()` | `kb_query.py` imports cleanly and `KBQuery()` instantiates | P1 | VERIFIED |
| DI-003-B | UN-003 | RAG ingestion agent shall index documents from FDA, EU MDR, and IMDRF sources | KB directory contains ≥1 JSON file per knowledge subdomain | P1 | VERIFIED |

---

## Voice Interface

### UN-004 — Wake Word and Voice Interaction

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-004-A | UN-004 | System shall detect the active wake word with threshold ≤ 0.35 | `WAKE_THRESHOLD` in `voice_bridge.py` is ≤ 0.35 | P0 | VERIFIED |
| DI-004-B | UN-004 | System shall transcribe voice queries via Whisper and log confidence score | Whisper model loads at startup; `[low conf]` tag written to log on low-confidence result | P0 | VERIFIED |
| DI-004-C | UN-004 | First TTS audio byte shall be produced within 2 seconds of query completion | Streaming sentence-split pipeline; first sentence dispatched to Kokoro before full response | P0 | PARTIAL |
| DI-004-D | UN-004 | Voice bridge shall classify query intent and route to the correct agent via `tool_use` | `voice_bridge.py` contains tool-use dispatch logic | P0 | VERIFIED |
| DI-004-E | UN-004 | SILENCE_DURATION shall be 0.65 s (BUG-2 latency fix 2026-06-06 — reduced from 0.8 s; 0.65 s is the minimum that avoids mid-sentence cutoff on the RTX 4070 + Whisper base.en stack) | `SILENCE_DURATION` default in `voice_bridge.py` equals 0.65 | P0 | VERIFIED |

### UN-005 — Task Completion Notifications

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-005-A | UN-005 | System shall queue a spoken notification when any long-running agent completes | `POST /api/voice/notify` endpoint exists in server.py | P1 | VERIFIED |
| DI-005-B | UN-005 | Notification shall only be spoken if a voice session is currently active | `_notification_queue` drained only when voice listening loop is active | P1 | VERIFIED |

### UN-006 — Persistent Voice Session

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-006-A | UN-006 | Voice session WebSocket shall persist when the user navigates between tabs | `useVoiceSession.js` is app-level (not tab-level); session state stored in App.jsx | P1 | VERIFIED |
| DI-006-B | UN-006 | `VoiceStatusBadge` shall appear in the header on all tabs showing live voice state | Header component contains VoiceStatusBadge with live state prop | P1 | VERIFIED |

### UN-022 — Voice Conversation Quality

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-022-A | UN-022 | Latency between completion of user's voice input and commencement of audible agent response shall be ≤ 2 seconds (see also DI-004-C for TTS pipeline timing) | Live timing measurement with voice stack running; static: `voice_bridge.py` contains `_ask_claude_streaming` using a streaming LLM call, `_split_sentences` / `_SENTENCE_END` for sentence-boundary detection, and `_speak_sentence` called inside the token-stream loop — not after full response is buffered | P0 | PARTIAL |

---

## Content & Marketing

### UN-007 — MedTech Meridian Content

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-007-A | UN-007 | Content agent shall generate articles of 900–1,200 words | `max_tokens = 4000` in content agent; word-count check in post-processing | P0 | PARTIAL |
| DI-007-B | UN-007 | Article title shall be derived from the body H1 via `title_from_body()` and cleaned via `clean_title()` | Both functions exist in `content_agent.py` | P0 | VERIFIED |
| DI-007-C | UN-007 | Banned phrases shall be enforced at prompt level | Banned phrase list present in content agent system prompt | P0 | VERIFIED |
| DI-007-D | UN-007 | Non-Latin characters shall be removed from titles before storage | `clean_title()` strips non-ASCII characters | P0 | VERIFIED |
| DI-007-E | UN-007 | YAML frontmatter shall be stripped before content is rendered in the UI | `renderInline` / MarkdownView strips YAML frontmatter | P0 | VERIFIED |

### UN-008 — Marketing Pipeline

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-008-A | UN-008 | Marketing agent shall maintain a pipeline DB with ≥ 20 targets | `ops/marketing/pipeline.db` created on first run with ≥ 20 seed targets | P1 | PARTIAL |
| DI-008-B | UN-008 | All outreach channels shall be zero-cash-budget (no paid media at Alpha) | No paid channel types in pipeline seed data | P1 | PARTIAL |

### UN-009 — Slide Deck Generation

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-009-A | UN-009 | Deck agent shall generate a PPTX file with cover, exec summary, narrative, charts, and recommendations | `deck_agent.py` constructs slides in that sequence | P1 | PARTIAL |
| DI-009-B | UN-009 | Decks shall use Latitude brand palette (LM_BLACK 1A1A1A, LM_SLATE 2C3E50, LM_BLUE 5B7FA6) | Brand colour constants present in deck generation code | P1 | VERIFIED |
| DI-009-C | UN-009 | Generated decks shall be listed in the DeckView gallery and downloadable | `GET /api/documents/decks` returns deck list; download route exists | P1 | VERIFIED |

---

## Regulatory Intelligence

### UN-010 — ISO 13485 Coach

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-010-A | UN-010 | ISO coach shall generate clause content for any valid ISO 13485 clause reference | Clause lookup present in `iso_coach_agent.py`; responds to any clause number | P0 | VERIFIED |
| DI-010-B | UN-010 | ISO coach shall generate one clause at a time (blank input = next ungenerated clause) | Sequential generation logic present; `--all` flag unavailable from UI | P0 | VERIFIED |
| DI-010-C | UN-010 | No verbatim ISO standard text shall appear in the RAG knowledge base | KB ingestion pipeline excludes ISO standard files | P0 | PARTIAL |

### UN-011 — M&A Intelligence

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-011-A | UN-011 | M&A agent shall include QARA integration frameworks in deal analysis | QARA framework text present in `ma_intelligence_agent.py` or its agent MD | P1 | VERIFIED |
| DI-011-B | UN-011 | M&A outputs shall cite named sources with dates | Citation requirement present in M&A agent system prompt | P1 | VERIFIED |

### UN-012 — Regulatory Briefings

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-012-A | UN-012 | Briefing agent shall produce structured briefs covering FDA, EU MDR, and IMDRF | Briefing agent sources include all three frameworks | P1 | VERIFIED |
| DI-012-B | UN-012 | Briefing outputs shall enter the review queue via `submit_for_review()` | `submit_for_review()` called in `briefing_agent.py` | P1 | VERIFIED |

### UN-023 — Historical Data Depth

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-023-A | UN-023 | The knowledge base ingestion pipeline shall not apply a date filter that excludes documents published or effective more than 50 years before the current year; RAG search queries shall include non-date-restricted and historically-scoped terms alongside current-year queries, so that agents can access and cite source material spanning at least 50 years | `rag_agent.py` contains no hard `cutoff_year`, `min_year`, or equivalent date filter rejecting documents older than 50 years; KB seed queries include at least one historically-scoped term not restricted to a specific recent year | P1 | VERIFIED |

---

## Operations & Monitoring

### UN-013 — Dashboard

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-013-A | UN-013 | Dashboard shall display agent health status (green/yellow/red) for all registered agents | `GET /api/dashboard` returns health entries for each agent | P1 | VERIFIED |
| DI-013-B | UN-013 | Dashboard shall display hourly token spend timeseries for today and yesterday | `GET /api/dashboard/timeseries` returns hourly buckets for both days | P1 | VERIFIED |
| DI-013-C | UN-013 | Dashboard shall display cumulative knowledge base growth over time | `GET /api/dashboard/knowledge-growth` returns daily + cumulative KB item counts | P1 | VERIFIED |
| DI-013-D | UN-013 | `loadData()` in App.jsx shall call `/api/dashboard` with `authHdr()` so the request is not rejected as Unauthorized | `App.jsx` `loadData` useCallback body includes `authHdr()` in the `/api/dashboard` fetch | P0 | VERIFIED |
| DI-013-E | UN-013 | All six Dashboard sub-fetches (history, timeseries, knowledge-growth, skills, sessions, decks) shall include `authHdr()` in their request headers | All six `fetch()` calls inside the `Dashboard` component include `{ headers: authHdr() }` | P1 | VERIFIED |
| DI-013-F | UN-013 | `loadData()` shall be called after `setToken()` completes — not in a parallel `useEffect` — to eliminate the startup race condition that causes a 401 on first load | `loadData()` is invoked inside the auth-token `useEffect` after `setToken()`, with no standalone `useEffect([loadData])` present | P1 | VERIFIED |

### UN-014 — Learning & Skills

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-014-A | UN-014 | Every agent run shall stamp `last_learning` regardless of whether new items were found | `last_learning` stamped in `agent_learning.py` even on no-op runs | P1 | VERIFIED |
| DI-014-B | UN-014 | `skills_profile.py` shall generate a per-agent skills profile and master SKILLS.md | Both files written by skills_profile.py; endpoint `POST /api/agents/skills-profile` exists | P1 | VERIFIED |

---

## Security & Compliance

### UN-015 — Security

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-015-A | UN-015 | No API keys or secrets shall appear in any `.py`, `.js`, `.jsx`, `.json`, or `.md` file tracked by git | Static grep over source tree finds no `ANTHROPIC_API_KEY=sk-` or similar patterns | P0 | VERIFIED |
| DI-015-B | UN-015 | All subprocess calls shall use `shell=False` | No `subprocess.run(..., shell=True)` in any Python source file | P0 | VERIFIED |
| DI-015-C | UN-015 | API shall enforce rate limiting at ≤ 120 requests per minute | Rate-limit middleware present in `server.py` | P0 | VERIFIED |
| DI-015-D | UN-015 | API shall set security headers (CSP, X-Frame-Options, X-Content-Type-Options) | Security header middleware present in `server.py` | P0 | VERIFIED |
| DI-015-E | UN-015 | File-serving endpoints shall reject path traversal attempts (`../`) | Path traversal check present in file-serving routes | P0 | VERIFIED |
| DI-015-F | UN-015 | Session authentication token shall be required for all non-health API endpoints | Auth middleware or dependency in server.py guards non-public routes | P0 | PARTIAL |
| DI-015-G | UN-015 | Every `fetch()` call to a non-exempt `/api/` endpoint in the frontend shall include `authHdr()` in its request headers — GET calls are not exempt | `dc_verify.py` `test_DI_015_G` scans all `.jsx`/`.js` source files for naked fetch calls | P0 | VERIFIED |

### UN-016 — Output Labeling & Disclaimer

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-016-A | UN-016 | Every finalized agent output shall include the canonical disclaimer text | `DISCLAIMER` constant defined in `orchestrator.py`; applied at finalize node | P0 | VERIFIED |
| DI-016-B | UN-016 | Every finalized agent output shall include the readiness label | `LABEL` constant defined in `orchestrator.py`; applied at finalize node | P0 | VERIFIED |
| DI-016-C | UN-016 | Output label shall be one of: Demo / Alpha / Beta / Production | Label value is one of the four permitted strings | P0 | VERIFIED |

### UN-017 — Audit Log

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-017-A | UN-017 | Voice session exchanges shall be logged to `voice/sessions.jsonl` | File exists and grows after a voice session | P1 | VERIFIED |
| DI-017-B | UN-017 | Full Athena session metadata shall be appended to `ui/logs/athena_sessions.jsonl` on shutdown | File exists; entry written by `stop_athena.ps1` | P1 | VERIFIED |
| DI-017-C | UN-017 | All agent outputs submitted to review shall be retrievable by review ID | `GET /api/review/{id}` returns the stored output | P1 | VERIFIED |

---

## Client Lifecycle

### UN-018 — Client Lifecycle Management

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-018-A | UN-018 | `POST /api/clients` shall return `{"status": "created", "client_id": <int>}` on success; database errors shall return a 500 JSON response with an `"error"` key containing the exception message | `server.py` `create_client` wraps `mem.add_client()` in try/except and returns error details on exception | P0 | VERIFIED |
| DI-018-B | UN-018 | Client intake form shall require Full Name, Email, and Program/Tier before submission; fields shall be highlighted with a red border and inline error message if left empty on submit | `ClientsView.jsx` `IntakeForm` validates `name`, `email`, and `program_tier`; per-field error state shown on failed submit | P0 | VERIFIED |

---

## Startup Experience

### UN-019 — Startup Splash Screen

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-019-A | UN-019 | Splash screen progress bar shall be absolutely positioned at the bottom edge of the window spanning its full width, with no side padding | `.bar-wrap` in `start_splash.hta` has `position:absolute; bottom:0; left:0; right:0` | P2 | VERIFIED |
| DI-019-B | UN-019 | Splash screen shall not display numeric percentage text during startup loading | No `id="pct"` element and no `pctEl.innerText` assignment in `start_splash.hta` | P2 | VERIFIED |
| DI-019-C | UN-019 | The splash screen progress bar shall advance through discrete stages tied to actual application loading state — the bar target shall not reach 100% until the `.athena_ready` flag file is detected, and the splash shall close automatically only after the bar has visually reached 100% | `start_splash.hta` contains a `PollChromeReady` (or equivalent) routine that sets `targetVal = 100` only after detecting `.athena_ready`; a `readyToClose` flag triggers `window.close()` only after `stepVal >= 100` | P0 | VERIFIED |

---

## Document Review & Approval

### UN-020 — AI-Generated Document Availability for Review and Approval

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-020-A | UN-020 | Every agent that produces a reviewable output shall call `submit_for_review()`, and the resulting entry shall appear in the review queue DB within the same agent run | `review_queue` table contains an entry with matching `agent` name and `status = 'pending'` after a representative agent run | P0 | VERIFIED |
| DI-020-B | UN-020 | The review queue UI shall fetch pending items using authenticated requests — `authHdr()` shall be present on the `GET /api/review/pending` fetch call in `ReviewView.jsx` | `ReviewView.jsx` `load()` function contains `authHdr()` in the fetch options | P0 | VERIFIED |
| DI-020-C | UN-020 | The review history UI shall fetch reviewed items using authenticated requests — `authHdr()` shall be present on the `GET /api/review/history` fetch call in `ReviewView.jsx` | `ReviewView.jsx` `loadHistory()` function contains `authHdr()` in the fetch options | P0 | VERIFIED |
| DI-020-D | UN-020 | The review queue shall automatically reload when the application receives an `agent_done` WebSocket event with `review_added > 0`, without requiring a manual page refresh | `ReviewView.jsx` contains a `useEffect` that calls `load()` when `reviewRefreshToken` is greater than 0 | P0 | VERIFIED |
| DI-020-E | UN-020 | Document content shall be viewable inline within the review queue — a viewer component shall fetch and render the document without navigating away from the Review tab | `ReviewView.jsx` contains a viewer component (`ReviewViewer`) that fetches `/api/review/{id}/content` and renders output inline | P1 | VERIFIED |

---

## Operations & Monitoring (continued)

### UN-021 — Single-Instance Enforcement

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-021-A | UN-021 | The Athena startup script shall detect whether another Athena instance is already running in the same Windows session by testing whether port 8000 is bound (`Get-NetTCPConnection`) or whether the recorded Chrome PID is still alive; if a running instance is found it shall either bring the existing instance to the foreground and exit cleanly without starting any new services, or stop the existing instance completely before starting a new one — at no point shall two complete Athena instances (backend + frontend + Chrome) be running simultaneously | `athena_lib.ps1` defines `Test-AthenaRunning` using `Get-NetTCPConnection -LocalPort 8000`; `start_athena.ps1` calls `Test-AthenaRunning` before starting any services and either exits without launching or runs `stop_athena.ps1` before proceeding | P0 | VERIFIED |

---

## Phase 2C — Client Lifecycle & Regulatory Agents

### UN-024 — Statement of Work Generation

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-024-A | UN-024 | SOW agent shall generate a branded .docx SOW, submit it to the review queue (Gate 10), and compute a Gate 3 confidence score ≥ 0.65 before final submission | `sow_agent.py` calls `submit_for_review()` after docx save; confidence score computed from required SOW element presence | P0 | VERIFIED |

### UN-025 — Regulatory Gap Assessment

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-025-A | UN-025 | Regulatory strategy agent shall generate a gap assessment .docx, submit it to the review queue (Gate 10), and compute a Gate 3 confidence score ≥ 0.65 | `regulatory_strategy_agent.py` calls `submit_for_review()` after docx save; confidence score present in metadata | P0 | VERIFIED |

### UN-026 — Application Startup Loading Experience

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-026-A | UN-026 | The React application shall display a full-screen loading overlay with animated progress bar from page load until the main WebSocket connection is established; the overlay shall dismiss automatically on first WS connect | `App.jsx` contains `startupDone` state; overlay shows while `!startupDone`; `ws.onopen` handler sets `startupDone = true` | P0 | VERIFIED |

### UN-027 — Documents Hub Approval Gate

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-027-A | UN-027 | The Documents hub (`GET /api/documents`) shall only surface files whose `file_path` appears in the `review_queue` table with `status = 'approved'` — pending, rejected, and unsubmitted files shall not appear | `server.py` `list_documents()` calls `mem.get_approved_reviews()` and filters disk scan to the approved path set | P0 | VERIFIED |

---

## Design Input Change Protocol

Adding a new DI requires:
1. Assign the next available DI-NNN-X ID in the appropriate UN section.
2. State the requirement so that pass/fail is unambiguous.
3. Define the verification method (what to check and where).
4. Set initial status to OPEN.
5. Add a corresponding `test_DI_NNN_X()` function to `dc_verify.py`.
6. Update DC-004 traceability matrix.
7. Change status to VERIFIED once the test passes on a real run.
