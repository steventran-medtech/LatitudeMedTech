# DC-004 — Requirements Traceability Matrix (RTM)
**Document:** DC-004 · Version 3.4 · 2026-06-07
**Approved by:** Steven Tran

This is the single source of truth for end-to-end coverage. Every user need
shall trace to ≥1 design input. Every design input shall trace to ≥1 design
output. Every design input shall trace to ≥1 verification test. Gaps in any
column are open findings requiring immediate remediation.

---

## How to Read This Table

- **UN → DI**: User need is addressed by these requirements.
- **DI → DO**: Requirement is implemented by these files/symbols (see DC-003).
- **Verification Test**: Function name in `dc_verify.py` that checks this DI.
- **Status**: VERIFIED / PARTIAL / OPEN / WAIVED.

---

## Traceability Matrix

| UN | User Need Summary | DI | Design Input Summary | Primary Design Output | Verification Test | Status |
|---|---|---|---|---|---|---|
| UN-001 | Client briefing generation | DI-001-A | Brief generated from name | `orchestrator.py` intake→generate_brief | `test_DI_001_A` | VERIFIED |
| UN-001 | | DI-001-B | Brief enters review queue | `memory.py` add_review_item | `test_DI_001_B` | VERIFIED |
| UN-001 | | DI-001-C | Readiness label on output | `orchestrator.py` LABEL | `test_DI_001_C` | VERIFIED |
| UN-001 | | DI-001-D | Disclaimer on output | `orchestrator.py` DISCLAIMER | `test_DI_001_D` | VERIFIED |
| UN-002 | Human review gate | DI-002-A | All outputs to review queue | `server.py` review routes | `test_DI_002_A` | VERIFIED |
| UN-002 | | DI-002-B | Approve action | `server.py` POST /api/review/{id}/approve | `test_DI_002_B` | VERIFIED |
| UN-002 | | DI-002-C | Reject action | `server.py` POST /api/review/{id}/reject | `test_DI_002_C` | VERIFIED |
| UN-002 | | DI-002-D | Edit-and-rewrite action | `server.py` POST /api/review/{id}/edit | `test_DI_002_D` | VERIFIED |
| UN-002 | | DI-002-E | Approved items in Document Queue Approved filter only | `ReviewView.jsx` `loadApproved()` + `GET /api/documents` | `test_DI_002_E` | VERIFIED |
| UN-002 | | DI-002-F | Three-state filter: Pending/Approved/Rejected | `ReviewView.jsx` `useState("pending")` + tabs array | `test_DI_002_F` | VERIFIED |
| UN-002 | | DI-002-G | App.jsx NAV_ITEMS has id:queue; id:documents and id:review absent | `App.jsx` NAV_ITEMS | `test_DI_002_G` | VERIFIED |
| UN-002 | | DI-002-H | AGENT_TAB maps all agents to valid NAV_ITEMS tab IDs | `App.jsx` AGENT_TAB — no "review"/"documents" values; coaching_brief→"coaching"; 4 agents→"queue" | `test_DI_002_H` | VERIFIED |
| UN-002 | | DI-002-I | WorkQueuePanel routes awaiting_review to "queue" not "review" | `App.jsx` WorkQueuePanel routing expression | `test_DI_002_I` | VERIFIED |
| UN-002 | | DI-002-J | ReviewView.jsx has no duplicate import declarations | `ReviewView.jsx` import lines — no repeated statement | `test_DI_002_J` | VERIFIED |
| UN-002 | | DI-002-K | Approved-tab conditional closes with )))}: arrow-fn paren + map call + ternary paren + JSX expr | `ReviewView.jsx` contains `)))}` sequence | `test_DI_002_K` | VERIFIED |
| UN-003 | Knowledge base | DI-003-A | KBQuery searchable by agents | `kb_query.py` KBQuery | `test_DI_003_A` | VERIFIED |
| UN-003 | | DI-003-B | RAG indexes FDA/EU/IMDRF | `knowledge_base/` subdirs | `test_DI_003_B` | VERIFIED |
| UN-003 | | DI-003-C | RAG report with "Newly Ingested Documents" section + `date_published` + `scope_summary` fields per document | `agents/rag_agent.py` `main()` + `submit_for_review()` + `date_published` + `scope_summary` | `test_DI_003_C` | VERIFIED |
| UN-003 | | DI-003-D | Report written to `rag_summary_<ts>.md` with "No new documents" fallback | `agents/rag_agent.py` report write + fallback string | `test_DI_003_D` | VERIFIED |
| UN-004 | Voice interaction | DI-004-A | Wake threshold ≤ 0.35 | `voice_bridge.py` WAKE_THRESHOLD | `test_DI_004_A` | VERIFIED |
| UN-004 | | DI-004-B | Whisper STT + confidence log | `voice_bridge.py` whisper | `test_DI_004_B` | VERIFIED |
| UN-004 | | DI-004-C | First audio ≤ 2s | Kokoro streaming pipeline | `test_DI_004_C` | PARTIAL |
| UN-004 | | DI-004-D | Intent routing via tool_use | `voice_bridge.py` dispatch | `test_DI_004_D` | VERIFIED |
| UN-004 | | DI-004-E | SILENCE_DURATION in [0.4, 0.65] s (C3 update 2026-06-06; tuned to 0.5 s) | `voice_bridge.py` constant + settings.json | `test_DI_004_E` | VERIFIED |
| UN-005 | Task notifications | DI-005-A | Notify endpoint exists | `server.py` POST /api/voice/notify | `test_DI_005_A` | VERIFIED |
| UN-005 | | DI-005-B | Notification only if voice active | `voice_bridge.py` queue guard | `test_DI_005_B` | VERIFIED |
| UN-006 | Persistent voice session | DI-006-A | Session persists across tabs | `useVoiceSession.js` app-level | `test_DI_006_A` | VERIFIED |
| UN-006 | | DI-006-B | Status badge in header | `App.jsx` VoiceStatusBadge | `test_DI_006_B` | VERIFIED |
| UN-022 | Voice conversation quality | DI-022-A | Latency ≤ 1.75 s (tightened from 2 s, CO-016); streaming sentence-split pipeline; first sentence dispatched to TTS before full response buffered | `voice_bridge.py` `_ask_claude_streaming` + `_SENTENCE_END` + `_speak_sentence` in token-stream loop; live timing manual (MTP-003) | `test_DI_022_A` | PARTIAL |
| UN-007 | Content generation | DI-007-A | 900–1,200 word articles | `content_agent.py` system prompt word-count instruction | `test_DI_007_A` | VERIFIED |
| UN-007 | | DI-007-B | Title from body H1 | `content_agent.py` title_from_body | `test_DI_007_B` | VERIFIED |
| UN-007 | | DI-007-C | Banned phrases enforced | `content_agent.py` system prompt | `test_DI_007_C` | VERIFIED |
| UN-007 | | DI-007-D | Non-Latin chars stripped | `content_agent.py` clean_title | `test_DI_007_D` | VERIFIED |
| UN-007 | | DI-007-E | YAML frontmatter stripped in UI | `App.jsx` renderInline | `test_DI_007_E` | VERIFIED |
| UN-007 | | DI-007-F | Content tab labeled "MedTech Meridian Drafts" in NAV_ITEMS and ContentView h2 | `App.jsx` NAV_ITEMS label + ContentView h2 | `test_DI_007_F` | VERIFIED |
| UN-007 | | DI-007-G | DEVICE_SUBSECTORS covers all 6 MedTech sectors | `content_agent.py` `DEVICE_SUBSECTORS` | `test_DI_007_G` | VERIFIED |
| UN-007 | | DI-007-H | Sector/topic fallback uses `tm_yday` not `random.choice` | `content_agent.py` `_get_next_subsector()` + `_get_next_topic_category()` | `test_DI_007_H` | VERIFIED |
| UN-008 | Marketing pipeline | DI-008-A | Pipeline DB ≥ 20 targets | `marketing_agent.py` seed count ≥ 20 verified by `test_DI_008_A` | `test_DI_008_A` | VERIFIED |
| UN-008 | | DI-008-B | Zero-cash channels only | `marketing_agent.py` seed data; `test_DI_008_B` scans for paid types | `test_DI_008_B` | VERIFIED |
| UN-008 | | DI-008-C | MarketingView bulk-select-and-delete via BulkBar pattern | `MarketingView.jsx` `useMultiSelect` + `BulkBar` + `delete-bulk` | `test_DI_008_C` | VERIFIED |
| UN-009 | Slide deck generation | DI-009-A | Deck with required sections | `deck_agent.py` slide sequence | `test_DI_009_A` | PARTIAL |
| UN-009 | | DI-009-B | Latitude brand palette | `deck_agent.py` colour constants | `test_DI_009_B` | VERIFIED |
| UN-009 | | DI-009-C | DeckView gallery + download | `server.py` deck routes | `test_DI_009_C` | VERIFIED |
| UN-010 | ISO 13485 coach | DI-010-A | Any clause on demand | `iso_coach_agent.py` clause lookup | `test_DI_010_A` | VERIFIED |
| UN-010 | | DI-010-B | One clause at a time; no --all from UI | `iso_coach_agent.py` sequential logic | `test_DI_010_B` | VERIFIED |
| UN-010 | | DI-010-C | No verbatim ISO text in RAG | `iso.org` removed from Tavily `include_domains` in `rag_agent.py` (CO-018); `test_DI_010_C` confirms exclusion | `test_DI_010_C` | VERIFIED |
| UN-011 | M&A intelligence | DI-011-A | QARA frameworks in analysis | `ma_intelligence_agent.py` | `test_DI_011_A` | VERIFIED |
| UN-011 | | DI-011-B | Cited sources + dates | M&A agent system prompt | `test_DI_011_B` | VERIFIED |
| UN-011 | | DI-011-C | M&A system prompt explicitly accepts historical requests from any year | `agents/ma_intelligence_agent.py` system prompt | `test_DI_011_C` | VERIFIED |
| UN-012 | Regulatory briefings | DI-012-A | FDA + EU MDR + IMDRF coverage | `briefing_agent.py` sources | `test_DI_012_A` | VERIFIED |
| UN-012 | | DI-012-B | Briefings enter review queue | `briefing_agent.py` submit_for_review | `test_DI_012_B` | VERIFIED |
| UN-023 | Historical data depth | DI-023-A | No date cutoff blocking >50-year-old sources; KB queries include historically-scoped terms | `rag_agent.py` no hard year filter; seed queries include non-date-restricted terms | `test_DI_023_A` | VERIFIED |
| UN-023 | | DI-023-B | TAVILY_QUERIES includes ≥5 historically-scoped entries (history/evolution/1970s/etc.) | `agents/rag_agent.py` `TAVILY_QUERIES` | `test_DI_023_B` | VERIFIED |
| UN-023 | | DI-023-C | Tavily rotation uses `tm_yday` not `random.sample` | `agents/rag_agent.py` `ingest_tavily()` | `test_DI_023_C` | VERIFIED |
| UN-023 | | DI-023-D | HISTORICAL_CONSULTING_SOURCES in consulting_agent.py has ≥5 entries with historical marker terms | `agents/consulting_agent.py` `HISTORICAL_CONSULTING_SOURCES` | `test_DI_023_D` | VERIFIED |
| UN-013 | Dashboard | DI-013-A | Agent health (green/yellow/red) | `server.py` /api/dashboard | `test_DI_013_A` | VERIFIED |
| UN-013 | | DI-013-B | Hourly token timeseries | `server.py` /api/dashboard/timeseries | `test_DI_013_B` | VERIFIED |
| UN-013 | | DI-013-C | KB growth chart | `server.py` /api/dashboard/knowledge-growth | `test_DI_013_C` | VERIFIED |
| UN-013 | | DI-013-D | loadData() sends authHdr() to /api/dashboard | `App.jsx` `loadData` useCallback body | `test_DI_013_D` | VERIFIED |
| UN-013 | | DI-013-E | All Dashboard sub-fetches send authHdr() | `App.jsx` Dashboard useEffect fetches | `test_DI_013_E` | VERIFIED |
| UN-013 | | DI-013-F | loadData deferred until after setToken() — no race | `App.jsx` auth-token useEffect calls loadData after setToken | `test_DI_013_F` | VERIFIED |
| UN-014 | Learning & skills | DI-014-A | last_learning stamped on no-op | `agent_learning.py` stamp logic | `test_DI_014_A` | VERIFIED |
| UN-014 | | DI-014-B | Per-agent profiles + SKILLS.md | `skills_profile.py` | `test_DI_014_B` | VERIFIED |
| UN-015 | Security | DI-015-A | No secrets in source code | Source tree static grep | `test_DI_015_A` | VERIFIED |
| UN-015 | | DI-015-B | shell=False everywhere | Source tree grep | `test_DI_015_B` | VERIFIED |
| UN-015 | | DI-015-C | Rate limiting at 120 req/min | `server.py` middleware | `test_DI_015_C` | VERIFIED |
| UN-015 | | DI-015-D | Security headers | `server.py` middleware | `test_DI_015_D` | VERIFIED |
| UN-015 | | DI-015-E | Path traversal protection | `server.py` file routes | `test_DI_015_E` | VERIFIED |
| UN-015 | | DI-015-F | Session auth on all routes | `AuthMiddleware` blanket coverage + `_AUTH_EXEMPT` scope verified by `test_DI_015_F` | `test_DI_015_F` | VERIFIED |
| UN-015 | | DI-015-G | authHdr() on every frontend /api/ fetch | All `.jsx`/`.js` source files | `test_DI_015_G` | VERIFIED |
| UN-016 | Output labeling | DI-016-A | Disclaimer on all outputs | `orchestrator.py` DISCLAIMER | `test_DI_016_A` | VERIFIED |
| UN-016 | | DI-016-B | Readiness label on all outputs | `orchestrator.py` LABEL | `test_DI_016_B` | VERIFIED |
| UN-016 | | DI-016-C | Label is permitted value | `orchestrator.py` label value | `test_DI_016_C` | VERIFIED |
| UN-017 | Audit log | DI-017-A | Voice sessions logged | `voice/sessions.jsonl` | `test_DI_017_A` | VERIFIED |
| UN-017 | | DI-017-B | Athena sessions logged | `ui/logs/athena_sessions.jsonl` pattern | `test_DI_017_B` | VERIFIED |
| UN-017 | | DI-017-C | Review items retrievable by ID | `server.py` GET /api/review/{id} | `test_DI_017_C` | VERIFIED |
| UN-018 | Client lifecycle | DI-018-A | Client creation returns ID; db errors return 500 JSON | `server.py` create_client | `test_DI_018_A` | VERIFIED |
| UN-018 | | DI-018-B | Intake form required-field validation (name, email, tier) | `ClientsView.jsx` IntakeForm | `test_DI_018_B` | VERIFIED |
| UN-019 | Startup experience | DI-019-A | Progress bar absolutely positioned full-width at bottom | `start_splash.hta` `.bar-wrap` CSS | `test_DI_019_A` | VERIFIED |
| UN-019 | | DI-019-B | Float-right percentage label per Spectrum design | `start_splash.hta` `id="pct"` + `pctEl.innerText` + `float:right` CSS | `test_DI_019_B` | VERIFIED |
| UN-019 | | DI-019-C | Bar advances through real loading stages; reaches 100% only on `.athena_ready`; splash closes only after `stepVal >= 99.5` | `start_splash.hta` `PollChromeReady` + `readyToClose` + `stepVal >= 99.5` gate | `test_DI_019_C` | VERIFIED |
| UN-019 | | DI-019-F | Smooth loading — asymptotic easing + minimum per-frame floor in Tick | `start_splash.hta` Tick asymptotic factor + `If inc <` floor | `test_DI_019_F` | VERIFIED |
| UN-019 | | DI-019-G | Splash→Chrome gap < 3 seconds | `start_athena.ps1` polls `.athena_splash_done` at 200ms; max gap < 400ms | `test_DI_019_G` | VERIFIED |
| UN-019 | | DI-019-H | Bar never stalls > 1 s; cap ≤ 98 + mathematical bound `(99.5−cap)/floor×16 ms < 1000 ms` | `start_splash.hta` floors; cap ≤ 98; `Int()` display; computed bound | `test_DI_019_H` | VERIFIED |
| UN-019 | | DI-019-I | Athena title `.name` font-size is 101px in both splash files | `start_splash.hta` `font-size:101px`; `electron/main.js` clamp(61px,7vw,101px) | `test_DI_019_I` | VERIFIED |
| UN-019 | | DI-019-J | `#dots` cycles `.` / `..` / `...` via VBScript `TickDots` at ≤ 500 ms/state; hidden on done | `start_splash.hta` `TickDots` sub; `setInterval("TickDots", N)` N ≤ 500; `dotsEl.style.display = "none"` | `test_DI_019_J` | VERIFIED |
| UN-019 | | DI-019-K | `$modelTimeout` polling loop absent from `start_athena.ps1`; voice models load async after Chrome open | `start_athena.ps1` | `test_DI_019_K` | VERIFIED |
| UN-019 | | DI-019-L | Chrome opens only after `CloseSplash` sub writes `.athena_splash_done`; `start_athena.ps1` polls before Chrome launch; no fixed 2500ms sleep | `start_splash.hta` `CloseSplash` sub; `start_athena.ps1` poll loop | `test_DI_019_L` | VERIFIED |
| UN-020 | Document review & approval | DI-020-A | All reviewable agents call submit_for_review() | `agents/` source grep for `submit_for_review` | `test_DI_020_A` | VERIFIED |
| UN-020 | | DI-020-B | Review queue GET fetch sends authHdr() | `ReviewView.jsx` `load()` contains `authHdr()` | `test_DI_020_B` | VERIFIED |
| UN-020 | | DI-020-C | Review history GET fetch sends authHdr() | `ReviewView.jsx` `loadHistory()` contains `authHdr()` | `test_DI_020_C` | VERIFIED |
| UN-020 | | DI-020-D | Queue auto-refreshes on agent_done WebSocket event | `ReviewView.jsx` `useEffect` on `reviewRefreshToken` | `test_DI_020_D` | VERIFIED |
| UN-020 | | DI-020-E | Document content viewable inline via ReviewViewer | `ReviewView.jsx` `ReviewViewer` fetches content inline | `test_DI_020_E` | VERIFIED |
| UN-021 | Single-instance enforcement | DI-021-A | Second Athena launch blocked by port/Chrome-PID check + dialog or clean stop-before-restart | `athena_lib.ps1` `Test-AthenaRunning` + `start_athena.ps1` guard block | `test_DI_021_A` | VERIFIED |
| UN-031 | Browser tab singleton | DI-031-A | Second Athena tab shows blocking overlay; React not mounted | `tabGuard.js` BroadcastChannel + localStorage; `main.jsx` conditional render | `test_DI_031_A` | VERIFIED |
| UN-031 | | DI-031-B | Tab lock released on close via beforeunload + release message | `tabGuard.js` beforeunload + ch.postMessage release | `test_DI_031_B` | VERIFIED |
| UN-024 | SOW agent (Phase 2C) | DI-024-A | SOW agent: Gate 10 review submission + Gate 3 confidence score | `agents/sow_agent.py` | `test_DI_024_A` | VERIFIED |
| UN-025 | Regulatory strategy (Phase 2C) | DI-025-A | Regulatory strategy agent: Gate 10 + Gate 3 confidence | `agents/regulatory_strategy_agent.py` | `test_DI_025_A` | VERIFIED |
| UN-026 | App startup loading (Phase 2C) | DI-026-A | React loading overlay with animated bar until WS connects | `App.jsx` `startupDone` state | `test_DI_026_A` | VERIFIED |
| UN-027 | Documents hub approval gate | DI-027-A | Documents hub shows only Gate 10-approved files | `server.py` `list_documents()` | `test_DI_027_A` | VERIFIED |
| UN-028 | Voice/noise discrimination | DI-028-A | `_vad_query` aggressiveness ≥ 2 | `voice_bridge.py` `_vad_query` init | `test_DI_028_A` | VERIFIED |
| UN-028 | | DI-028-B | Post-speech silence on VAD alone (no RMS gate) | `voice_bridge.py` `_record_query` post-speech branch | `test_DI_028_B` | VERIFIED |
| UN-028 | | DI-028-C | Greeting via `_voice_queue`, not direct TTS | `server.py` `_speak_phrase_greeting` | `test_DI_028_C` | VERIFIED |
| UN-028 | | DI-028-D | Voice loop sleep ≥ 0.5 s before first drain | `voice_bridge.py` `_voice_loop` startup pause | `test_DI_028_D` | VERIFIED |
| UN-029 | Audio device detection | DI-029-A | Device monitor polls ≤ 5 s | `voice_bridge.py` `_device_monitor_loop` | `test_DI_029_A` | VERIFIED |
| UN-029 | | DI-029-B | `_device_changed` Event + `_listen_for_wake` break on device change | `voice_bridge.py` `_device_changed`, `_listen_for_wake` | `test_DI_029_B` | VERIFIED |
| UN-029 | | DI-029-C | `device_changed` WebSocket event emitted | `voice_bridge.py` `_device_monitor_loop` | `test_DI_029_C` | VERIFIED |
| UN-030 | McKinsey/Latitude brand formatting | DI-030-A | All 6 `_DECK_GUIDES` entries include exec_summary | `agents/deck_agent.py` `_DECK_GUIDES` all 6 types | `test_DI_030_A` | VERIFIED |
| UN-030 | | DI-030-B | McKinsey/Big-4/pyramid quality directive in all 6 deliverable agents | `content_agent.py`, `briefing_agent.py`, `ma_intelligence_agent.py`, `regulatory_strategy_agent.py`, `sow_agent.py`, `deck_agent.py` | `test_DI_030_B` | VERIFIED |
| UN-030 | | DI-030-C | Latitude MedTech LLC brand identity injected via agent_base.py | `agents/agent_base.py` system prompt construction | `test_DI_030_C` | VERIFIED |
| UN-030 | | DI-030-D | `PUBLICATION_FORMAT_GUIDE` dict in `agent_base.py`; injected via `system_prompt()` | `agents/agent_base.py` `PUBLICATION_FORMAT_GUIDE` + `system_prompt()` | `test_DI_030_D` | VERIFIED |
| UN-030 | | DI-030-E | All 8 persona files contain `## Output Format Standard` section | `.claude/agents/*.md` — 8 files | `test_DI_030_E` | VERIFIED |
| UN-032 | Consulting learning visibility | DI-032-A | consulting_agent.py learn() generates "## Newly Ingested Items" report and calls submit_for_review() | `agents/consulting_agent.py` `learn()` + `submit_for_review(` | `test_DI_032_A` | VERIFIED |
| UN-032 | | DI-032-B | Report written to `consulting_learning_<ts>.md`; "No new items ingested this run." fallback present | `agents/consulting_agent.py` path pattern + fallback string | `test_DI_032_B` | VERIFIED |
| UN-033 | Voice query readiness latency | DI-033-A | `_listen_for_wake` accepts `stream` param; no internal `sd.InputStream` | `voice/voice_bridge.py` `_listen_for_wake(oww_model, stream)` | `test_DI_033_A` | VERIFIED |
| UN-033 | | DI-033-B | `_record_query` accepts `stream` param; no internal `sd.InputStream` | `voice/voice_bridge.py` `_record_query(stream)` | `test_DI_033_B` | VERIFIED |
| UN-033 | | DI-033-C | `_voice_loop` opens one stream; passes to `_listen_for_wake` and `_record_query` | `voice/voice_bridge.py` `_voice_loop` shared `sd.InputStream` | `test_DI_033_C` | VERIFIED |
| UN-034 | Engineering process integrity | DI-034-A | CLAUDE.md contains co-commit rule | `CLAUDE.md` Engineering Integrity Standards | `test_DI_034_A` | VERIFIED |
| UN-034 | | DI-034-B | CLAUDE.md contains Auth Centralization Standard | `CLAUDE.md` Engineering Integrity Standards | `test_DI_034_B` | VERIFIED |
| UN-034 | | DI-034-C | CLAUDE.md contains voice_bridge.py Boundary | `CLAUDE.md` Engineering Integrity Standards | `test_DI_034_C` | VERIFIED |
| UN-034 | | DI-034-D | CLAUDE.md contains Progress Bar Specification | `CLAUDE.md` Engineering Integrity Standards | `test_DI_034_D` | VERIFIED |
| UN-034 | | DI-034-E | CLAUDE.md contains App.jsx Responsibility Scope | `CLAUDE.md` Engineering Integrity Standards | `test_DI_034_E` | VERIFIED |
| UN-034 | | DI-034-F | CLAUDE.md contains CLAUDE.md Update Policy | `CLAUDE.md` Engineering Integrity Standards | `test_DI_034_F` | VERIFIED |
| UN-035 | Voice widget docking persistence | DI-035-A | Docked bar JSX style includes `width: "auto"` and `right: 0` | `App.jsx` `FloatingVoiceWidget` docked bar style | `test_DI_035_A` | VERIFIED |
| UN-036 | Agent tab approval gate | DI-036-A | AGENT_TAB maps 6 agent IDs to "queue" | `App.jsx` `AGENT_TAB` constant | `test_DI_036_A` | VERIFIED |
| UN-036 | | DI-036-B | list_briefings() and list_drafts() gate on approved status | `server.py` `list_briefings` + `list_drafts` | `test_DI_036_B` | VERIFIED |
| UN-036 | | DI-036-C | list_briefs() and list_marketing_outputs() gate on approved status | `server.py` `list_briefs` + `list_marketing_outputs` | `test_DI_036_C` | VERIFIED |
| UN-036 | | DI-036-D | list_decks() gates on approved status | `server.py` `list_decks` | `test_DI_036_D` | VERIFIED |
| UN-036 | | DI-036-E | list_iso_lessons() gates on approved status | `server.py` `list_iso_lessons` | `test_DI_036_E` | VERIFIED |

