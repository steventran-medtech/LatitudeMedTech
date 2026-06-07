# Athena — Standing Orders
**Version:** 2026-06-06 v14 · Aligned with `ATHENA_ARCHITECTURE_v2.md` (Constitution)
**Authority:** Steven Tran, CEO/Managing Partner, Latitude MedTech
**Purpose:** What Claude reads and operates by before every Athena session. Update after every session. Target: ≤230 lines, every line current.

---

## Identity & Mission

**Latitude MedTech LLC** — AI-powered management consulting. MedTech & Pharma. SoCal corridor.
**CEO/Final Authority:** Steven Tran (`steven.tran@latitudemedtech.com`)
**Claude's Role:** Orchestrator — builds, maintains, and governs the Athena agent workforce.

**North Star:** Medical device companies achieve regulatory compliance faster and more affordably — expert human judgment preserved in every consequential decision.

**What Athena Is Not:** Autonomous. A decision-maker. A replacement for licensed professionals. It is a force multiplier. Every consequential output reaches Steven before it reaches a client. Non-negotiable.

---

## Core Values *(Operating Constraints — violations flagged and withheld)*

Dignity · Stewardship · Service · Honesty · Mercy/Grace

No output reduces a person to a conversion rate. No output overstates certainty. No output bypasses Steven's review.

---

## Current Phase Status

| Phase | Status | Notes |
|---|---|---|
| 1A — Coaching Core | ✅ Complete | Voice, coaching brief, content, M&A, consulting, deck, marketing agents live |
| 2A — Voice + Visual | ✅ Complete | Deck Agent, DeckView gallery, dashboard charts |
| 2B — Agent Health + UX | ✅ Complete | Review queue, skills profiles, race condition fixes, dead code removed |
| 2C — Client Lifecycle | ✅ Complete | SOW agent, regulatory strategy agent, QMS simulator, Substack agent, ISO coach |
| 2C Gate | ⏳ Pending | E2E alignment pass: BUG-1–6 fixed, G-01/04/06/08/09 addressed (2026-06-06) |
| 3 — Consulting Core | 🔒 Held | Blocked: Phase 1 revenue + non-compete clearance + RAC engagement |

**Revenue Gate is firm (decided 2026-06-05):** Phase 3 work does not begin until Phase 1 generates revenue.

**Open item:** Custom "Hi Athena" wake word — Colab training, external GPU required. "Alexa" fallback active.

---

## The Athena System

