# DC-003 — Design Outputs
**Document:** DC-003 · Version 1.0 · 2026-06-05  
**Approved by:** Steven Tran

Design outputs are the code artifacts, APIs, data structures, and
configuration files that implement the design inputs in DC-002. Each entry
maps one or more DIs to the specific file(s) and symbols that fulfill them.

---

## Layer Overview

```
Athena/
├── agents/           ← Python agent logic (LLM calls, KB queries, output generation)
├── ui/
│   ├── backend/
│   │   └── server.py ← FastAPI — all API routes, WebSocket, middleware
│   └── frontend/src/ ← React UI — views, hooks, rendering
├── voice/            ← Whisper STT, Kokoro TTS, wake word detection
└── memory/           ← SQLite DBs (checkpoints, agent memory, review queue)
```

---

## DO-001 — Coaching Brief Generation

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Coaching brief LangGraph workflow | `agents/orchestrator.py` | `CoachingState`, `intake()`, `generate_brief()`, `finalize()` | DI-001-A, DI-001-B, DI-001-C, DI-001-D |
| Human-gate interrupt | `agents/orchestrator.py` | `human_review()` — `interrupt()` call | DI-002-A |
| Brief parsing + generation | `agents/coaching_brief.py` | `parse_input()`, `generate_brief()`, `brief_title()` | DI-001-A |
| Disclaimer constant | `agents/orchestrator.py` | `DISCLAIMER`, `LABEL` | DI-001-C, DI-001-D, DI-016-A, DI-016-B |
| Brief API route | `ui/backend/server.py` | `POST /api/agents/briefing` | DI-001-A |
| Coaching brief list | `ui/backend/server.py` | `GET /api/coaching/briefs` | DI-001-B |

---

## DO-002 — Human Review Gate

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Review queue DB | `agents/memory.py` | `Memory.add_review_item()`, `Memory.get_pending_review()` | DI-002-A |
| Approve endpoint | `ui/backend/server.py` | `POST /api/review/{item_id}/approve` | DI-002-B |
| Reject endpoint | `ui/backend/server.py` | `POST /api/review/{item_id}/reject` | DI-002-C |
| Edit-and-rewrite endpoint | `ui/backend/server.py` | `POST /api/review/{item_id}/edit` | DI-002-D |
| Review UI | `ui/frontend/src/ReviewView.jsx` | Full component | DI-002-A through DI-002-D |
| Submit for review helper | `agents/briefing_agent.py`, `agents/marketing_agent.py` | `submit_for_review()` calls | DI-002-A, DI-012-B |

---

## DO-003 — Knowledge Base

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| KB query interface | `agents/kb_query.py` | `KBQuery`, `KBQuery.search()` | DI-003-A |
| RAG ingestion agent | `agents/rag_agent.py` | `RagAgent`, `learn()` | DI-003-B |
| Central KB helper | `agents/agent_base.py` | `AgentBase.central_kb_context()` | DI-003-A |
| KB directory | `Athena/knowledge_base/` | Subdirs: `FDA/`, `EU_MDR/`, `IMDRF/`, `consulting/`, `ma/`, `General/` | DI-003-B |

---

## DO-004 — Voice Interface

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Voice bridge (wake + STT + TTS) | `voice/voice_bridge.py` | `VoiceBridge`, `WAKE_THRESHOLD`, `SILENCE_DURATION`, `_listen_loop()` | DI-004-A through DI-004-E |
| Wake word model | `voice/wake/hi_athena.onnx` (or "alexa" fallback) | openwakeword model | DI-004-A |
| Whisper STT | `voice/voice_bridge.py` | `whisper.load_model("tiny.en")` | DI-004-B |
| Kokoro TTS server | `voice/kokoro_server.py`, port 8002 | Sentence-split streaming pipeline | DI-004-C |
| Intent classification + dispatch | `voice/voice_bridge.py` | Claude Haiku `tool_use` in `_classify_and_dispatch()` | DI-004-D |
| Voice API | `ui/backend/server.py` | `WebSocket /ws/voice`, `POST /api/voice/query` | DI-004-A through DI-004-D |

