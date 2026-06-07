# Latitude MedTech — Athena Platform
## High-Level Architecture & Strategic Blueprint

**Classification:** Internal Strategic Document — Confidential
**Version:** 2.1
**Date:** June 2026
**Owner:** Steven Tran (CEO/Managing Partner) · Claude (Orchestrator)

---

## Preamble: Why We Build This Way

> *"To work every day that God gives us, to accomplish something that makes up for the length of that day—that is a divine ordinance."*
> — Abraham Kuyper, *On Business and Economics*

Latitude MedTech exists to serve medical device companies navigating one of the most consequential regulatory environments in the world. A flawed submission delays a therapy. A missed gap assessment misses a patient. A confused QMS lets a defect reach the field.

We take that weight seriously. Every architectural decision below is made with two commitments in mind: **excellence in craft** (doing the work well) and **fidelity in service** (doing it for the right reasons). Technology amplifies human judgment — it does not replace it. Human dignity is not a compliance checkbox. It is a design principle.

---

## Section 1: Strategic Foundation

### 1.1 North Star

Enable medical device companies to achieve and maintain regulatory compliance faster, more accurately, and more affordably than traditional consulting — while preserving expert human judgment in every consequential decision.

### 1.2 Starting Wedge

FDA 21 CFR Part 820 gap analysis and 510(k) regulatory pathway strategy for Class II device companies — delivered via AI-assisted analysis with licensed regulatory affairs consultant (RAC) review before every client deliverable.

**Current active line:** MedTech career coaching via Athena agents. Consulting line is held pending non-compete clearance and RAC engagement.

### 1.3 What Athena Is Not

Athena is not autonomous. It does not replace licensed regulatory professionals. It is not a decision-maker. It is a force multiplier: it researches, drafts, synthesizes, and flags — and it hands every consequential output to a human expert before it reaches a client.

This is not a limitation. It is the product. Clients are not buying AI outputs. They are buying expert judgment, delivered faster and more affordably because AI handles the preparation.

---

## Section 2: Foundational Values

The following values are embedded into every workflow, every output gate, and every architectural decision. They are not a mission statement to frame on a wall — they are operational constraints.

| Value | Meaning in Practice |
|---|---|
| **Human Dignity** | Every system user — client, SME, patient downstream — is treated as an image-bearer, not a data point. No reduction of people to conversion rates or tokens. |
| **Stewardship** | We handle regulated documents, client IP, and patient-adjacent data as a trust, not a resource. Conservative data access, minimal retention, explicit consent. |
| **Common Good** | Better regulatory compliance serves patients who need safe devices. We measure success partly by whether the work makes the regulatory ecosystem healthier. |
| **Truth-telling** | Outputs are honest about uncertainty. No AI-generated confidence theater. Confidence scores are calibrated. Every deliverable is labeled for its readiness level. |
| **Servant Leadership** | AI serves the expert. The expert serves the client. The client serves the patient. No layer exploits the next. |

---

## Section 3: Architecture Overview

### 3.1 The Core Model — Advisor-Executor with SME Gate

Athena uses a three-tier execution model, not a flat multi-agent swarm:

```
┌─────────────────────────────────────────────────────────┐
│                    TIER 1: ADVISOR                      │
│          Claude Opus — Strategic reasoning              │
│    Activated only for high-stakes routing decisions     │
│    and low-confidence escalations (cost-controlled)     │
└─────────────────────┬───────────────────────────────────┘
                      │ Delegates to
┌─────────────────────▼───────────────────────────────────┐
│                   TIER 2: EXECUTOR                      │
│       Claude Sonnet — Domain agent workers              │
│   FDA Agent · EU MDR Agent · Risk Agent · CAPA Agent   │
│   Doc Gen · Audit Readiness · Supplier QA · Training   │
└─────────────────────┬───────────────────────────────────┘
                      │ All outputs flow through
┌─────────────────────▼───────────────────────────────────┐
│                 TIER 3: SME REVIEW GATE                 │
│      Steven Tran (all current outputs) · Licensed RAC   │
│      (consulting deliverables, when line opens)         │
│      No client deliverable bypasses this gate.          │
│      This is non-negotiable. It is the product.         │
└─────────────────────────────────────────────────────────┘
```