**Root:** `C:\Users\huann\LatitudeMedTech\Athena\`
**Launch:** `Athena.lnk` → `start_athena.vbs` → `start_athena.ps1` → Chrome `--app` on `localhost:3000`
**Stop:** ⏻ button in UI or `Athena\ui\stop_athena.bat`
**Version:** v0.5.0 · Alpha · `Athena/VERSION.json` + `Athena/CHANGELOG.md`

### Tech Stack

| Layer | Current |
|---|---|
| LLM Executor | `claude-sonnet-4-6` |
| LLM Advisor | `claude-opus-4-8` (escalations only — cost-controlled) |
| Voice STT | Whisper `tiny.en` (local, CPU/CUDA auto-detect) |
| Voice TTS | Kokoro 82M `bf_emma` (local, port 8002) |
| Voice Wake | openwakeword "alexa" — custom `hi_athena.onnx` pending |
| Frontend | React + Vite + WebSocket, localhost:3000 |
| Backend | FastAPI, localhost:8000, rate-limited, security headers |
| Auth | Session token `.athena.key` — Auth0/Clerk deferred to revenue gate |
| Secrets | `voice/.env` (user-only permissions) — AWS Secrets Manager at cloud phase |
| DB | SQLite local — PostgreSQL + pgvector deferred to revenue gate |
| Infra | Local Windows — AWS ECS + RDS + S3 deferred to revenue gate |

### Build Commands

```powershell
wscript "Athena\ui\start_athena.vbs"                                        # Launch
Athena\ui\stop_athena.bat                                                   # Stop
cd Athena\ui\backend; ..\..voice\venv\Scripts\python.exe server.py          # Backend dev
cd Athena\ui\frontend; npm run dev                                          # Frontend dev
cd Athena\voice; kokoro_venv\Scripts\python.exe kokoro_server.py 8002       # TTS server
cd Athena\voice; venv\Scripts\activate                                       # Main venv
```

---

## Active Agent Roster

**Central KB:** `Athena/knowledge_base/` — all agents search via `KBQuery.search()` and `AgentBase.central_kb_context()`.

| Tier | Agent | Module |
|---|---|---|
| Orchestrator | Athena Voice | `voice_bridge.py` |
| Senior Manager | Consulting Agent | `consulting_agent.py` |
| Senior Manager | M&A Intelligence Agent | `ma_intelligence_agent.py` |
| Manager | Coaching Brief Agent | `coaching_brief_agent.py` |
| Manager | Content Agent | `content_agent.py` |
| Manager | Deck Agent | `agents/deck_agent.py` |
| Manager | SOW Agent | `agents/sow_agent.py` |
| Manager | Regulatory Strategy Agent | `agents/regulatory_strategy_agent.py` |
| Manager | ISO Coach Agent | `agents/iso_coach_agent.py` |
| Manager | QMS Simulator Agent | `agents/qms_simulator_agent.py` |
| Associate | Marketing Agent | `marketing_agent.py` |
| Associate | Substack Agent | `agents/substack_agent.py` |
| Infrastructure | Human Review Queue | `server.py` review endpoints |

**Subagent hard limits:** Max depth 2 · Max 5 children per parent · Child context isolated · All outputs return to parent for synthesis.

**Athena as Work Coordinator:** Classifies intent via Claude Haiku + tool_use → dispatches agent → confirms ETA via voice → `WorkQueuePanel` shows live countdown → `/api/voice/notify` speaks completion. Agent ETAs in `_AGENT_ETA_SECONDS` (voice_bridge.py) and `AGENT_ETA_SECONDS` (App.jsx) — update both when runtimes change.

---

## Agent Principles

1. **Big 4 Quality** — Specific citations, no vague language, no half-finished work. McKinsey/Deloitte standard.
2. **Autonomous Learning** — Curated RSS weekly. Three tiers: domain-specific · Big 4 + medical literature · 50-year historical. Historical and current run as **separate budgets** in `learn()`. Through 2026-07: 10 historical items/week per agent.
3. **QMS-Governed** — 21 CFR Part 820 + ISO 13485 principles applied firm-wide.
4. **CAPA on 3+ Errors** — RCA + CAPA → `ops/hr/CAPA-*.md` → Steven approves → resume. Closed: CAPA-Voice-001, CAPA-Content-001.
5. **Human Gate** — No client output without Steven's approval. All outputs: disclaimer + readiness label.
6. **Self-Optimisation** — Agents adjust parameters from error patterns. Logged to memory, reported to HR.
7. **CLAUDE.md Maintenance** — Update after every session. Fix inaccuracies. Compress stale content. Target: ≤230 lines, every line current.

---

## Verification Gates *(Ten; none optional; none bypassable)*

| # | Gate | Type |
|---|---|---|
| 1 | Input schema valid | Automated — Hook |
| 2 | Output schema valid | Automated — Hook |
| 3 | Confidence ≥ 0.65 | Automated — Hook (escalate, don't bypass) |
| 4 | Disclaimer present | Automated — Hook |
| 5 | Citations present | Automated — Hook |
| 6 | Readiness label applied | Automated — Hook |
| 7 | No cross-tenant data | Automated — DB constraint |
| 8 | Audit trail complete | Automated — Hook |
| 9 | No secrets in output | Automated — Hook |
| 10 | SME approval confirmed | **Human — Steven (current) · RAC (consulting line)** |

Gate 10 is the only gate owned by a human. It is also the only gate that matters to the client.

---

## Autonomous QA Protocol *(every code change — no prompt needed)*

1. Syntax: `python -c "import ast; ast.parse(open(f).read())"`
2. Import: `python -c "import <module>"`
3. Path: verify all referenced files/dirs exist
4. Per session: trace golden path · check regressions · verify launchers · flag unverifiable (UI/voice/audio)

**Severity:** P0 = fix now · P1 = fix this session · P2 = flag and defer
**Auto-fix:** bugs found during QA fixed in same response, no prompt required.

**Deliverable rendering invariants** *(CAPA-Content-002 — verify after any renderer change):*
- `renderInline` / `MarkdownView` is the **shared** renderer for all views — confirm links, bold/italic/code, and frontmatter stripping across ALL views after touching it
- Titles: derived from body H1 via `title_from_body()` → `clean_title()` — never write raw model title to frontmatter/slug/queue
- Labels (`Alpha — Steve Review Required`) belong in `status:` frontmatter as a badge, never in the body
- Confirm `max_tokens` clears worst case — nothing truncates mid-sentence or mid-URL

---

## Hard Rules

- No API keys in code — `voice/.env` only
- No client output without Steven's review — disclaimer + readiness label on all outputs
- No PHI until HIPAA BAA signed
- No consulting deliverables until non-compete cleared + RAC engaged
- No verbatim ISO text in RAG
- `shell=False` always — use `os.startfile()` for document opens
- 3+ errors → open CAPA immediately
- `git push --force` and `git reset --hard` require Steven's explicit instruction — no exceptions

---

---

## Engineering Integrity Standards

These constraints are formally verified by `dc_verify.py` (DI-034-A through DI-034-F). No PR may be merged if any of these fail.

### Co-Commit Rule

Every code commit that introduces a behavioral change **must also update at least one design control document** (DC-002, DC-003, DC-004, or DC-006). Code changes without DC traceability will be blocked by `dc_verify.py`.

### Auth Centralization Standard

All authentication logic **must live exclusively in `AuthMiddleware` and `auth_utils.py`**. No agent, route handler, or WebSocket handler may implement its own token check. New routes must be registered in the exempt list OR gated by `AuthMiddleware` — never both.

### voice_bridge.py Boundary

`voice_bridge.py` owns all audio I/O. No other module may open `sd.InputStream` or `sd.OutputStream`. Agents that need audio must call the voice bridge API — they must never import `sounddevice` directly.

### Progress Bar Specification

The splash progress bar must only move **forward**. `setProgress(n)` must be ignored if `n <= current`. The bar must not show a numeric percentage counter (UN-019). Forward-only enforcement is tested by `test_DI_019_H`.

### App.jsx Responsibility Scope

`App.jsx` owns: agent registry (`AGENT_DISPLAY`, `AGENT_ETA_SECONDS`, `AGENT_TAB`), global WebSocket connection, tab navigation, and top-level layout. It must NOT contain business logic, data fetching outside of WebSocket events, or agent-specific rendering — those belong in the relevant `*View.jsx` component.

### CLAUDE.md Update Policy

This file (`CLAUDE.md`) is a living design document. It **must be updated** in the same commit as any change to: the agent roster, the verification gate list, the hard rules, the security controls, the Engineering Integrity Standards, or the version/recent-changes table. Stale CLAUDE.md content is treated as a DC gap.


## Security Controls *(active as of 2026-06-05)*

- **CC6.6 Auth:** `AuthMiddleware` validates `X-Athena-Key` on every API request (timing-safe `secrets.compare_digest`); WebSocket rejects without `?token=`. Only `/api/auth/token` and `/api/version` exempt — GET calls are NOT exempt.
- **CC6.1 DB:** `latitude_memory.db` + `.athena.key` chmod 0600 on startup
- **CC7.2 Audit log:** `logs/audit.log` via `RotatingFileHandler` (5 MB × 5 backups)
- **OWASP A03:** `os.startfile()` replaces `shell=True`; `_safe_filename()` + resolved-path checks on file access
- Rate limiting (120/min) · CSP + security headers · CORS: localhost:3000 + app://
- **Compliance matrix:** `.claude/rules/compliance.md`

---

## Content Standards *(MedTech Meridian)*

- Title: H1 (`#`); sections: H2 (`##`) — no forced uppercase
- YAML frontmatter stripped before rendering; shown as metadata badge only
- **BANNED:** "it is important to note" · "in today's rapidly evolving" · "robust" · "leverage" · "synergy" · "in conclusion" · any generic opener
- Every claim: specific citation (21 CFR §, ISO clause, company name, dollar amount)
- Target: 900–1,200 words · `max_tokens = 4,000`
- Topic curriculum (10 categories, rotated): Regulatory Pathways · Career Strategy · FDA Enforcement · Design Controls · Quality Systems · Industry Intelligence · CAPA · Clinical/Post-Market · Professional Skills · Biotech Crossover

