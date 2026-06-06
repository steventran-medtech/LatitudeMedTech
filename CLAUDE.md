# Latitude MedTech — Master Instructions
**Version:** 2026-06-05 v10 · Compressed and updated after each session per Agent Principle #7.

---

## Company & North Star
**Latitude MedTech LLC** — E2E AI-powered management consulting. MedTech & Pharma. SoCal corridor.
CEO: **Steven Tran** · linkedin.com/in/huanntran100 · steven.tran@latitudemedtech.com · Status: **Alpha**

**Vision:** Steven speaks → Athena responds, delivers, executes. Real-time voice-driven analysis — not async docs.
Differentiator vs. Big 3 AI (Lilli, GENE): **interactive reasoning with voice as primary interface**.
Phase 2A target: voice + visual simultaneously (speak a query; slide deck appears as you talk).
This is the single canonical Phase 2A definition (supersedes the old "Voice Layer" framing; the Miso One voice layer is a component of it).
Phase 1 must be revenue-generating before Phase 2A work begins.
**Decision 2026-06-05 (Steven):** Phase 2A is HELD — all effort stays on closing Phase 1A until Phase 1 generates revenue.

## Business Lines
1. **Coaching** (active) — MedTech career coaching via Athena agents
2. **Consulting** (building) — FDA, EU MDR, ISO 13485, MDSAP; gated: non-compete clearance + RAC

---

## Core Values *(operating constraints)*
Dignity · Stewardship · Service · Honesty · Mercy/Grace
Any output violating these is flagged and withheld pending Steven's review.

---

## Firm Structure

**Leadership:** Steven Tran (Managing Partner/CEO — final authority) · Claude (Orchestrator)

**Agent roster by tier:**
- Senior Manager: **Consulting Agent** · **M&A Intelligence Agent** · Regulatory Strategy
- Manager: FDA · EU MDR · ISO/MDSAP · Coaching Brief · Content
- Senior Associate: RAG Ingestion · Document Generation · Human Review
- Associate: Voice (Athena) · Sales · Marketing
- Business functions: HR/L&D Manager · Legal · Finance · Sales · Marketing

**Central KB:** `Athena/knowledge_base/` searched by all agents via `KBQuery.search()` and `AgentBase.central_kb_context()`.
Subdirs: `learning/` · `consulting/` (frameworks, methodologies) · `ma/` (deal intelligence) · `skills/` (per-agent skill/KB profiles) · root (RAG docs).

**Skill/KB Profiles:** `skills_profile.py` generates a *living* profile per agent (`knowledge_base/skills/<agent>.md`) + a master `SKILLS.md` (firm root). Each profile = curated skill catalog + auto-generated accumulation block (all-time items/chunks/domains, between `<!-- ACC -->` markers) pulled from the memory DB via `Memory.get_skill_accumulation()`. Learning feeds live in dependency-free `learning_sources.py` (shared by `agent_learning.py`). Accumulation is now visible: `dashboard.py --skills` (per-agent table + firm total) and every HR scorecard/report. HR review auto-refreshes the profiles. Run manually: `run_skills.bat` or `python skills_profile.py`.

---

## Athena System