The advisor-executor pattern routes only decisions requiring deep reasoning to the more expensive model (Opus), while routine execution runs on Sonnet. This cuts costs by 60–70% versus running Opus everywhere, with no quality loss on structured regulatory tasks.

---

### 3.2 The Six Architectural Layers

```
LAYER 6 │ CLIENT INTERFACE
        │ React portal · Voice I/O · Review queue · Deliverables
        │
LAYER 5 │ ORCHESTRATION
        │ FastAPI master loop · Hub-spoke routing · State management
        │ Hooks layer (deterministic guardrails)
        │
LAYER 4 │ AGENT WORKFORCE
        │ CLAUDE.md-defined agents · Bounded subagent delegation
        │ Disjoint ownership · Explicit parent-state dependency
        │
LAYER 3 │ SKILLS
        │ Reusable modules: docx · pptx · xlsx · pdf-reading
        │ Custom: pathway-selector · FMEA · CAPA · audit-readiness
        │
LAYER 2 │ TOOL ABSTRACTION (MCP)
        │ FDA Guidance MCP Server · RAG Index MCP Server
        │ Skill Execution MCP Server · Audit Log MCP Server
        │
LAYER 1 │ DATA & INFRASTRUCTURE
        │ PostgreSQL + pgvector · S3 · AWS Secrets Manager
        │ Immutable audit logs · Client-isolated tenants
```

Each layer has **one owner, one interface, and one set of acceptance criteria.** Layers communicate through defined contracts. They do not share internal state.

---

### 3.3 MCP as the Tool Contract Layer

Model Context Protocol (MCP) is the de facto open standard for agent-to-tool integration as of 2026, with 97M+ monthly SDK downloads and support from every major AI vendor. It is used here because:

- One tool server, accessible from any agent — no duplication
- Clean upgrade path: update the MCP server, agents automatically inherit changes
- Enforces separation between *what the agent decides* and *how the tool executes*
- Production-ready horizontal scaling (cloud phase roadmap)

**MCP Servers for Athena (target architecture):**

| Server | Tools Exposed | Data |
|---|---|---|
| `fda-guidance-mcp` | `search_guidance()`, `get_cfr_section()`, `find_predicates()` | ~500 indexed FDA guidance PDFs |
| `rag-index-mcp` | `semantic_search()`, `get_chunk()` | pgvector: ISO standards, SOPs, client docs |
| `skill-execution-mcp` | `run_skill()`, `get_skill_result()` | Wraps docx, pptx, xlsx, pdf-reading |
| `audit-log-mcp` | `log_decision()`, `get_trail()` | PostgreSQL immutable log table |

---

### 3.4 Hooks — What Claude Cannot Bypass

Hooks are deterministic code that execute at fixed points in the agent loop, outside Claude's control. This is the correct pattern for regulated environments.

```
HOOK POINTS:
  before_agent_call  → Validate input schema · Check rate limits · Log request
  after_tool_call    → Validate tool output · Log tool usage
  before_response    → Add disclaimer · Check confidence score
                     → Gate to SME review if high-stakes
                     → Apply readiness label (Demo/Alpha/Beta/Prod)
  on_error           → Escalate to orchestrator · Log incident
```

No client-facing output leaves the system without passing:
1. Schema validation (automated)
2. Confidence scoring ≥ 0.65 (automated)
3. Disclaimer present (automated)
4. Citation check — all claims cite FDA/ISO sources (automated)
5. Readiness label applied (automated)
6. **SME review and approval (human, mandatory, no bypass)**

---

## Section 4: Agent Workforce

### 4.1 Design Principles for Each Agent

Every agent is defined by a configuration that specifies:
- **Role** — what it is
- **Scope** — what it owns (and explicitly, what it does not)
- **Tools** — which MCP tools it may call
- **Guardrails** — what it must never do
- **Output format** — exact JSON schema + document type
- **Confidence behavior** — what triggers escalation

Agents do not communicate directly with each other. All routing flows through the orchestrator (hub-spoke). This keeps debugging tractable at scale.

### 4.2 Agent Roster — Current State & Roadmap

**Active (Phase 1A / 2A / 2B — June 2026)**