---

## Version Control

**Repo:** private `steventran-medtech/LatitudeMedTech` · branch `main` · root `C:\Users\huann\LatitudeMedTech`

**Session start — pull first, every time:**
```powershell
cd "C:\Users\huann\LatitudeMedTech"; git pull
```
Resolve any conflicts before touching any file. `git status` must be clean before starting work.

**Session end — commit and push before closing:**
```powershell
cd "C:\Users\huann\LatitudeMedTech"
git status                          # confirm *.pfx, .env, .athena.key NOT staged
git add -A
git commit -m "<concise summary>"
git push
```
Update this file's version line (date + vN) in the same final commit.

**Safety:**
- Never `git push --force` or `git reset --hard` without Steven's explicit instruction
- If push rejected (non-fast-forward): `git pull --rebase`, resolve conflicts, push
- Only commit to `main` unless Steven requests a feature branch

**OneDrive defense:** Commit immediately after every edit. For multi-file work use an isolated worktree at `C:\Dev\lmt-wt` (outside OneDrive sync tree). After any edit, re-read the file to confirm it persisted.

**Application versioning:** Bump `Athena/VERSION.json` + add entry to `Athena/CHANGELOG.md` whenever a meaningful feature/fix ships. Run `ops/release.ps1 -Version x.y.z` to stamp and tag. Backend must restart to reflect version change in UI.

