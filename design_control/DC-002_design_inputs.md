# DC-002 — Design Inputs
**Document:** DC-002 · Version 3.5 · 2026-06-07  
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
| DI-002-E | UN-002 | Approved items shall be surfaced exclusively under the Approved filter of the Document Queue tab; the Approved filter fetches from `GET /api/documents` which gates on `status='approved'` via `get_approved_reviews()` | `ReviewView.jsx` Approved tab calls `fetch(${API}/api/documents)` | P0 | VERIFIED |
| DI-002-F | UN-002 | The Document Queue tab shall provide three mutually-exclusive filter states: Pending (awaiting review), Approved (finalized), Rejected (declined) | `ReviewView.jsx` uses `useState("pending")` as initial tab state; tabs array contains keys "pending", "approved", "rejected" | P0 | VERIFIED |
| DI-002-G | UN-002 | `App.jsx` NAV_ITEMS shall contain `id:"queue"` (the Document Queue entry) and shall not contain `id:"documents"` or `id:"review"` (both retired nav entries) | `App.jsx` NAV_ITEMS string search | P0 | VERIFIED |
| DI-002-H | UN-002 | `AGENT_TAB` in `App.jsx` shall map every agent ID to a valid NAV_ITEMS tab ID — no retired values ("review" or "documents") shall appear as target values; `coaching_brief` → "coaching"; `consulting_agent`, `ma_intelligence_agent`, `sow_agent`, `regulatory_strategy_agent` → "queue" | `App.jsx` AGENT_TAB string search | P1 | VERIFIED |
| DI-002-I | UN-002 | `WorkQueuePanel` in `App.jsx` shall use `"queue"` (not `"review"`) as the routing target for tasks with `status === "awaiting_review"` | `App.jsx` WorkQueuePanel routing logic string search | P1 | VERIFIED |
| DI-002-J | UN-002 | `ReviewView.jsx` shall contain no duplicate import declarations — each imported identifier shall appear at most once; duplicate imports cause a Vite build failure that prevents the Document Queue from loading | `dc_verify.py` `test_DI_002_J` scans all import lines in `ReviewView.jsx` for repeated identical statements | P0 | VERIFIED |
| DI-002-K | UN-002 | The Approved-tab conditional expression in `ReviewView.jsx` shall be closed by the exact token sequence `)))}` — closing the map-callback paren, the `.map()` call, the outer ternary paren, and the JSX expression; a missing paren causes a Vite parse error that prevents the Document Queue from loading | `dc_verify.py` `test_DI_002_K` asserts `)))}` appears in `ReviewView.jsx` after the Approved-tab `.map(doc =>` pattern | P0 | VERIFIED |

### UN-003 — Knowledge Base

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-003-A | UN-003 | Knowledge base shall be searchable by all agents via `KBQuery.search()` | `kb_query.py` imports cleanly and `KBQuery()` instantiates | P1 | VERIFIED |
| DI-003-B | UN-003 | RAG ingestion agent shall index documents from FDA, EU MDR, and IMDRF sources | KB directory contains ≥1 JSON file per knowledge subdomain | P1 | VERIFIED |
| DI-003-C | UN-003 | RAG ingestion agent shall generate a Markdown ingestion report after each run and submit it to the review queue via `submit_for_review()`, with a report body that includes a "## Newly Ingested Documents" section listing each new document (title, URL, category, chunk count, **date_published**, **scope_summary**) or an explicit "No new documents ingested this run." message if none were found | `rag_agent.py` contains `submit_for_review()` call, "## Newly Ingested Documents" section header, `date_published`, and `scope_summary` | P1 | VERIFIED |
| DI-003-D | UN-003 | The ingestion report shall be written to a file matching the `rag_summary_` path pattern under the logs directory and shall include a fallback "No new documents ingested this run." message when zero documents were ingested in the run | `rag_agent.py` source contains both `rag_summary_` path pattern and "No new documents ingested" string | P1 | VERIFIED |

---

## Voice Interface