| Tier | Agent | Module | Scope |
|---|---|---|---|
| Orchestrator | Athena Voice | `voice_bridge.py` | Intent classification · agent dispatch · task queue · spoken notifications |
| Senior Manager | Consulting Agent | `consulting_agent.py` | MECE/Pyramid/7-S/BCG/Porter · SCQA strategy · McKinsey/BCG/Bain sources |
| Senior Manager | M&A Intelligence Agent | `ma_intelligence_agent.py` | 5 landmark deals preloaded · QARA diligence · 50-year Brave queries |
| Manager | Coaching Brief Agent | `coaching_brief_agent.py` | MedTech career coaching · resume · interview · career strategy |
| Manager | Content Agent | `content_agent.py` | MedTech Meridian articles · 10-category curriculum · 900–1,200 words |
| Manager | Deck Agent | `agents/deck_agent.py` | PPTX slide decks · McKinsey/PwC quality · SCR narrative |
| Associate | Marketing Agent | `marketing_agent.py` | SoCal guerilla pipeline · 20+ targets · 6 channel types |
| Infrastructure | Human Review Queue | `server.py` review endpoints | Approval routing · SME assignment · edit-prompt revision |
| Infrastructure | Document Generation | via skills | Memos · reports · slide decks |

**Roadmap — Consulting Core (Phase 3, held pending revenue + RAC)**

| Agent | Scope | Key Skills | MCP Tools |
|---|---|---|---|
| FDA Regulatory | 510(k) · De Novo · PMA · predicates | pdf-reading · docx · pathway-selector | fda-guidance-mcp · rag-index-mcp |
| EU MDR Regulatory | MDR 2017/745 · IVDR · Notified Body | pdf-reading · docx | rag-index-mcp |
| ISO 13485 / MDSAP Audit | Gap analysis · audit readiness | xlsx · audit-readiness | rag-index-mcp |
| Risk Management | ISO 14971 · FMEA · hazard analysis | xlsx · risk-fmea | fda-guidance-mcp |

**Roadmap — Full QMS Advisory (Phase 4)**

| Agent | Scope |
|---|---|
| CAPA Operations | NC intake · root cause · remediation planning |
| Design Controls | DHF structure · design review facilitation |
| Supplier Quality | Approved supplier list · audit scorecards |
| Complaint Handling | MDR/MDV triage · complaint classification |
| Management Review | KPI dashboards · review input packages |
| Internal Audit | Audit schedules · finding reports |
| Training & Development | Training matrix · curricula |

### 4.3 Subagent Rules

Agents may spawn child agents for parallelizable subtasks. Hard constraints:

- Maximum depth: **2 levels** (parent → child, no grandchildren)
- Maximum children per parent: **5 per execution**
- Child context is isolated — no access to parent's full state
- All child outputs return to parent; parent synthesizes before escalating

This limit is deliberately conservative. Beyond depth 2, debugging multi-agent failures becomes exponentially harder. The constraint is a feature.

---

## Section 5: Data Architecture

### 5.1 Data Tenancy Model

Every client is fully isolated at the database level. No cross-client query is possible by design — not by permission model, by schema.

```
Client A schema:  latitude_client_a.*
Client B schema:  latitude_client_b.*
Shared schema:    latitude_shared.* (FDA guidance index only)
```

*Current state (local): client isolation enforced via `client_id` in SQLite. Full schema isolation applies when cloud PostgreSQL is provisioned.*

### 5.2 What Lives Where

| Data Type | Storage | Retention | Access |
|---|---|---|---|
| Client documents | S3 (encrypted, per-tenant bucket) | Per contract | Client + RAC only |
| RAG index | pgvector (per-tenant schema) | Per contract | Agent + RAC only |
| Audit logs | PostgreSQL (immutable, append-only) | 7 years | RAC + Compliance only |
| Agent outputs (drafts) | PostgreSQL (drafts table) | 90 days | RAC + Client |
| Approved deliverables | S3 (signed URL, time-limited) | Per contract | Client only |
| FDA guidance index | pgvector (shared schema) | Rolling (updated monthly) | All agents |

*Current state: SQLite local DB + local file storage. Cloud architecture provisions at revenue gate.*

### 5.3 What We Do Not Store