---

## Coverage Summary (v3.4 — CO-018)

| Metric | Count |
|---|---|
| Total user needs | 36 |
| Total design inputs | 129 |
| Design inputs with VERIFIED tests | 126 |
| Design inputs with PARTIAL coverage | 3 |
| Design inputs with OPEN gap | 0 |
| Design inputs with WAIVED status | 0 |

**PARTIAL items** require manual live-stack verification; static automated
tests pass for all three. See DC-005 for manual test procedures (MTP-001
through MTP-003). See `DC-005_manual_verification_protocol.md` for the
step-by-step protocol Steven executes against the running system.

---

## Open Traceability Gaps

Items with OPEN or PARTIAL status that are tracked as formal findings:

| Finding ID | DI | Gap Description | Owner | Target |
|---|---|---|---|---|
| TG-002 | DI-004-C | Latency test (first audio ≤ 2s) requires running voice stack; manual only — see MTP-001 | Steven | Phase 3 |
| TG-003 | DI-007-A | CLOSED — `test_DI_007_A` added (CO-018); system prompt word-count instruction verified | — | CLOSED |
| TG-004 | DI-008-A | CLOSED — `test_DI_008_A` added (CO-018); seed count ≥ 20 verified statically | — | CLOSED |
| TG-005 | DI-008-B | CLOSED — `test_DI_008_B` added (CO-018); no paid channel types in seed | — | CLOSED |
| TG-006 | DI-009-A | Deck section completeness requires PPTX inspection; manual only — see MTP-002 | Steven | Phase 3 |
| TG-007 | DI-010-C | CLOSED — iso.org removed from Tavily include_domains (CO-018); `test_DI_010_C` passes | — | CLOSED |
| TG-008 | DI-015-F | CLOSED — `test_DI_015_F` added (CO-018); AuthMiddleware blanket coverage confirmed | — | CLOSED |
| TG-014 | DI-022-A | Latency ≤ 1.75 s — static test passes; live timing requires running voice stack — see MTP-003 | Steven | Phase 3 |
| TG-009 | DI-030-A/B/C | CLOSED — DI-030-A/B/C promoted to VERIFIED by CO-010/CO-011 (DI-030-D/E publication format + DI-034 engineering integrity) | — | CLOSED |
| TG-010 | DI-007-G | CLOSED — DEVICE_SUBSECTORS all-6-sector coverage verified by CO-017 (dc_verify 122/122) | — | CLOSED |
| TG-011 | DI-007-H | CLOSED — Content agent tm_yday fallback verified by CO-017 | — | CLOSED |
| TG-012 | DI-008-C | CLOSED — MarketingView bulk delete BulkBar pattern verified by CO-017 | — | CLOSED |
| TG-013 | DI-011-C | CLOSED — M&A agent historical scope statement verified by CO-017 | — | CLOSED |
| TG-014 | DI-022-A | Latency ≤ 1.75 s — static check on DC-002 text; live timing requires running voice stack (manual, Phase 3) | Steven | Phase 3 |
| TG-015 | DI-035-A | CLOSED — Voice docked bar width:auto and right:0 verified by CO-017 (test strengthened to check both properties) | — | CLOSED |
| TG-016 | DI-036-A | CLOSED — AGENT_TAB queue routing verified by CO-017 | — | CLOSED |
| TG-017 | DI-036-B | CLOSED — list_briefings/list_drafts approval gate verified by CO-017 | — | CLOSED |
| TG-018 | DI-036-C | CLOSED — list_briefs/list_marketing_outputs approval gate verified by CO-017 | — | CLOSED |