### UN-004 — Wake Word and Voice Interaction

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-004-A | UN-004 | System shall detect the active wake word with threshold ≤ 0.35 | `WAKE_THRESHOLD` in `voice_bridge.py` is ≤ 0.35 | P0 | VERIFIED |
| DI-004-B | UN-004 | System shall transcribe voice queries via Whisper and log confidence score | Whisper model loads at startup; `[low conf]` tag written to log on low-confidence result | P0 | VERIFIED |
| DI-004-C | UN-004 | First TTS audio byte shall be produced within 2 seconds of query completion | Streaming sentence-split pipeline; first sentence dispatched to Kokoro before full response | P0 | PARTIAL |
| DI-004-D | UN-004 | Voice bridge shall classify query intent and route to the correct agent via `tool_use` | `voice_bridge.py` contains tool-use dispatch logic | P0 | VERIFIED |
| DI-004-E | UN-004 | SILENCE_DURATION, loaded from settings.json `voice.silence_duration`, shall be in the range [0.4, 0.65] s — values below 0.4 risk mid-sentence cutoff; values above 0.65 cause unacceptable latency on the RTX 4070 + Whisper base.en stack; current tuned value is 0.5 s (C3 update 2026-06-06) | `SILENCE_DURATION` in `voice_bridge.py` and `settings.json voice.silence_duration` are each in [0.4, 0.65] | P0 | VERIFIED |

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
| DI-022-A | UN-022 | Latency between completion of user's voice input and commencement of audible agent response shall be ≤ 1.75 seconds (tightened from 2 s in CO-016; see also DI-004-C for TTS pipeline timing) | Static: `DC-002_design_inputs.md` DI-022-A text states "1.75" seconds; `voice_bridge.py` contains `_ask_claude_streaming` using a streaming LLM call, `_split_sentences` / `_SENTENCE_END` for sentence-boundary detection, and `_speak_sentence` called inside the token-stream loop — not after full response is buffered | P0 | OPEN |

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
| DI-007-F | UN-007 | Navigation tab for MedTech Meridian content shall use `label:"MedTech Meridian Drafts"` in `NAV_ITEMS` and `ContentView` h2 shall read "MedTech Meridian Drafts" — the retired label "Content Drafts" shall not appear in either location | `App.jsx` NAV_ITEMS and ContentView h2 string search | P1 | VERIFIED |
| DI-007-G | UN-007 | `content_agent.py` `DEVICE_SUBSECTORS` list shall contain entries mapping to all 6 required MedTech sector groups: Cardiology, IVD (In Vitro Diagnostics), Diagnostic Imaging, Orthopedics & Prosthetics, Surgical & Medical Instruments, Digital Health & Connected Care — ensuring deliverables can span all major MedTech verticals | `content_agent.py` contains all 6 required sector keywords: `Cardiology`, `IVD`, `Imaging`, `Orthopedic`, `Surgical`, `Digital Health` (case-insensitive) | P1 | VERIFIED |
| DI-007-H | UN-007 | Sector and topic-category fallback selection in `content_agent.py` shall use deterministic day-of-year modulo bucketing (`tm_yday`) rather than `random.choice` so that the same calendar day always produces the same fallback sector and consecutive days produce different outputs | `content_agent.py` contains `tm_yday` and does NOT contain `random.choice` | P1 | VERIFIED |

### UN-008 — Marketing Pipeline

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-008-A | UN-008 | Marketing agent shall maintain a pipeline DB with ≥ 20 targets | `ops/marketing/pipeline.db` created on first run with ≥ 20 seed targets | P1 | PARTIAL |
| DI-008-B | UN-008 | All outreach channels shall be zero-cash-budget (no paid media at Alpha) | No paid channel types in pipeline seed data | P1 | PARTIAL |
| DI-008-C | UN-008 | `MarketingView.jsx` shall provide a bulk-select-and-delete capability for marketing output files using the `BulkBar` / `useMultiSelect` pattern — checkboxes per file, a bulk-action bar showing selected count, and a delete-selected action calling `/api/files/delete-bulk` with `folder: "marketing"` | `MarketingView.jsx` contains `useMultiSelect`, `BulkBar`, and `delete-bulk` string | P1 | VERIFIED |

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
| DI-011-C | UN-011 | `ma_intelligence_agent.py` system prompt shall explicitly state that historical M&A requests from any year (including pre-2020) are within scope and shall not be declined based on the age of the data — historical analysis dating back to the 1970s is a core capability | `ma_intelligence_agent.py` contains `historical` and a statement that historical requests are in scope (e.g., "historical" + "in scope" or "1970" or "any year") | P1 | VERIFIED |