- PHI (Protected Health Information) — no clinical trial data, no patient records until HIPAA BAA signed
- Real credentials — all secrets in `voice/.env` (local); AWS Secrets Manager (cloud)
- Raw ISO standard text — licensing requires ingestion without reproduction
- User passwords — delegated to Auth0/Clerk (deferred to revenue gate)

---

## Section 6: Workflow Patterns

### 6.1 Standard Query — Regulatory Pathway Assessment

```
1. Client submits query (web portal or voice)
2. Orchestrator validates input schema [Hook]
3. Orchestrator routes to FDA Agent
4. FDA Agent:
   a. Calls semantic_search() via rag-index-mcp
   b. Calls search_guidance() via fda-guidance-mcp
   c. Calls pathway-selector skill
   d. Constructs structured JSON output
5. Confidence check [Hook] — if < 0.65, escalate to Advisor (Opus)
6. Document Generation Agent drafts memo via docx skill
7. Disclaimer + readiness label applied [Hook]
8. Output routed to SME Review Queue
9. Licensed RAC reviews, edits, approves
10. Approved deliverable released to client
11. Full audit trail logged [Hook]: query → agents → tools → drafts → review → approval
```

### 6.2 Parallel Processing — Multi-Market Gap Analysis

```
1. Client requests: "FDA + EU MDR + MDSAP gap analysis"
2. Orchestrator spawns 3 parallel agents (within 5-child budget):
   ├── FDA Gap Agent        (21 CFR 820 vs. client QMS)
   ├── EU MDR Gap Agent     (MDR 2017/745 vs. client QMS)
   └── MDSAP Gap Agent      (ISO 13485 vs. client QMS)
3. All three execute concurrently — wall time = slowest agent, not sum
4. Orchestrator merges outputs
5. Document Gen Agent produces consolidated xlsx matrix
6. SME reviews consolidated output as single package
7. Client receives unified compliance matrix
```

### 6.3 Event-Triggered — Nonconformance to CAPA

```
Trigger: NC filed in client QMS
1. Webhook fires to Orchestrator
2. CAPA Agent:
   a. Extracts severity, product, failure mode
   b. Generates root cause analysis
   c. Spawns Risk Management Subagent (parallel)
3. Risk Assessment returned to CAPA Agent
4. If critical finding: route to Management Review Agent
5. Management Review Agent:
   a. Evaluates remediation effectiveness
   b. Generates management review brief (pptx)
6. SME approves action plan
7. Client notified; audit trail records full chain
```

---

## Section 7: Human-in-the-Loop Design

### 7.1 The Right Model of HITL

A common mistake is treating human oversight as friction to be minimized or eventually removed. This is wrong in principle and counterproductive in practice.

In regulated industries, human oversight is not a temporary limitation. It is a **permanent feature** of certain workflow categories — regulatory decisions, client-facing communications, and novel situations outside defined parameters.

The correct model: **approval triggers defined by action type, value threshold, and confidence level — not by blanket policy.**

| Action Type | Trigger | Oversight Level |
|---|---|---|
| Regulatory pathway recommendation | Always | SME approval required |
| Gap analysis output | Always | SME approval required |
| CAPA action plan | Risk-based | SME approval if critical finding |
| Document formatting only | Never | Automated release |
| Internal draft for SME review | Never | SME sees it as input, not output |
| Novel regulatory situation | Confidence < 0.65 | Escalate to Advisor → SME |

### 7.2 Avoiding Automation Complacency

Research shows that consent fatigue leads to humans approving automated prompts without genuine review at high rates. This is a known failure mode — not a solved problem.

Our mitigation:
- SME reviews are **summary-first**: agent presents key findings, risks, and uncertainties before the full document
- Confidence scores are **always visible** to the SME — never hidden
- Readiness labels are **prominent** — a Beta output looks different from a Production output
- SMEs can **reject with one click and request revision** — friction is removed from the right path, not from oversight

---

## Section 8: Build Phases

### Phase 0 — Foundation ✅ Complete

Infrastructure provisioned. Git repo, secrets management, local dev environment confirmed.

---

### Phase 1A — Coaching Core ✅ Complete (2026-06-05)

Voice agent, coaching brief, content agent, knowledge base, dashboard, M&A intelligence, consulting agent, deck agent, marketing agent. Full Athena UI with review queue, work queue panel, voice session persistence.

