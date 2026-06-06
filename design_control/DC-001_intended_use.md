# DC-001 — Intended Use & User Needs
**Document:** DC-001 · Version 1.2 · 2026-06-05  
**Approved by:** Steven Tran

---

## 1. Intended Use Statement

Athena is an AI-powered internal business operations platform for
**Latitude MedTech LLC**. It assists the Managing Partner (Steven Tran) in
running MedTech and Pharma career coaching and management consulting
operations through autonomous AI agents, a voice interface, a review
workflow, and document generation capabilities.

**Intended use environment:** Windows 11, local machine, no external network
access to client systems, no cloud deployment at Alpha stage.

**Intended users:** Steven Tran (sole operator at Alpha). No client-facing
access is permitted until Beta/Production controls are in place.

**Operational status at time of writing:** Alpha — all AI-generated outputs
are reviewed and approved by Steven before any downstream use.

---

## 2. What Athena Is NOT

These are explicit contraindications. The system must not be used for:

| # | Prohibited Use | Hard Rule Source |
|---|---|---|
| CI-001 | Direct delivery of regulatory advice to clients without a licensed RAC consultant review | compliance.md §Hard Stops |
| CI-002 | Storage, processing, or transmission of Protected Health Information (PHI) | HIPAA — no BAA in place |
| CI-003 | Any consulting client work prior to non-compete attorney clearance | compliance.md §Hard Stops |
| CI-004 | Client portal or multi-user access at Alpha/Beta without RBAC | compliance.md §Production Blockers |
| CI-005 | Ingestion of verbatim ISO standard text into RAG | IP/licensing constraint |
| CI-006 | Any action where `shell=True` in subprocess calls | Security hard rule |

---

## 3. User Profile

| Attribute | Value |
|---|---|
| Name | Steven Tran |
| Role | Managing Partner / CEO |
| Domain expertise | MedTech/Pharma regulatory affairs (FDA 21 CFR 820, ISO 13485, EU MDR, MDSAP) |
| Technical proficiency | Advanced — installs, runs, and maintains the system |
| Use frequency | Daily operational use |
| Decision authority | Final approval on all AI outputs; sole human in the loop at Alpha |

---

## 4. Use Environment

| Attribute | Value |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| Hardware | Local machine — CPU Whisper inference; CUDA optional |
| Network | Local only at Alpha; no external client access |
| Backend | FastAPI localhost:8000 |
| Frontend | React/Vite localhost:3000, Chrome `--app` mode |
| TTS | Kokoro 82M, port 8002 |
| Secrets | `Athena/voice/.env` — local-only, not in git |

---

## 5. User Needs

User needs express *what* the system must accomplish — not *how*. Each is
stated from the user's perspective in the format: "I need to…"

These are the enumerated, controlled user needs for Athena v0.5 (Alpha).

### Coaching Business Line

| ID | User Need | Priority |
|---|---|---|
| UN-001 | Generate a client preparation brief for an upcoming coaching session, starting from only the client's name or LinkedIn URL | P0 |
| UN-002 | Review every AI-generated output before it is delivered, acted upon, or stored as final — and be able to approve, reject, or request edits | P0 |
| UN-003 | Maintain a persistent knowledge base of domain documents and prior interactions that agents can search | P1 |
| UN-018 | Capture and manage the full lifecycle of coaching clients — intake, program assignment, engagement tracking, and SOW generation — through a structured form with validated required fields | P0 |

### Voice Interface

| ID | User Need | Priority |
|---|---|---|
| UN-004 | Speak to Athena hands-free and receive a voiced response, routing my query to the appropriate agent automatically | P0 |
| UN-005 | Be verbally notified when a long-running agent task completes, without checking the UI | P1 |
| UN-006 | Keep my voice session alive as I navigate between UI tabs, without losing context or resetting | P1 |
| UN-022 | Interact with a voice agent that responds with the quality and conversational fluency expected of a chief of staff or expert management consultant — audible response shall commence within 2 seconds of completing a spoken query | P1 |

### Content & Marketing

| ID | User Need | Priority |
|---|---|---|
| UN-007 | Draft MedTech Meridian articles (Substack/LinkedIn) that meet McKinsey/BCG editorial quality, with cited claims | P0 |
| UN-008 | Track and manage my marketing outreach pipeline across Southern California targets at zero cash budget | P1 |
| UN-009 | Generate branded PPTX slide decks for consulting proposals on demand | P1 |

### Regulatory Intelligence

| ID | User Need | Priority |
|---|---|---|
| UN-010 | Access ISO 13485 clause-by-clause coaching content on demand | P0 |
| UN-011 | Monitor and analyze MedTech M&A deals with QARA integration frameworks | P1 |
| UN-012 | Receive structured briefings on FDA, EU MDR, and IMDRF regulatory developments | P1 |
| UN-023 | Agents shall learn from and reason over historical data dating back at least 50 years — including regulatory filings, device clearance precedents, clinical evidence, standards evolution, and industry transactions — so that analysis reflects the full arc of the MedTech regulatory landscape and is not artificially constrained to recent data | P1 |

### Operations & Monitoring

| ID | User Need | Priority |
|---|---|---|
| UN-013 | See real-time system health, agent status, token spend, and knowledge base growth in a dashboard | P1 |
| UN-014 | Track each agent's accumulated learning, skills profile, and last-learning timestamp | P1 |

### Security & Compliance

| ID | User Need | Priority |
|---|---|---|
| UN-015 | Operate the system with confidence that API keys, session tokens, and any sensitive data cannot be exposed by the system itself | P0 |
| UN-016 | Have every AI-generated output automatically labeled with its readiness status and a regulatory disclaimer | P0 |
| UN-017 | Maintain a searchable audit log of agent outputs and review decisions | P1 |

### Startup Experience

| ID | User Need | Priority |
|---|---|---|
| UN-019 | See startup progress displayed cleanly — a full-width progress bar at the window bottom, without a distracting numeric percentage counter | P2 |
| UN-021 | It shall not be possible to operate two simultaneous instances of Athena in the same Windows session — a second launch attempt shall either bring the existing instance to the foreground or stop it completely before starting a fresh one; at no point shall two conflicting backend + frontend stacks be running at the same time | P0 |

---

## 6. Priority Definitions

| Priority | Definition |
|---|---|
| P0 | System does not meet intended use without this. Failures block release. |
| P1 | Important capability; failure degrades user value but does not block core use. |
| P2 | Enhancement; deferred to future phase without impact to current operations. |