### UN-012 — Regulatory Briefings

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-012-A | UN-012 | Briefing agent shall produce structured briefs covering FDA, EU MDR, and IMDRF | Briefing agent sources include all three frameworks | P1 | VERIFIED |
| DI-012-B | UN-012 | Briefing outputs shall enter the review queue via `submit_for_review()` | `submit_for_review()` called in `briefing_agent.py` | P1 | VERIFIED |

### UN-023 — Historical Data Depth

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-023-A | UN-023 | The knowledge base ingestion pipeline shall not apply a date filter that excludes documents published or effective more than 50 years before the current year; RAG search queries shall include non-date-restricted and historically-scoped terms alongside current-year queries, so that agents can access and cite source material spanning at least 50 years | `rag_agent.py` contains no hard `cutoff_year`, `min_year`, or equivalent date filter rejecting documents older than 50 years; KB seed queries include at least one historically-scoped term not restricted to a specific recent year | P1 | VERIFIED |
| DI-023-B | UN-023 | `TAVILY_QUERIES` in `rag_agent.py` shall include at least 5 entries that contain a historical marker term — one of: "history", "historical", "evolution", "origin", "1970", "1980", "1990", "2000s" — so that the Tavily search pipeline actively retrieves pre-2020 QARA source material spanning the 50-year scope defined in UN-023 | Count of `TAVILY_QUERIES` entries matching `history\|historical\|evolution\|origin\|1970\|1980\|1990\|2000s` ≥ 5 | P1 | OPEN |
| DI-023-C | UN-023 | Tavily query selection per run shall use deterministic day-of-year modulo bucketing (`datetime.now().timetuple().tm_yday`) rather than `random.sample()` so that the same calendar day always executes the same query bucket and adjacent days execute different buckets, enabling predictable full-corpus coverage | `rag_agent.py` contains `tm_yday` and does NOT contain `random.sample` | P1 | OPEN |
| DI-023-D | UN-023 | `consulting_agent.py` shall define a `HISTORICAL_CONSULTING_SOURCES` list with at least 5 entries whose `"name"` field contains a historical marker term — one of: "history", "historical", "evolution", "origin", "1970", "1980", "1990", "2000s", "50 year", "classic" — so that the consulting learning pipeline actively retrieves management consulting knowledge spanning the 50-year scope defined in UN-023 | Count of `HISTORICAL_CONSULTING_SOURCES` entries in `consulting_agent.py` whose `"name"` value matches `history\|historical\|evolution\|origin\|1970\|1980\|1990\|2000s\|50.year\|classic` ≥ 5 | P1 | OPEN |

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
| DI-019-B | UN-019 | Splash screen shall display a percentage label floated right above the progress bar track, styled per Adobe Spectrum progress bar guidelines | `id="pct"` element present in `start_splash.hta` HTML; `pctEl.innerText` assigned in VBScript Tick sub; `.pct-text` CSS includes `float:right` | P2 | VERIFIED |
| DI-019-C | UN-019 | The splash screen progress bar shall advance through discrete stages tied to actual application loading state — the bar target shall not reach 100% until the `.athena_ready` flag file is detected, and the splash shall close automatically only after the bar has visually reached 100% | `start_splash.hta` contains a `PollChromeReady` (or equivalent) routine that sets `targetVal = 100` only after detecting `.athena_ready`; a `readyToClose` flag triggers `window.close()` only after `stepVal >= 99.5` (99.9 displays as "100%" via `CInt` rounding — exact `= 100` would never fire) | P0 | VERIFIED |
| DI-019-F | UN-019 | Splash progress bar shall load smoothly per standard UI/UX best practices — the Tick animation loop shall use asymptotic easing with a guaranteed minimum per-frame increment so the bar is always visibly moving while behind its target | `start_splash.hta` Tick sub contains asymptotic expression `(targetVal - stepVal) * 0.N` and minimum floor `If inc < N Then inc = N` | P2 | VERIFIED |
| DI-019-G | UN-019 | The interval between splash screen close and Chrome opening shall be less than 3 seconds | `start_athena.ps1` polls for `.athena_splash_done` at 200ms intervals; the maximum gap from splash-done signal to Chrome launch is < 400ms (200ms poll + process launch overhead), well within 3 seconds | P2 | VERIFIED |
| DI-019-H | UN-019 | The progress bar shall not remain at any single whole-number percentage for more than 1 second due to animation algorithm constraints — enforced by: (a) a minimum per-frame increment floor in the Tick loop, (b) a minimum per-poll advancement floor in PollChromeReady, (c) a PollChromeReady cap ≤ 98 so that `Int()` display can never show "100%" while loading is incomplete, and (d) a mathematical proof that the Tick easing can traverse from the cap to the 99.5 close-trigger in < 1000 ms: `(99.5 − cap) ÷ min_floor × 16 ms < 1000 ms` | `start_splash.hta` Tick floor; PollChromeReady floor + cap ≤ 98; `Int(stepVal)` display; computed `(99.5 − cap) / min_floor * 16 < 1000` | P2 | VERIFIED |
| DI-019-I | UN-019 | The splash screen "Athena" title (`.name`) font-size shall be 101px — `start_splash.hta` fixed value and `electron/main.js` clamp maximum shall both equal 101px | `start_splash.hta` `.name` CSS contains `font-size:101px`; `electron/main.js` `.name` CSS clamp is `clamp(61px,7vw,101px)` | P2 | VERIFIED |
| DI-019-J | UN-019 | The `#dots` element shall cycle its displayed text through a one-dot (`.`), two-dot (`..`), and three-dot (`...`) sequence at a fixed interval of ≤ 500 ms per state, driven by a VBScript timer (not CSS animation), while loading is in progress; the dots shall be hidden when loading completes | `start_splash.hta` contains a `TickDots` sub using 3-state cycling; `setInterval("TickDots", N)` with N ≤ 500; `dotsEl.style.display = "none"` on completion | P2 | VERIFIED |
| DI-019-K | UN-019 | The Athena startup sequence shall not gate Chrome opening on voice model readiness — the `$modelTimeout` polling loop that blocks `.athena_ready` on `models_ready = true` from `/api/voice/status` shall be absent from `start_athena.ps1`; voice models shall preload asynchronously after Chrome opens; on warm start (Python env active, all model files present on disk), the total time from launch invocation to Chrome window opening shall be less than 10 seconds | `start_athena.ps1` does not contain `$modelTimeout` variable | P1 | OPEN |
| DI-019-L | UN-019 | Chrome shall not open until the splash screen confirms its progress bar has reached 100% by writing a `.athena_splash_done` signal file; `start_splash.hta` shall contain a `CloseSplash` sub that writes the signal file before calling `window.close()`; `start_athena.ps1` shall poll for this file (up to 6000ms timeout) before launching Chrome and shall not use a fixed sleep as the sole gating mechanism | Static: `start_splash.hta` contains `CloseSplash` sub that writes `.athena_splash_done` before `window.close()`; `start_athena.ps1` contains `athena_splash_done` poll loop; `Start-Sleep -Milliseconds 2500` is absent from the Chrome-launch path | P0 | OPEN |

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