**Shipped:** PRs #1–33. Version v0.5.0 · Alpha.

---

### Phase 2A — Voice + Visual ✅ Complete (2026-06-05)

Deck Agent (`agents/deck_agent.py`) — PPTX generation at McKinsey/PwC quality. DeckView gallery UI. Dashboard charts (timeseries token spend + knowledge growth). Persistent voice session across tab switches. Task queue with live countdown timers.

---

### Phase 2B — Agent Health + UX Hardening ✅ Complete (2026-06-05)

Briefing + Marketing outputs surface in review queue. Wake threshold lowered. Agent learning stamps `last_learning` on clean runs. Race conditions fixed. Dead code removed. Skills profiles (`skills_profile.py`) + master `SKILLS.md`.

**Phase 2B Gate:** ⏳ Pending — Steven runs full coaching + voice workflow end-to-end.

---

### Phase 3 — Consulting Core 🔒 Held

**Blocked by:** Phase 1 revenue generation · Non-compete clearance · RAC engagement confirmed.

**Goal:** One complete consulting workflow, end-to-end, with real SME review.

FDA regulatory pathway query → Agent analysis → Draft memo → SME review → Client delivery → Audit trail.

**Agent team:**
- Agent-1: Orchestrator Builder (master loop, routing, hooks)
- Agent-2: FDA Agent + RAG integration (semantic search, guidance lookup)
- Agent-3: MCP Server Architect (4 MCP servers with test coverage)
- Agent-4: Skills Adapter (wrap docx/pdf-reading for agent use)
- Agent-5: Review Queue enhancements (RAC dashboard, approval/reject flow)

**Verification gate:** RAC submits a 510(k) query; system produces a reviewed, approved, labeled memo; audit trail is complete.

---

### Phase 4 — Expanded Regulatory

**Goal:** Multi-market coverage + parallel processing pattern.

Add EU MDR, MDSAP, ISO 13485 agents. Deliver consolidated multi-market gap analysis. Introduce xlsx skill for compliance matrices.

**Verification gate:** Parallel 3-agent gap analysis completes; consolidated matrix reviewed by SME; client receives single deliverable.

---

### Phase 5 — Full QMS Advisory Roster

**Goal:** All process-owner agents active; event-triggered workflow chains.

CAPA → Risk Management → Management Review trigger chains. Internal Audit scheduling. Training matrix generation.

**Verification gate:** NC filed → system executes full chain autonomously → SME approves final action plan → client notified.

---

### Phase 6 — Client-Facing Hardening

**Goal:** Multi-tenant SaaS ready for 5 paying beta clients.

RBAC at DB level. Usage metering. SLA monitoring. Penetration test. Beta onboarding with 3–5 design partners.

**Verification gate:** 5 beta clients onboarded; using system for real regulatory work; zero cross-tenant data access confirmed by pen test; SME coverage documented.

---

## Section 9: Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| LLM — Executor | Claude Sonnet 4.6 | Regulatory reasoning, tool use, long-context |
| LLM — Advisor | Claude Opus 4.8 | Activated only for escalations; cost-controlled |
| Orchestration | FastAPI (Python async) + Claude Agent SDK | Custom loop; full observability; no black-box orchestrator |
| Tool abstraction | MCP (Streamable HTTP, 2026 spec) | De facto standard; horizontal scaling ready |
| RAG | PostgreSQL + pgvector (cloud) / SQLite (local) | Auditable; metadata filtering; familiar operations |
| Document generation | docx / pptx / xlsx skills | Reuse existing; no rebuilding |
| Auth | Session token `.athena.key` (local) — Auth0/Clerk deferred | RBAC at revenue gate |
| Voice STT | Whisper `tiny.en` (local, CPU/CUDA auto-detect) | Regulatory terminology; no API dependency |
| Voice TTS | Kokoro 82M `bf_emma` (local, port 8002) | Natural; low latency; no API cost |
| Voice Wake | openwakeword "alexa" (fallback) — custom `hi_athena.onnx` pending | Always-listening entry point |
| Infrastructure | Local Windows (AWS ECS + RDS + S3 deferred to revenue gate) | HIPAA-eligible at cloud phase |
| Audit logging | SQLite (local) → PostgreSQL append-only + S3 Parquet (cloud) | Immutable; queryable; 7-year retention target |
| Frontend | React + Vite + WebSocket | Real-time streaming; component isolation |

