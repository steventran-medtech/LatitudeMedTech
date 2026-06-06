# DC-004 — Requirements Traceability Matrix (RTM)
**Document:** DC-004 · Version 1.6 · 2026-06-05  
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
| UN-002 | | DI-002-E | Rejected items not in Docs hub | `server.py` document filtering | `test_DI_002_E` | PARTIAL |
| UN-003 | Knowledge base | DI-003-A | KBQuery searchable by agents | `kb_query.py` KBQuery | `test_DI_003_A` | VERIFIED |
| UN-003 | | DI-003-B | RAG indexes FDA/EU/IMDRF | `knowledge_base/` subdirs | `test_DI_003_B` | VERIFIED |
| UN-004 | Voice interaction | DI-004-A | Wake threshold ≤ 0.35 | `voice_bridge.py` WAKE_THRESHOLD | `test_DI_004_A` | VERIFIED |
| UN-004 | | DI-004-B | Whisper STT + confidence log | `voice_bridge.py` whisper | `test_DI_004_B` | VERIFIED |
| UN-004 | | DI-004-C | First audio ≤ 2s | Kokoro streaming pipeline | `test_DI_004_C` | PARTIAL |
| UN-004 | | DI-004-D | Intent routing via tool_use | `voice_bridge.py` dispatch | `test_DI_004_D` | VERIFIED |
| UN-004 | | DI-004-E | SILENCE_DURATION = 0.8s (C3 change — responsiveness) | `voice_bridge.py` constant + `settings.json` | `test_DI_004_E` | VERIFIED |
| UN-005 | Task notifications | DI-005-A | Notify endpoint exists | `server.py` POST /api/voice/notify | `test_DI_005_A` | VERIFIED |
| UN-005 | | DI-005-B | Notification only if voice active | `voice_bridge.py` queue guard | `test_DI_005_B` | VERIFIED |
| UN-006 | Persistent voice session | DI-006-A | Session persists across tabs | `useVoiceSession.js` app-level | `test_DI_006_A` | VERIFIED |
| UN-006 | | DI-006-B | Status badge in header | `App.jsx` VoiceStatusBadge | `test_DI_006_B` | VERIFIED |
| UN-022 | Voice conversation quality | DI-022-A | Latency between end of user voice input and start of audible response <= 2 s; streaming sentence-split pipeline ensures first sentence dispatched to TTS before full response is buffered | `voice_bridge.py` `_ask_claude_streaming` + `_SENTENCE_END` sentence-split + `_speak_sentence` called inside token-stream loop | `test_DI_022_A` | PARTIAL |
| UN-007 | Content generation | DI-007-A | 900–1,200 word articles | `content_agent.py` max_tokens | `test_DI_007_A` | PARTIAL |
| UN-007 | | DI-007-B | Title from body H1 | `content_agent.py` title_from_body | `test_DI_007_B` | VERIFIED |
| UN-007 | | DI-007-C | Banned phrases enforced | `content_agent.py` system prompt | `test_DI_007_C` | VERIFIED |
| UN-007 | | DI-007-D | Non-Latin chars stripped | `content_agent.py` clean_title | `test_DI_007_D` | VERIFIED |
| UN-007 | | DI-007-E | YAML frontmatter stripped in UI | `App.jsx` renderInline | `test_DI_007_E` | VERIFIED |
| UN-008 | Marketing pipeline | DI-008-A | Pipeline DB ≥ 20 targets | `marketing_agent.py` pipeline.db | `test_DI_008_A` | PARTIAL |
| UN-008 | | DI-008-B | Zero-cash channels only | `marketing_agent.py` seed data | `test_DI_008_B` | PARTIAL |
| UN-009 | Slide deck generation | DI-009-A | Deck with required sections | `deck_agent.py` slide sequence | `test_DI_009_A` | PARTIAL |
| UN-009 | | DI-009-B | Latitude brand palette | `deck_agent.py` colour constants | `test_DI_009_B` | VERIFIED |
| UN-009 | | DI-009-C | DeckView gallery + download | `server.py` deck routes | `test_DI_009_C` | VERIFIED |
| UN-010 | ISO 13485 coach | DI-010-A | Any clause on demand | `iso_coach_agent.py` clause lookup | `test_DI_010_A` | VERIFIED |
| UN-010 | | DI-010-B | One clause at a time; no --all from UI | `iso_coach_agent.py` sequential logic | `test_DI_010_B` | VERIFIED |
| UN-010 | | DI-010-C | No verbatim ISO text in RAG | `rag_agent.py` exclusion | `test_DI_010_C` | PARTIAL |
| UN-011 | M&A intelligence | DI-011-A | QARA frameworks in analysis | `ma_intelligence_agent.py` | `test_DI_011_A` | VERIFIED |
| UN-011 | | DI-011-B | Cited sources + dates | M&A agent system prompt | `test_DI_011_B` | VERIFIED |
| UN-012 | Regulatory briefings | DI-012-A | FDA + EU MDR + IMDRF coverage | `briefing_agent.py` sources | `test_DI_012_A` | VERIFIED |
| UN-012 | | DI-012-B | Briefings enter review queue | `briefing_agent.py` submit_for_review | `test_DI_012_B` | VERIFIED |
| UN-023 | Historical data depth | DI-023-A | No date cutoff blocking >50-year-old sources; KB queries include historically-scoped terms | `rag_agent.py` no hard year filter; seed queries include non-date-restricted terms | `test_DI_023_A` | OPEN |
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
| UN-015 | | DI-015-F | Session auth on all routes | `server.py` auth dependency | `test_DI_015_F` | PARTIAL |
| UN-016 | Output labeling | DI-016-A | Disclaimer on all outputs | `orchestrator.py` DISCLAIMER | `test_DI_016_A` | VERIFIED |
| UN-016 | | DI-016-B | Readiness label on all outputs | `orchestrator.py` LABEL | `test_DI_016_B` | VERIFIED |
| UN-016 | | DI-016-C | Label is permitted value | `orchestrator.py` label value | `test_DI_016_C` | VERIFIED |
| UN-017 | Audit log | DI-017-A | Voice sessions logged | `voice/sessions.jsonl` | `test_DI_017_A` | VERIFIED |
| UN-017 | | DI-017-B | Athena sessions logged | `ui/logs/athena_sessions.jsonl` pattern | `test_DI_017_B` | VERIFIED |
| UN-017 | | DI-017-C | Review items retrievable by ID | `server.py` GET /api/review/{id} | `test_DI_017_C` | VERIFIED |
| UN-018 | Client lifecycle | DI-018-A | Client creation returns ID; db errors return 500 JSON | `server.py` create_client | `test_DI_018_A` | VERIFIED |
| UN-018 | | DI-018-B | Intake form required-field validation (name, email, tier) | `ClientsView.jsx` IntakeForm | `test_DI_018_B` | VERIFIED |
| UN-019 | Startup experience | DI-019-A | Progress bar absolutely positioned full-width at bottom | `start_splash.hta` `.bar-wrap` CSS | `test_DI_019_A` | VERIFIED |
| UN-019 | | DI-019-B | No numeric percentage text during loading | `start_splash.hta` — no `#pct` element or `pctEl.innerText` | `test_DI_019_B` | VERIFIED |
| UN-019 | | DI-019-C | Bar advances through real loading stages; reaches 100% only on `.athena_ready`; splash closes only after bar visually completes | `start_splash.hta` `PollChromeReady` + `readyToClose` + `stepVal >= 100` gate | `test_DI_019_C` | VERIFIED |
| UN-020 | Document review & approval | DI-020-A | All reviewable agents call submit_for_review() | `agents/` source grep for `submit_for_review` | `test_DI_020_A` | VERIFIED |
| UN-020 | | DI-020-B | Review queue GET fetch sends authHdr() | `ReviewView.jsx` `load()` contains `authHdr()` | `test_DI_020_B` | VERIFIED |
| UN-020 | | DI-020-C | Review history GET fetch sends authHdr() | `ReviewView.jsx` `loadHistory()` contains `authHdr()` | `test_DI_020_C` | VERIFIED |
| UN-020 | | DI-020-D | Queue auto-refreshes on agent_done WebSocket event | `ReviewView.jsx` `useEffect` on `reviewRefreshToken` | `test_DI_020_D` | VERIFIED |
| UN-020 | | DI-020-E | Document content viewable inline via ReviewViewer | `ReviewView.jsx` `ReviewViewer` fetches content inline | `test_DI_020_E` | VERIFIED |
| UN-021 | Single-instance enforcement | DI-021-A | Second Athena launch blocked by port/Chrome-PID check + dialog or clean stop-before-restart | `athena_lib.ps1` `Test-AthenaRunning` + `start_athena.ps1` guard block | `test_DI_021_A` | VERIFIED |