## Deliverable Formatting Standard

### UN-030 — McKinsey/Latitude Brand Formatting Standard

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-030-A | UN-030 | All 6 `_DECK_GUIDES` entries in `deck_agent.py` ("strategy", "pitch", "regulatory", "coaching", "ma", "briefing") shall include "exec_summary" in their slide-sequence string so that every deck type leads with a McKinsey-standard executive summary slide | All 6 values in `_DECK_GUIDES` contain "exec_summary" | P1 | VERIFIED |
| DI-030-B | UN-030 | All 6 deliverable-generating agent Python files (`content_agent.py`, `briefing_agent.py`, `ma_intelligence_agent.py`, `regulatory_strategy_agent.py`, `sow_agent.py`, `deck_agent.py`) shall contain at least one of "McKinsey", "Big 4", "pyramid", or "SCQA" as a quality directive in their system prompt or agent description | Grep across the 6 files for `McKinsey\|Big.4\|pyramid\|SCQA` | P1 | VERIFIED |
| DI-030-C | UN-030 | `agent_base.py` shall inject "Latitude MedTech LLC" brand identity into all agent system prompts via a system-prompt construction routine | `agent_base.py` contains "Latitude MedTech LLC" and a system-prompt construction pattern (function or list) | P1 | VERIFIED |
| DI-030-D | UN-030 | `agent_base.py` shall define a `PUBLICATION_FORMAT_GUIDE` class-level dict mapping each agent name to a publication-style directive string, and `system_prompt()` shall inject the matching directive into the system prompt via `PUBLICATION_FORMAT_GUIDE.get(self.name, "")` | `agent_base.py` contains `PUBLICATION_FORMAT_GUIDE` dict AND `PUBLICATION_FORMAT_GUIDE.get(self.name` in `system_prompt()` | P1 | VERIFIED |
| DI-030-E | UN-030 | All 8 production agent persona files (content, briefing, consulting, ma-intelligence, marketing, iso, deck, coaching) shall contain a `## Output Format Standard` section that specifies the publication style for that agent | Each of the 8 `.claude/agents/<name>-agent.md` files contains `## Output Format Standard` | P1 | VERIFIED |