---

## Recent Changes

| Date | Change | DC Reference |
|---|---|---|
| 2026-06-07 | CO-015 (C1 corrective): Fixed missing closing paren `))}` → `)))}` in Approved-tab JSX of `ReviewView.jsx`; was masked by CO-014's import error; added DI-002-K regression test (P0) | DI-002-K (new, VERIFIED) |
| 2026-06-07 | CO-014 (C1 corrective): Removed duplicate `import FileViewer` in `ReviewView.jsx` — caused Vite build failure and Chrome opening to error overlay; added DI-002-J regression test (P0) | DI-002-J (new, VERIFIED) |
| 2026-06-07 | CO-013 (UN-019): Splash 100% guaranteed before Chrome opens — `CloseSplash` sub in `start_splash.hta` writes `.athena_splash_done` before `window.close()`; `start_athena.ps1` polls for signal file at 200ms (6s max) before Chrome launch; fixed `Start-Sleep -Milliseconds 2500` race condition | DI-019-L (new), DI-019-G (verification updated) |
| 2026-06-07 | CO-012 (UN-007, UN-002): renamed "Content Drafts" → "MedTech Meridian Drafts" (NAV_ITEMS + ContentView h2); fixed AGENT_TAB — coaching_brief→"coaching", 4 agents→"queue"; fixed WorkQueuePanel awaiting_review routing "review"→"queue" | DI-007-F, DI-002-H, DI-002-I |
| 2026-06-07 | CO-010 (UN-033/UN-034): Voice stream sharing (DI-033-A/B/C VERIFIED); PUBLICATION_FORMAT_GUIDE in agent_base.py (DI-030-D); Output Format Standard in 8 persona files (DI-030-E); Engineering Integrity Standards in CLAUDE.md (DI-034-A–F); Version 0.6.0 | DI-033-A/B/C, DI-030-D/E, DI-034-A–F |
| 2026-06-07 | UN-003, UN-023 (CO-003): RAG reviewable reports + 50-year QARA knowledge — rich ingestion report with `## Newly Ingested Documents` table; 7 historical Tavily queries; `tm_yday` deterministic rotation; QARA RSS sources in `learning_sources.py` | DI-003-C, DI-003-D, DI-023-B, DI-023-C |
| 2026-06-07 | CO-006 (UN-032/UN-023): Consulting Agent `learn()` now generates `consulting_learning_<ts>.md` report + submits to review queue after every run; `HISTORICAL_CONSULTING_SOURCES` + `HISTORICAL_CONSULTING_KNOWLEDGE` (7 eras, 1970s–2020s) added to KB | DI-032-A, DI-032-B, DI-023-D |
| 2026-06-07 | UN-031 (CO-004): Browser tab singleton guard added — second Athena tab in Chrome now shows blocking overlay and never mounts React; `tabGuard.js` uses BroadcastChannel + localStorage heartbeat | DI-031-A, DI-031-B |
| 2026-06-06 | UN-028: VAD aggressiveness raised to 2; VAD-only silence detection; greeting routed through `_notification_queue` to eliminate startup echo | DI-028-A/B/C/D |
| 2026-06-06 | UN-029: `_device_monitor_loop` polls system default mic every 3 s; `_device_changed` Event triggers stream reopen on headphone/speaker switch | DI-029-A/B/C |
| 2026-06-06 | DI-004-E (C3): `SILENCE_DURATION` tuned to 0.5 s; requirement range updated to [0.4, 0.65] s | DI-004-E |
| 2026-06-06 | Version 0.5.3 — voice/noise discrimination + audio device detection |  |
| 2026-06-07 | CO-004 / DI-019-H (C1): keep-alive wrap replaces ceiling -- bar cycles 97->98->99->wrap@99.5 at 320 ms/pt; test_DI_019_H expanded to 9 checks | DI-019-H |
| 2026-06-07 | Version 0.5.5 -- splash bar all-whole-number freeze prevention |  |
| 2026-06-07 | CO-008 (UN-019 / DI-019-K): removed `$modelTimeout` blocking poll from `start_athena.ps1`; voice models load async in background; warm-start ≤ 10 s | DI-019-K |
| 2026-06-07 | Version 0.5.6 — async startup, warm-start under 10 s |  |
| 2026-06-07 | CO-005 (UN-002): Document Queue tab merged Documents + Review Queue into Pending/Approved/Rejected three-filter view; App.jsx NAV_ITEMS consolidated to id:queue | DI-002-E, DI-002-F, DI-002-G |
| 2026-06-07 | CO-010 (UN-033): `_voice_loop` shares one `sd.InputStream` per query cycle between `_listen_for_wake` and `_record_query` — eliminates 200-500 ms Windows MME close/reopen gap after wake detection | DI-033-A, DI-033-B, DI-033-C |
| 2026-06-07 | CO-011 (UN-034): Engineering Process Integrity — test_DI_034_A corrected (CLAUDE.md co-commit rule check); DI-034-B–F confirmed; DC-004 coverage summary corrected (34 UNs, 116 DIs); DC-005 v2.0 DI-034 procedures added; Version 0.6.1 | DI-034-A–F |
| 2026-06-06 | DI-019-J (C2): splash `#dots` now cycles `.`/`..`/`...` via VBScript `TickDots` at 400 ms/state; CSS `dotFlash` wave removed | DI-019-J |

---

## Reference Documents

| Document | Purpose |
|---|---|
| `ATHENA_ARCHITECTURE_v2.md` | Constitution — strategic blueprint, values, architectural decisions |
| `ATHENA_CLAUDE.md` | Mirror of this file — kept in sync |
| `.claude/rules/agents.md` | Agent-specific rules |
| `.claude/rules/architecture.md` | Architecture constraints |
| `.claude/rules/compliance.md` | SOC II + OWASP matrix |
| `.claude/rules/business.md` | Business rules and constraints |