**Framework decision:** We do not use LangGraph. The hub-spoke pattern with FastAPI and Claude Agent SDK provides full transparency, single-threaded debuggability, and lower operational overhead. We earn complexity only when the simpler system proves insufficient.

---

## Section 10: Skills Composition

| Phase | Agent | Reuse | Custom Build |
|---|---|---|---|
| 1A | Coaching Brief | pdf-reading, docx | coaching-brief-generator |
| 1A | Content | docx | article-generator, banned-phrase-filter |
| 2A | Deck | pptx | scr-narrative-builder, chart-generator |
| 3 | FDA Regulatory | pdf-reading, docx | regulatory-pathway-selector |
| 3 | Document Gen | docx, pptx | None |
| 4 | EU MDR | pdf-reading, docx | None (adapted from FDA agent) |
| 4 | Risk Management | xlsx | risk-fmea, iso-14971-scorer |
| 5 | CAPA Operations | docx, xlsx | capa-root-cause-analyzer |
| 6 | Management Review | pptx | kpi-dashboard-builder |
| 6 | Internal Audit | xlsx | audit-schedule-generator |

Custom skills are built using the `skill-creator` framework. Each skill has test prompts and a calibration eval before it enters production.

---

## Section 11: Verification Gates

Ten mandatory gates. All ten must pass before any deliverable reaches a client.