**Launch:** `Athena.lnk` → `start_athena.vbs` → `start_athena.ps1` (hidden) → Chrome `--app` mode on `localhost:3000`
**Splash:** HTA polls `localhost:8000` then `localhost:3000`; PS1 writes `.athena_ready` flag after Chrome process confirmed open; HTA closes 500ms after flag detected.
**Stop:** ⏻ button in UI (goodbye phrase + shutdown) or `stop_athena.bat`
**Icon:** `Athena\athena.ico` · **Root:** `C:\Users\huann\LatitudeMedTech\Athena\`

### Tech Stack
| Layer | Current | Target |
|---|---|---|
| LLM | claude-sonnet-4-6 / claude-haiku-4-5 | Same |
| Voice STT | Whisper `tiny.en` CPU/CUDA auto-detect | Same |
| Voice TTS | **Kokoro 82M** `bf_emma` British, port 8002 | Phase 2A (Miso One API) |
| Voice Wake | openwakeword "alexa" → `voice/wake/hi_athena.onnx` (train via Colab) |
| Frontend | React + Vite + WebSocket, localhost:3000 | Same + Auth |
| API | FastAPI, localhost:8000, rate-limited, security headers | Hardened |
| Auth | Session token `.athena.key` | Clerk/Auth0 |
| Secrets | `voice/.env` user-only permissions | AWS Secrets Manager |
| Infra | Local Windows | AWS ECS + RDS + S3 |

### Athena as Work Coordinator
Athena is the primary interface and coordinator — not just a voice assistant. She can delegate to any agent and report back.
- **Voice → agent trigger**: Athena classifies intent via Claude Haiku + tool_use, dispatches the agent, and confirms with ETA ("Starting the M&A Intelligence analysis. Should be ready in three to four minutes.").
- **Task queue** (`WorkQueuePanel` in sidebar): All running/completed agents appear here with live countdown timers, context (e.g., client name), and navigation links to the output tab. Persists across tab switches.
- **Spoken completion**: When an agent finishes, Athena says "Your [X] is ready for review" via `/api/voice/notify` → `_notification_queue` in voice_bridge.py → spoken at the next listening cycle. Only fires when voice is active.
- **Agent ETAs** are in `_AGENT_ETA_SECONDS` (voice_bridge.py) and `AGENT_ETA_SECONDS` (App.jsx) — update both when agent runtimes change.

### Voice Architecture *(CAPA-Voice-001 closed)*
- **Streaming TTS**: Claude streams → sentence split → Kokoro per sentence. First audio ~1.2s.
- **SILENCE_DURATION**: **1.5s** (0.8 cut off speech mid-sentence; 2.0 was too slow)
- **Confidence correction loop**: REMOVED — was blocking responses. Low-conf now just logs `[low conf]` tag.
- **Auto mic**: scores headset(100) > array(85) > single-mic/jack(40) > line(5). **`VOICE_INPUT_DEVICE=2`** (Microphone Array) set in `.env` for no-headphones use.
- **Model pre-warm**: OWW + Whisper load at server startup in background thread. Kokoro pre-warms at import.
- **Greeting**: Once per server session (`_session_greeted` flag). "Athena" name NOT spoken in TTS (Kokoro mispronounces it as "Atheney") — greetings use "your AI assistant" instead.
- **Wake word**: "Alexa" (fallback). Train custom `hi_athena.onnx` via [Colab notebook](https://colab.research.google.com/github/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb).
- **Always-listening limit**: Half-duplex. True <1s conversation needs local CUDA Whisper + local LLM (Phase 2A).

---

## Agent Principles

1. **Big 4 Quality** — Specific citations, no vague language, no half-finished work. McKinsey/Deloitte standard.
2. **Autonomous Learning** — Curated RSS weekly across three source tiers: (1) domain-specific current feeds, (2) `_shared` Big 4 + medical literature, (3) `_historical` 50-year retrospective feeds (Deming Institute, Drucker Institute, Federal Register, IEEE Spectrum, Nieman Lab, Health Affairs). ALL 13 agents ingest historical sources. Each agent's `.claude/agents/*.md` file defines a `## Historical Scope` section with 50-year domain milestones and a minimum 2 historical items/week learning target. `agent_base.py` injects domain evolution context into every system prompt via `HISTORICAL_CONTEXT` dict. Historical and current learning run as **separate budgets** in `learn()` — historical items never displace current news and vice versa. **Through 2026-07: 10 historical items/week per agent** (`DEFAULT_MAX_HISTORICAL = 10` in agent_learning.py — reduce to 2 after the deep-build phase). CLI: `--max-historical N` to override.
3. **QMS-Governed** — 21 CFR Part 820 + ISO 13485 principles applied firm-wide.
4. **CAPA on 3+ Errors** — RCA + CAPA → `ops/hr/CAPA-*.md` → Steven approves → resume. Closed: CAPA-Voice-001, CAPA-Content-001.
5. **Human Gate** — No client output without Steven's approval. All outputs: disclaimer + label.
6. **Self-Optimisation** — Agents adjust parameters from error patterns (e.g., voice silence threshold). Logged to memory, reported to HR.
7. **CLAUDE.md Maintenance** — Update after every session. Fix inaccuracies. Compress stale content. Target: ≤230 lines, every line current.

---

## Established Agents *(prior sessions)*
- **Consulting Agent** (`consulting_agent.py`) — MECE/Pyramid/7-S/BCG/Porter frameworks; SCQA + strategy slide structures; McKinsey/BCG/Bain/PwC sources. Modes: `learn`, `--generate report`.
- **M&A Intelligence Agent** (`ma_intelligence_agent.py`) — 5 landmark deals preloaded; QARA diligence/integration frameworks; 50-year Brave queries. Modes: `learn`, `--analyse`, `--historical`.
- **Marketing Agent** (`marketing_agent.py`) — SoCal guerilla pipeline; `ops/marketing/pipeline.db` **lazy-created on first run** (20+ targets, 6 channel types). Modes: `brief`, `--plan`, `--outreach TARGET`, `--pipeline`, `--events`, `--scorecard`. Full UI: **MarketingView.jsx** (`POST /api/agents/marketing`).

## Recent Changes *(2026-06-05)*
- **Persistent Athena Voice** — `useVoiceSession.js` hook lifts voice state to app level; tab switches no longer reset the session or close the WebSocket. `VoiceStatusBadge` in header shows live state on every tab.
- **Athena Work Queue** — `WorkQueuePanel` in sidebar shows all running/completed agents with live countdown timers, context (e.g., client name), and one-click navigation to the output tab.
- **Spoken task notifications** — `/api/voice/notify` endpoint + `_notification_queue` in `voice_bridge.py`; Athena speaks "Your [X] is ready for review" at the next listening cycle when voice is active.
- **AI audio filtering** — `webrtcvad` (aggressiveness 2) gates OpenWakeWord predictions so keyboard noise can't accumulate wake-word scores; VAD also assists silence detection in `_record_query`. Post-response echo flush extended to 1.5s.
- **Review edit-prompt** — `POST /api/review/{item_id}/edit` rewrites a pending document via natural-language instruction at consulting quality (Claude Sonnet 4.6). Button in ReviewView.jsx.
- **Dashboard charts** — `/api/dashboard/timeseries` (today/yesterday hourly token toggle) and `/api/dashboard/knowledge-growth` (daily + cumulative KB items).
- **Learning infrastructure** — `agent_learning.py` + `learning_sources.py` drive autonomous RSS/scrape feeds. `skills_profile.py` generates per-agent profiles (`knowledge_base/skills/<agent>.md`) + master `SKILLS.md`. Endpoints: `/api/agents/learn`, `/api/agents/skills-profile`.

---

## Content Standards *(MedTech Meridian)*

**Quality bar:** McKinsey/BCG standard. Specific citations required. Banned phrases enforced at prompt level.

**Non-negotiable rules:**
- Article title: H1 (`#`), sections: H2 (`##`) — no forced uppercase
- Canonical title = the body H1 (`title_from_body()`); frontmatter/slug/review-queue titles are derived from it, never written raw, and are scrubbed of non-Latin script (`clean_title()`)
- YAML frontmatter stripped before rendering; shown as metadata badge only
- BANNED: "it is important to note" · "in today's rapidly evolving" · "robust" · "leverage" · "synergy" · "in conclusion" · any generic opener
- Every claim: specific citation (21 CFR §, ISO clause, company name, dollar amount)
- Opening sentence: specific, surprising, not obvious
- Target: 900–1,200 words · **max_tokens = 4,000**
- Topic curriculum (10 categories, rotated): Regulatory Pathways · Career Strategy · FDA Enforcement · Design Controls · Quality Systems · Industry Intelligence · CAPA · Clinical/Post-Market · Professional Skills · Biotech Crossover

---

## ISO 13485 Coach
- Generates **one clause at a time** (blank input = `--next` = next ungenerated clause)
- `--all` flag only available via CLI, never from UI
- Clause selector: quick-pick chips for all clauses + datalist autocomplete
- YAML frontmatter stripped before rendering; no duplicate title (prompt says "do not include title")

---

## Autonomous QA Protocol *(every code change — no prompt needed)*
1. Syntax: `python -c "import ast; ast.parse(open(f).read())"`
2. Import: `python -c "import <module>"`
3. Path: verify referenced files/dirs exist
4. Per session: trace golden path · check regressions · verify launchers · flag unverifiable (UI/voice/audio)
- P0 = fix now · P1 = fix this session · P2 = flag and defer
- **Auto-fix**: bugs found during QA fixed in same response, no prompt.

**Deliverable rendering & title invariants** *(CAPA-Content-002)* — verify after any change to these:
- `renderInline` / `MarkdownView` (`App.jsx`, `ReviewView.jsx`) is the **shared** renderer for Briefing, Content, HR, M&A, ISO views. After touching it, confirm markdown **links**, **bold/italic/code**, and **frontmatter stripping** all still render — regress every view, not just the one in front.
- Generated **titles** must contain no non-Latin script and must match the deliverable's own H1. Content titles are derived from the body H1 via `title_from_body()` and passed through `clean_title()` (`content_agent.py`); never write a raw model title to frontmatter / slug / review queue.
- Generators must not emit their own title/date/label when the surface adds a header — labels (`Alpha — Steve Review Required`, `DRAFT — …`) belong in `status:` frontmatter (rendered as a badge), never the body.
- Long-form outputs: confirm `max_tokens` clears the worst case so nothing truncates mid-sentence/URL.

---

## Security & Compliance
SOC 2 Type II (target) · NIST CSF 2.0 · HIPAA (hard gate — no PHI until BAA) · OWASP Top 10 · 21 CFR Part 11 (future)

**Controls:** Rate limiting (120 req/min) · Security headers (CSP, X-Frame-Options, nosniff) · Path traversal protection · Input sanitisation · Session token · API docs disabled · `shell=False` all subprocesses · CORS: localhost + app:// only

---

## Hard Rules
- No API keys in code — `voice/.env` only · No client output without Steven's review
- Disclaimer + label on all outputs · No PHI until HIPAA BAA · No consulting until non-compete cleared + RAC
- No verbatim ISO text in RAG · Client data isolated by `client_id` (Phase 3+)
- 3+ errors → CAPA · `shell=False` always

---

## Build Commands
```powershell
wscript "Athena\ui\start_athena.vbs"          # Launch (or double-click Athena.lnk)
Athena\ui\stop_athena.bat                      # Stop all processes
cd Athena\ui\backend; ..\..voice\venv\Scripts\python.exe server.py  # Backend dev
cd Athena\ui\frontend; npm run dev             # Frontend dev
cd Athena\voice; kokoro_venv\Scripts\python.exe kokoro_server.py 8002  # TTS server
cd Athena\voice; venv\Scripts\activate         # Activate main venv
```

---

## Version Control *(Git)*
**Repo:** private GitHub `steventran-medtech/LatitudeMedTech` · branch `main` · root `C:\Users\huann\LatitudeMedTech`. Auth: Git Credential Manager (browser sign-in, cached).

**Session Start — pull first, every time:**
```powershell
cd "C:\Users\huann\LatitudeMedTech"; git pull
```
If `git pull` reports conflicts, resolve them before touching any other file. `git status` should be clean before starting work.

**Session End — commit and push before closing:**
```powershell
cd "C:\Users\huann\LatitudeMedTech"
git status                                    # confirm no secrets staged
git add -A
git commit -m "<concise summary of session changes>"
git push
```
Update the CLAUDE.md version line (date + vN) in the same final commit.

**Multi-session continuity:**
- Read CLAUDE.md at the top of every new session — it is the canonical state document.
- Check `## Current Phase` and any open ⏳ items before starting new work.
- If a session ends mid-task, note the stopping point in CLAUDE.md before committing.

**Safety rules:**
- `git status` before every `git add` — verify `*.pfx`, `.env`, `.athena.key` are not staged.
- **Never** `git push --force` or `git reset --hard` without Steven's explicit instruction.
- If push is rejected (non-fast-forward): `git pull --rebase`, resolve any conflicts, then push.
- If rebase has conflicts: edit the affected files, `git add` them, then `git rebase --continue`.
- Only commit to `main` — no feature branches unless Steven requests one.

**Secrets stay out of Git** — `.gitignore` excludes `*.pfx`, `.env`, `.athena.key`, venvs, `node_modules/`, logs. `StevenTran.pfx` / `voice/.env` / `voice/.athena.key` live local-only; restore manually on a fresh clone.

### Application versioning (what the user sees)
Separate from Git history, Athena tracks a user-facing **release version** so Steven can see what build he's running and what changed.
- **Single source of truth:** `Athena/VERSION.json` (`version`, `released`, `channel`, `codename`). Currently **v0.5.0 · alpha**.
- **Human history:** `Athena/CHANGELOG.md` — Keep a Changelog format, SemVer (`0.x` while alpha; each feature batch bumps minor).
- **In-app display:** sidebar footer shows `v<version> · <channel>`; clicking it opens an About panel (`AboutModal` in `App.jsx`) rendering the changelog. Served by `GET /api/version` (`server.py`, reads VERSION.json + CHANGELOG.md).
- **Cutting a release:** add notes under `## [Unreleased]` in CHANGELOG.md → move them to a new `## [x.y.z] - <date>` heading → run `ops/release.ps1 -Version x.y.z` (stamps VERSION.json, syncs `ui/frontend/package.json`, creates git tag `vx.y.z`) → commit all three together. **Bump the version whenever a meaningful feature/fix ships**, and record it in the changelog in the same commit. The backend reads VERSION.json at startup, so a version bump requires a backend restart to show in the UI.

---

## Current Phase
**Phase 1A — Coaching Core: ✅ COMPLETE (2026-06-05)**
All items shipped. Custom "Hi Athena" wake word is the only optional item remaining — awaiting Steven's one-time Colab training run; "alexa" fallback active until then.

**Phase 2A — Voice + Visual: ✅ COMPLETE (2026-06-05)**
- ✅ **Deck Agent** (`agents/deck_agent.py`) — PPTX slide deck generation. McKinsey/PwC quality. Cover, exec summary, SCR narrative, data charts, comparison tables, roadmap, recommendations, next steps. Client lookup against briefing KB. Shipped PR #30.
- ✅ **DeckView gallery UI** — deck browser with preview and download. Shipped PR #31.
- ✅ **Dashboard charts** — timeseries (hourly token spend today/yesterday) + knowledge-growth (cumulative KB items); 6 time-range toggles.

**Phase 2B — Agent Health + UX Hardening: ✅ COMPLETE (2026-06-05)**
- ✅ Briefing + Marketing outputs now surface in Documents hub review queue (`submit_for_review()`).
- ✅ Wake threshold lowered 0.5→0.35; M&A TTS substitution; per-token `speaking_word` events for Voice UI.
- ✅ `agent_learning.py` stamps `last_learning` on clean no-op runs — agents no longer stay red/yellow after a healthy run with no new items.
- ✅ `useVoiceSession.js` race condition fixed — generation counter cancels in-flight animation loops on new transcript.
- ✅ Stale dead code removed (`__import__(datetime).timedelta` in server.py; dead `CLAUSES` const in ISOView.jsx). Shipped PR #33.

**Next:** Phase 2B gate — Steven runs full coaching + voice workflow end-to-end. Auth (Clerk/Auth0) and cloud infra (AWS ECS + RDS + S3) are deferred until revenue gate.

⏳ **Open:** Custom "Hi Athena" wake word (Colab training run, external GPU required).

See `.claude/rules/` — agents.md · architecture.md · compliance.md · business.md