---

## Browser Tab Singleton

### UN-031 — Browser Tab Singleton Enforcement

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-031-A | UN-031 | When the Athena frontend loads in a browser tab, it shall acquire a named singleton lock via `BroadcastChannel`; if another tab already holds the lock (detected via a `localStorage` heartbeat key that is updated at least once per second and expires after 3 seconds), the second tab shall immediately display a "Athena is already open in another tab — close this tab." blocking overlay and shall not initialize the React application | Static: `tabGuard.js` in `ui/frontend/src/` exists and contains `BroadcastChannel` and a blocking overlay render; `main.jsx` imports and calls `initTabGuard` and only mounts React when the call returns truthy | P0 | VERIFIED |
| DI-031-B | UN-031 | The singleton lock shall be released automatically when the holding tab closes or navigates away — on `beforeunload` the lock holder shall broadcast a `release` message via the `BroadcastChannel` and remove the `localStorage` lock key, so that a reloaded or replacement tab can acquire the lock immediately without waiting for a stale-lock timeout | Static: `tabGuard.js` contains a `beforeunload` event listener that calls `ch.postMessage({ type: "release" ... })` and removes the `localStorage` lock key | P0 | VERIFIED |

---

## Agent Learning Visibility

### UN-032 — Consulting Agent Learning Reports

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-032-A | UN-032 | `consulting_agent.py`'s `learn()` shall generate a Markdown learning summary report after each run and submit it to the review queue via `submit_for_review()`, with a report body that includes a "## Newly Ingested Items" section listing each new item (title, source, URL, category, chunk count) or an explicit "No new items ingested this run." message if none were found | `consulting_agent.py` contains `submit_for_review(` call AND "## Newly Ingested Items" section header string | P1 | OPEN |
| DI-032-B | UN-032 | The consulting learning report shall be written to a file matching the `consulting_learning_` path pattern under the logs directory and shall include a fallback "No new items ingested this run." message when zero items were ingested in the run | `consulting_agent.py` source contains both `consulting_learning_` path pattern and `"No new items ingested this run."` string | P1 | OPEN |

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

### UN-033 — Voice Query Readiness Latency

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-033-A | UN-033 | `_listen_for_wake` shall accept a `stream` parameter and shall not open an `sd.InputStream` internally | `voice_bridge.py` `def _listen_for_wake` signature contains `stream` parameter; no `sd.InputStream(` in body | P1 | VERIFIED |
| DI-033-B | UN-033 | `_record_query` shall accept a `stream` parameter and shall not open an `sd.InputStream` internally | `voice_bridge.py` `def _record_query` signature contains `stream` parameter; no `sd.InputStream(` in body | P1 | VERIFIED |
| DI-033-C | UN-033 | `_voice_loop` shall open exactly one `sd.InputStream` per listen/record cycle and pass it to both `_listen_for_wake` and `_record_query` | `voice_bridge.py` `_voice_loop` body contains `with sd.InputStream(`; calls `_listen_for_wake(oww, stream)` and `_record_query(stream)` | P1 | VERIFIED |

