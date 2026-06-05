# Architecture & Phase Roadmap

## Folder Structure
```
C:\Users\huann\LatitudeMedTech\
├── CLAUDE.md                          ← Master instructions (this system)
├── .claude\
│   ├── rules\
│   │   ├── agents.md                  ← Agent roster + trigger chains
│   │   ├── architecture.md            ← This file
│   │   ├── compliance.md              ← Legal + regulatory constraints
│   │   └── business.md                ← Coaching ops + client rules
│   ├── agents\                        ← Subagent persona files
│   │   ├── fda-agent.md
│   │   ├── eu-mdr-agent.md
│   │   ├── iso-agent.md
│   │   ├── coaching-agent.md
│   │   └── content-agent.md
│   └── commands\                      ← Custom slash commands
│       ├── new-client.md              ← /project:new-client
│       ├── sprint-review.md           ← /project:sprint-review
│       └── generate-sop.md            ← /project:generate-sop
│
├── Athena\                            ← Core AI system (built)
│   ├── agents\                        ← Python agent scripts
│   ├── voice\                         ← Whisper STT + Piper TTS + .env
│   ├── ui\
│   │   ├── backend\                   ← FastAPI server.py
│   │   ├── frontend\                  ← React + Vite
│   │   ├── start_athena.bat
│   │   └── stop_athena.bat
│   ├── content\drafts\                ← MedTech Meridian drafts
│   ├── coaching\briefs\               ← Discovery call briefs
│   ├── knowledge_base\                ← RAG indexed docs
│   └── logs\
│
├── clients\                           ← Client files (Phase 3+)
├── ops\                               ← SOPs, contracts, runbooks
├── marketing\                         ← Brand assets, campaigns
└── finance\                           ← P&L, invoicing, projections
```

## Tech Stack
| Layer | Current | Target |
|---|---|---|
| LLM | Claude API (claude-sonnet-4-6) | Same |
| Orchestration | LangGraph (coaching) + subprocess (other agents) | LangGraph (all) |
| RAG | Local JSONL | pgvector + PostgreSQL |
| API | FastAPI | FastAPI (hardened) |
| Frontend | React + Vite + WebSocket | Same + Auth |
| Voice STT | Whisper | Whisper → Miso One |
| Voice TTS | Piper | Miso One (110ms latency) |
| Auth | None | Clerk or Auth0 |
| Infra | Local Windows | AWS ECS + RDS + S3 |
| Secrets | .env file (local) | AWS Secrets Manager |

## Phase Roadmap
**Phase 1A — Coaching Core (NOW, near-complete)**
- ✅ Restructure under LatitudeMedTech root
- ✅ CLAUDE.md + rule files in place
- ✅ LangGraph orchestration — `agents/orchestrator.py` (coaching graph w/ human-gate interrupt + SQLite checkpointer)
- ✅ Human review queue (Steve approves all outputs; `thread_id`-linked to workflow)
- ✅ Disclaimer layer on all outputs (orchestrator finalize + docx + system prompts)
- ⏳ Custom "Hi Athena" wake word — wired; awaiting Steven's Colab training run
- ✅ Gate: Steve can run full coaching workflow end-to-end

**Phase 1B — Content & Growth (Weeks 7–10)**
- Content agent hardened (MedTech Meridian pipeline)
- Editorial calendar automation
- Sales agent (coaching pipeline only)
- Model tiering: Haiku for routing/summaries
- Gate: Steve approves and publishes Substack draft fully AI-assisted

**Phase 1C — Consulting Infrastructure (Weeks 11–20)**
- All regulatory agents BUILT and TESTED on public/synthetic data
- All 10 QMS process owner agents built
- LangGraph trigger chains operational
- Full RAG pipeline (public FDA/EU guidance only)
- Agents held inactive — zero client consulting work
- Gate: All agents eval-verified by Steve as SME

**Phase 2A — Voice + Visual (HELD until Phase 1 is revenue-generating)**
Canonical definition (per CLAUDE.md v6): speak a query and a slide deck renders as you talk.
Encompasses the voice layer as a component:
- Miso One TTS integration · real-time WebSocket voice streaming · latency under 2s
- Simultaneous visual rendering (deck/visuals generated live from the spoken query)
- Gate: Steve speaks a query and receives a voiced, reviewed response with live visual output
- **Decision 2026-06-05:** held; not started. All effort on Phase 1A until Phase 1 generates revenue.

**Phase 2B — Consulting Activation (Post-departure)**
- Non-compete confirmed cleared by attorney
- RAC consultant engaged
- Consulting agents activated
- Auth0 multi-tenant auth
- Client portal
- Penetration test
- Beta clients (3–5 from Biocom network)
- Gate: First paying consulting client onboarded
