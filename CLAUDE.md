# Athena — Standing Orders
**Version:** 2026-06-06 v12 · Aligned with `ATHENA_ARCHITECTURE_v2.md` (Constitution)
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
| 2B Gate | ⏳ Pending | Steven runs full coaching + voice workflow end-to-end |
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
| Associate | Marketing Agent | `marketing_agent.py` |
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

## Reference Documents

| Document | Purpose |
|---|---|
| `ATHENA_ARCHITECTURE_v2.md` | Constitution — strategic blueprint, values, architectural decisions |
| `ATHENA_CLAUDE.md` | Mirror of this file — kept in sync |
| `.claude/rules/agents.md` | Agent-specific rules |
| `.claude/rules/architecture.md` | Architecture constraints |
| `.claude/rules/compliance.md` | SOC II + OWASP matrix |
| `.claude/rules/business.md` | Business rules and constraints |