### UN-034 — Engineering Process Integrity

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-034-A | UN-034 | `CLAUDE.md` shall contain the co-commit rule: any code commit affecting a behavioral change **must also update at least one design control document** | `CLAUDE.md` contains phrase "must also update at least one design control document" | P0 | VERIFIED |
| DI-034-B | UN-034 | `CLAUDE.md` shall contain an Auth Centralization Standard section declaring that all authentication logic lives exclusively in `AuthMiddleware` and `auth_utils.py` | `CLAUDE.md` contains "Auth Centralization Standard" | P1 | VERIFIED |
| DI-034-C | UN-034 | `CLAUDE.md` shall contain a voice_bridge.py Boundary section declaring that `voice_bridge.py` owns all audio I/O | `CLAUDE.md` contains "voice_bridge.py Boundary" | P1 | VERIFIED |
| DI-034-D | UN-034 | `CLAUDE.md` shall document the forward-only progress bar constraint in a Progress Bar Specification section | `CLAUDE.md` contains "Progress Bar Specification" | P1 | VERIFIED |
| DI-034-E | UN-034 | `CLAUDE.md` shall contain an App.jsx Responsibility Scope section defining what `App.jsx` owns and does not own | `CLAUDE.md` contains "App.jsx Responsibility Scope" | P1 | VERIFIED |
| DI-034-F | UN-034 | `CLAUDE.md` shall contain a CLAUDE.md Update Policy section declaring when this file must be updated | `CLAUDE.md` contains "CLAUDE.md Update Policy" | P1 | VERIFIED |

---

## Voice Widget Docking

### UN-035 — Voice Widget Docking Persistence

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-035-A | UN-035 | The `FloatingVoiceWidget` docked bar JSX style object in `App.jsx` shall include `width: "auto"` and `right: 0` so that React resets any inline `width` set during undock and the bar spans the full application width on every subsequent dock operation | `App.jsx` `FloatingVoiceWidget` docked bar style contains `width: "auto"` and `right: 0` | P1 | VERIFIED |

---

## Agent Tab Approval Gate

### UN-036 — Agent Tab Approval Gate

| ID | Source | Requirement Statement | Verification | Priority | Status |
|---|---|---|---|---|---|
| DI-036-A | UN-036 | `AGENT_TAB` in `App.jsx` shall map `briefing_agent`, `content_agent`, `coaching_brief`, `marketing_agent`, `deck_agent`, and `iso_coach` to `"queue"` so that their outputs are routed to the Document Queue for approval before appearing in any agent-specific tab | `App.jsx` AGENT_TAB entries for those 6 agent IDs all equal `"queue"` | P0 | VERIFIED |
| DI-036-B | UN-036 | `server.py` `list_briefings()` and `list_drafts()` shall filter their file listings to only files whose `file_path` appears in `mem.get_approved_reviews()`, matching the approval-gate pattern in `list_documents()` | `server.py` `list_briefings` and `list_drafts` functions each contain `get_approved_reviews` | P0 | VERIFIED |
| DI-036-C | UN-036 | `server.py` `list_briefs()` and `list_marketing_outputs()` shall filter their file listings to only files whose `file_path` appears in `mem.get_approved_reviews()`, matching the approval-gate pattern in `list_documents()` | `server.py` `list_briefs` and `list_marketing_outputs` functions each contain `get_approved_reviews` | P0 | VERIFIED |
| DI-036-D | UN-036 | `server.py` `list_decks()` shall filter its file listing to only `.pptx` files whose `file_path` appears in `mem.get_approved_reviews()`, matching the approval-gate pattern in `list_documents()` | `server.py` `list_decks` function contains `get_approved_reviews` | P0 | VERIFIED |
| DI-036-E | UN-036 | `server.py` `list_iso_lessons()` shall filter its file listing to only `.md` files whose `file_path` appears in `mem.get_approved_reviews()`, matching the approval-gate pattern in `list_documents()` | `server.py` `list_iso_lessons` function contains `get_approved_reviews` | P0 | VERIFIED |