---

## DO-005 — Task Notifications

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Notification queue | `voice/voice_bridge.py` | `_notification_queue`, drained in listening loop | DI-005-A, DI-005-B |
| Notify endpoint | `ui/backend/server.py` | `POST /api/voice/notify` | DI-005-A |
| WS agent events | `ui/backend/server.py` | `agent_start` / `agent_log` / `agent_done` WebSocket broadcast | DI-005-A |

---

## DO-006 — Persistent Voice Session

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| App-level voice hook | `ui/frontend/src/useVoiceSession.js` | Hook lifted to `App.jsx` | DI-006-A |
| Voice status header badge | `ui/frontend/src/App.jsx` | `VoiceStatusBadge` component in header | DI-006-B |
| Floating voice widget | `ui/frontend/src/VoiceView.jsx` | Persistent widget accessible from all tabs | DI-006-A, DI-006-B |

---

## DO-007 — Content Generation

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Content agent | `agents/content_agent.py` | `ContentAgent`, `generate()`, `title_from_body()`, `clean_title()` | DI-007-A through DI-007-D |
| Banned phrase enforcement | `agents/content_agent.py` | Banned phrase list in system prompt | DI-007-C |
| YAML frontmatter stripper | `ui/frontend/src/App.jsx` | `renderInline()` / `MarkdownView` | DI-007-E |
| Content API route | `ui/backend/server.py` | `POST /api/agents/content` | DI-007-A |
| Drafts storage | `Athena/content/drafts/` | Markdown files | DI-007-A |

---

## DO-008 — Marketing Pipeline

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Marketing agent | `agents/marketing_agent.py` | `MarketingAgent`, pipeline DB lazy-created | DI-008-A, DI-008-B |
| Pipeline database | `Athena/ops/marketing/pipeline.db` | SQLite, lazy-created on first run | DI-008-A |
| Marketing UI | `ui/frontend/src/MarketingView.jsx` | Full component | DI-008-A |
| Marketing API | `ui/backend/server.py` | `POST /api/agents/marketing` | DI-008-A |

---

## DO-009 — Slide Deck Generation

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Deck agent | `agents/deck_agent.py` | `DeckAgent`, slide construction sequence | DI-009-A |
| Brand palette constants | `agents/deck_agent.py` | `LM_BLACK`, `LM_SLATE`, `LM_BLUE` | DI-009-B |
| Deck gallery UI | `ui/frontend/src/DeckView.jsx` | Gallery + preview + download | DI-009-C |
| Deck API routes | `ui/backend/server.py` | `GET /api/documents/decks`, `POST /api/agents/deck` | DI-009-C |
| Deck output directory | `Athena/documents/decks/` | PPTX files | DI-009-A |

---

## DO-010 — ISO 13485 Coach

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| ISO coach agent | `agents/iso_coach_agent.py` | `ISOCoachAgent`, clause lookup | DI-010-A, DI-010-B |
| ISO coach UI | `ui/frontend/src/ISOView.jsx` | Clause selector, rendering | DI-010-A, DI-010-B |
| ISO coach API | `ui/backend/server.py` | `POST /api/agents/iso-coach` | DI-010-A |
| RAG exclusion rule | `agents/rag_agent.py` | ISO standard files excluded from ingestion | DI-010-C |

---

## DO-011 — M&A Intelligence

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| M&A agent | `agents/ma_intelligence_agent.py` | `MAIntelligenceAgent`, QARA frameworks | DI-011-A, DI-011-B |
| M&A knowledge base | `Athena/knowledge_base/ma/` | Deal intelligence documents | DI-011-A |
| M&A agent definition | `.claude/agents/ma-intelligence-agent.md` | QARA diligence frameworks | DI-011-A |
| M&A API | `ui/backend/server.py` | `POST /api/agents/ma` | DI-011-A |

---