---

## Coverage Summary (v1.5)

| Metric | Count |
|---|---|
| Total user needs | 23 |
| Total design inputs | 70 |
| Design inputs with VERIFIED tests | 60 |
| Design inputs with PARTIAL coverage | 9 |
| Design inputs with OPEN gap | 1 |
| Design inputs with WAIVED status | 0 |

**PARTIAL items** require manual verification currently; automated tests are
pending. See DC-005 for the verification procedures for PARTIAL items.

---

## Open Traceability Gaps

Items with OPEN or PARTIAL status that are tracked as formal findings:

| Finding ID | DI | Gap Description | Owner | Target |
|---|---|---|---|---|
| TG-001 | DI-002-E | Automated test for rejected items excluded from Documents hub not yet written | Steven | Phase 2C |
| TG-002 | DI-004-C | Latency test (first audio ≤ 2s) requires running voice stack; manual-only | Steven | Phase 2C |
| TG-003 | DI-007-A | Word count validation not enforced in post-processing code path | Steven | Phase 2C |
| TG-004 | DI-008-A | Automated count of pipeline.db seed targets not yet in dc_verify.py | Steven | Phase 2C |
| TG-005 | DI-008-B | Channel type validation against paid-media exclusion list not automated | Steven | Phase 2C |
| TG-006 | DI-009-A | Deck section completeness check requires PPTX inspection; manual-only | Steven | Phase 2C |
| TG-007 | DI-010-C | No automated check that ISO standard files are excluded from RAG ingestion | Steven | Phase 2C |
| TG-008 | DI-015-F | Session auth guard is present but coverage of all non-health routes not automated | Steven | Phase 2C |
