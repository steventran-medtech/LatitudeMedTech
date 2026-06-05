# Latitude MedTech — Master Instructions
**Version:** 2026-06-05 v8 · Compressed and updated after each session per Agent Principle #7.

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
| Voice TTS | **Kokoro 82M** `bf_emma` British, port 8002 | Miso One API |
| Voice Wake | openwakeword "alexa" → `voice/wake/hi_athena.onnx` (train via Colab) |
| Frontend | React + Vite + WebSocket, localhost:3000 | Same + Auth |
| API | FastAPI, localhost:8000, rate-limited, security headers | Hardened |
| Auth | Session token `.athena.key` | Clerk/Auth0 |
| Secrets | `voice/.env` user-only permissions | AWS Secrets Manager |
| Infra | Local Windows | AWS ECS + RDS + S3 |

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
2. **Autonomous Learning** — Curated RSS weekly. **50-year historical scope** — back to 1976 Medical Device Act. PubMed Central + NEJM for medical literature depth. HR tracks minimum items/week per agent.
3. **QMS-Governed** — 21 CFR Part 820 + ISO 13485 principles applied firm-wide.
4. **CAPA on 3+ Errors** — RCA + CAPA → `ops/hr/CAPA-*.md` → Steven approves → resume. Closed: CAPA-Voice-001, CAPA-Content-001.
5. **Human Gate** — No client output without Steven's approval. All outputs: disclaimer + label.
6. **Self-Optimisation** — Agents adjust parameters from error patterns (e.g., voice silence threshold). Logged to memory, reported to HR.
7. **CLAUDE.md Maintenance** — Update after every session. Fix inaccuracies. Compress stale content. Target: ≤230 lines, every line current.

---

## New Agents (added this session)

**Consulting Agent** (`consulting_agent.py`) — builds methodology library:
- Built-in: MECE, Pyramid Principle, McKinsey 7-S, BCG Matrix, Porter's 5 Forces, Issue Tree, Storyboarding
- Slide structures: Executive Summary (SCQA), Strategy Deck, Regulatory Strategy, M&A Diligence, Pitch Deck
- Sources: McKinsey, BCG, Bain, PwC Strategy+, HBR, MIT Sloan, Stanford Social Innovation
- Modes: `learn` (default), `--generate report`

**M&A Intelligence Agent** (`ma_intelligence_agent.py`) — MedTech/Pharma deal intelligence:
- Pre-loaded: 5 landmark deals (Medtronic/Covidien, Abbott/St. Jude, J&J/Synthes, Stryker/Wright, BD/Bard) with QARA impact + lessons
- QARA frameworks: pre-close diligence checklist, post-close integration steps, failure patterns
- Sources: BioPharma Dive, Fierce Biotech/MedTech, STAT News, Evaluate Vantage
- 50-year historical Brave queries included
- Modes: `learn`, `--analyse`, `--historical`

**Marketing Agent** (`marketing_agent.py`) — Guerilla marketing manager; SoCal MedTech corridor:
- Pipeline DB: `ops/marketing/pipeline.db` — 20+ seeded targets across 6 channel types
- Channels: conference circuit (MD&M, Biocom, RAPS), podcast circuit (Medical Device Podcast, MedTech Talk), regulatory clinic, MedTech Meridian Substack, FDA docket participation, warm email outreach
- Modes: default=`brief`, `--plan` (30-60-90 day), `--outreach TARGET`, `--pipeline`, `--events`, `--scorecard`
- API: `POST /api/agents/marketing` with `{"mode": "brief|plan|events|scorecard|learn", "target": "optional"}`
- Output: `ops/marketing/` — briefs, plans, outreach drafts, events calendar, KB entries

---

## Content Standards *(MedTech Meridian)*

**Quality bar:** McKinsey/BCG standard. Specific citations required. Banned phrases enforced at prompt level.

**Non-negotiable rules:**
- Article title: H1 (`#`), sections: H2 (`##`) — no forced uppercase
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

---

## Current Phase
**Phase 1A — Coaching Core (Active, near-complete)**
- ✅ **LangGraph orchestration** — `agents/orchestrator.py`. Coaching graph: intake → generate_brief → **human-gate `interrupt()`** → finalize. Durable SQLite checkpointer (`memory/orchestrator_checkpoints.sqlite`); paused runs survive restart, resumed by `thread_id`. Endpoints: `POST /api/orchestrate/coaching` (start); review approve/reject auto-resume the linked thread. Other agents still run via subprocess.
- ✅ **Human review queue** — `/api/review/*`, `ReviewView.jsx`, `review_queue` table (now has `thread_id` linking each item to its workflow).
- ✅ **Disclaimer layer** — applied at orchestrator `finalize` (brief gets disclaimer + "Alpha — Steve Review Required" label), plus docx + agent system prompts.
- ✅ **Auth (Phase 1A scope)** — session token `.athena.key`. Clerk/Auth0 is Phase 2B.
- ⏳ **Custom "Hi Athena" wake word** — wiring done (`voice_bridge.py` auto-loads `voice/wake/hi_athena.onnx`, else "alexa"); trainer + `voice/wake/README.md` ready. **Awaiting Steven's one-time Colab training run** (external GPU). Until then, "alexa" fallback.

Phase 1A gate (Steve runs the full coaching workflow end-to-end) is met for the coaching line; only the optional custom wake word remains.

**✅ Resolved (2026-06-05):** canonical-root path issue fixed. New `agents/pathconfig.py` derives `ATHENA_ROOT` from its own file location (no `Path.home()` assumption); all 17 agent modules import it, and entry points (`voice_bridge.py`, `ui/backend/server.py`) resolve the same root from `Path(__file__)`. Verified: imports clean, `ATHENA_ROOT` → `LatitudeMedTech\Athena`, runtime paths exist. Standalone runs no longer fragile.

**✅ Resolved (2026-06-05):** Skills & KB accumulation fully wired. `agents/skills_profile.py` generates per-agent profiles (`knowledge_base/skills/<agent>.md`) and master `SKILLS.md`. `memory.get_skill_accumulation()` is the single source of truth. Workforce UI now shows an **Accumulated** column (all-time items + chunks) live from the DB, with a Refresh Skills button (`POST /api/agents/skills-profile`). `.gitignore` hardened to exclude `*.sqlite-shm`, `*.sqlite-wal`, and `.athena_ready`.

See `.claude/rules/` — agents.md · architecture.md · compliance.md · business.md