## DO-012 — Regulatory Briefings

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Briefing agent | `agents/briefing_agent.py` | `BriefingAgent`, multi-framework sources | DI-012-A, DI-012-B |
| Briefing storage | `Athena/briefings/` | Markdown brief files | DI-012-A |
| Briefing API | `ui/backend/server.py` | `GET /api/briefings`, `POST /api/agents/briefing` | DI-012-A |

---

## DO-013 — Dashboard

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Dashboard data | `agents/dashboard.py` | `Dashboard`, health status per agent | DI-013-A |
| Dashboard API | `ui/backend/server.py` | `GET /api/dashboard`, `GET /api/dashboard/timeseries`, `GET /api/dashboard/knowledge-growth` | DI-013-A through DI-013-C |
| Dashboard UI | `ui/frontend/src/App.jsx` | Dashboard tab with charts and health cards | DI-013-A through DI-013-C |

---

## DO-014 — Learning & Skills

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Agent learning runner | `agents/agent_learning.py` | `learn()`, `stamp_last_learning()` | DI-014-A |
| Learning sources | `agents/learning_sources.py` | RSS + scrape feed definitions per agent | DI-014-A |
| Skills profile generator | `agents/skills_profile.py` | Per-agent profile + master SKILLS.md | DI-014-B |
| Skills API | `ui/backend/server.py` | `POST /api/agents/skills-profile`, `POST /api/agents/learn` | DI-014-B |
| Skills output | `Athena/knowledge_base/skills/<agent>.md`, `SKILLS.md` | Generated profile files | DI-014-B |

---

## DO-015 — Security Controls

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Secret exclusion | `voice/.env` (local-only), `.gitignore` | All secret keys in .env; .gitignore excludes it | DI-015-A |
| Shell=False enforcement | All `agents/*.py`, `ui/backend/server.py` | `subprocess.run(..., shell=False)` everywhere | DI-015-B |
| Rate limiting middleware | `ui/backend/server.py` | SlowAPI or custom middleware at 120 req/min | DI-015-C |
| Security headers | `ui/backend/server.py` | CSP, X-Frame-Options, X-Content-Type-Options | DI-015-D |
| Path traversal protection | `ui/backend/server.py` | Path normalization + allowlist in file routes | DI-015-E |
| Session authentication | `ui/backend/server.py` | `.athena.key` token validation | DI-015-F |

---

## DO-016 — Output Labels & Disclaimer

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Canonical disclaimer | `agents/orchestrator.py` | `DISCLAIMER` string constant | DI-016-A |
| Canonical label | `agents/orchestrator.py` | `LABEL = "Alpha — Steve Review Required"` | DI-016-B |
| Label application at finalize | `agents/orchestrator.py` | `finalize()` node appends disclaimer + label | DI-016-A, DI-016-B |
| Permitted label values | `agents/orchestrator.py`, `compliance.md` | Demo / Alpha / Beta / Production | DI-016-C |

---

## DO-017 — Audit Logs

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Voice session log | `Athena/voice/sessions.jsonl` | Written by `voice_bridge.py` per session | DI-017-A |
| Athena session log | `Athena/ui/logs/athena_sessions.jsonl` | Written by `stop_athena.ps1` on shutdown | DI-017-B |
| Review item retrieval | `ui/backend/server.py` | `GET /api/review/{item_id}` | DI-017-C |

---

## DO-018 — Client Lifecycle

| Design Output | File | Symbol / Route | Implements |
|---|---|---|---|
| Client CRUD API | `ui/backend/server.py` | `POST /api/clients` with try/except + error JSON | DI-018-A |
| Client DB methods | `agents/memory.py` | `Memory.add_client()`, `Memory.get_clients()`, `Memory.update_client()`, `Memory.delete_client()` | DI-018-A |
| Client intake form | `ui/frontend/src/ClientsView.jsx` | `IntakeForm` — required-field validation for `name`, `email`, `program_tier`; per-field red-border + inline error | DI-018-B |
| Engagement API | `ui/backend/server.py` | `GET/POST /api/clients/{id}/engagements`, `PUT /api/engagements/{id}` | DI-018-A |