| Gate | Type | Owner | Bypass? |
|---|---|---|---|
| 1. Input schema valid | Automated | Hook | Never |
| 2. Output schema valid | Automated | Hook | Never |
| 3. Confidence ≥ 0.65 | Automated | Hook | Never (escalate, don't bypass) |
| 4. Disclaimer present | Automated | Hook | Never |
| 5. Citations present | Automated | Hook | Never |
| 6. Readiness label applied | Automated | Hook | Never |
| 7. No cross-tenant data | Automated | DB constraint | Never |
| 8. Audit trail complete | Automated | Hook | Never |
| 9. No secrets in output | Automated | Hook | Never |
| 10. SME approval confirmed | Human | Steven (current) · Licensed RAC (consulting line) | Never |

Gate 10 is the only gate owned by a human. It is also the only gate that matters to the client. Everything before it is infrastructure for Gate 10.

---

## Section 12: Production Blockers

These must be resolved before consulting line opens for paying clients:

- [ ] Legal entity formed and bank account open
- [ ] Terms of Service and AI disclaimer reviewed by attorney
- [ ] Non-compete clearance confirmed
- [ ] Licensed RAC engagement (employee or contract) confirmed
- [ ] Consulting liability insurance secured
- [ ] RBAC confirmed at DB level (pen test signed off)
- [ ] ISO standard licensing reviewed — no unauthorized text reproduction
- [ ] Data retention and deletion policy implemented and documented
- [ ] Incident response runbook written and tested
- [ ] HIPAA BAA template prepared (even if PHI not yet in scope)
- [ ] SME review workflow has zero bypass path — confirmed in code, not just policy

---

## Section 13: Open Questions

| # | Question | Priority | Status | Who Decides |
|---|---|---|---|---|
| 1 | Will the first RAC be a full-time hire or a contract reviewer? | Critical | Open — deferred until consulting line unblocks | Steven |
| 2 | Which ISO standards can be legally ingested for RAG? (licensing) | Critical | Open — deferred until consulting line unblocks | Steven + Counsel |
| 3 | Primary consulting client profile: Pre-submission startups or established QMS maintenance? | High | Leaning pre-submission startups | Steven |
| 4 | Voice interface: internal SME use only, or client-facing? | High | **Resolved:** Internal first; client-facing roadmap post-Phase 3 | Steven |
| 5 | Will EU MDR include notified body interaction facilitation? | Medium | Open | Steven |
| 6 | Business model: per-seat SaaS, per-submission, retainer, or hybrid? | Medium | Open — defer to Phase 3 | Steven |
| 7 | CRM integration: HubSpot, Salesforce, or custom? | Medium | Defer to Phase 5 | — |
| 8 | Multi-language support (DE/FR for EU)? | Low | Defer to Phase 6 | — |

Questions 1 and 2 block Phase 3. All others can be resolved during or after Phase 3.

---

## Section 14: Key Performance Indicators

| Metric | Target | How Measured |
|---|---|---|
| Regulatory accuracy (SME pass rate) | ≥ 95% | Spot-check 100 outputs/month |
| Turnaround time (query to approved deliverable) | ≤ 4 hours | Timestamp logs, end-to-end |
| AI cost per deliverable | ≤ $15 (API cost only) | Token logs + cost dashboard |
| Client deliverable cost vs. traditional consulting | ≤ 30% of market rate | Pricing model vs. market benchmarks |
| SME review time per deliverable | ≤ 45 minutes | Time-stamped queue events |
| System uptime | ≥ 99.5% | Infrastructure monitoring |
| Confidence calibration accuracy | ±5% (0.8 confidence = 75–85% pass rate) | Calibration curve, monthly |
| Audit trail completeness | 100% | Automated audit log verification |

---

## Section 15: Current Milestone & Next Steps

**Immediate — Phase 2B Gate:**

Steven runs full coaching + voice workflow end-to-end. This is the gate before any new Phase 3 work begins.

Walkthrough checklist:
1. Launch via `Athena.lnk` — confirm splash and Chrome app mode
2. Voice activation — confirm wake word and first-response latency
3. Request a coaching brief — confirm agent dispatch, ETA announcement, task queue
4. Review output in Documents hub — confirm disclaimer, readiness label, edit-prompt
5. Request a deck — confirm DeckView gallery and download
6. Check dashboard — confirm token timeseries and knowledge-growth charts
7. Confirm audit log entries for the session

**Revenue Gate — before Phase 3 starts:**

Phase 1 must generate revenue before Phase 3 (Consulting Core) development begins. This is a firm commitment (decided 2026-06-05).

**Cloud Gate — before beta clients:**

Auth0/Clerk, AWS ECS + RDS + S3 provision only after consulting line opens and first revenue is confirmed.

---

## Appendix: Glossary

| Term | Definition |
|---|---|
| Advisor | Claude Opus — activated only for high-stakes routing or low-confidence escalation |
| Executor | Claude Sonnet — routine agent execution |
| Orchestrator | FastAPI master loop; routes queries, manages state, enforces hooks |
| Worker Agent | Specialized agent with bounded scope (FDA, CAPA, Risk, etc.) |
| Subagent | Child agent spawned by parent; depth- and budget-limited |
| Hub-Spoke | One orchestrator, multiple isolated workers; no direct worker-to-worker communication |
| MCP | Model Context Protocol; open standard for agent-to-tool integration |
| Hook | Deterministic code outside Claude's control; runs at fixed points in agent loop |
| Skill | Reusable capability module (docx generation, FMEA, pathway selection) |
| Verification Gate | Boolean check that must pass before output proceeds |
| SME Gate | Steven Tran (current) · Licensed RAC (consulting line); mandatory for all client deliverables |
| Readiness Label | Explicit status on every output: Demo / Alpha / Beta / Production |
| Confidence Score | 0.0–1.0; agent's calibrated uncertainty estimate; gates escalation at < 0.65 |
| Audit Trail | Immutable log: user → orchestrator → agent → tools → draft → SME → approval → delivery |
| HITL | Human-in-the-loop; oversight model where action type determines trigger, not blanket policy |
| RAC | Regulatory Affairs Consultant (licensed professional); owner of Gate 10 for consulting deliverables |
| Revenue Gate | Phase 1 must generate revenue before Phase 3 (Consulting Core) development begins |

---

*"The person is not a system of algorithms."*
— Pope Leo XIV

We build Athena to serve people — the consultants who use it, the companies that rely on it, and the patients who ultimately depend on the devices it helps bring safely to market. Every layer of this architecture is in service of that chain.

---

**Document Status:** Active — Phase 1A/2A/2B complete. Phase 2B gate pending. Phase 3 held at revenue gate.
**Standing Orders:** `ATHENA_CLAUDE.md` — operational instructions Claude reads before every session.
**Next Review:** When Phase 2B gate passes or Phase 3 unblocks.
