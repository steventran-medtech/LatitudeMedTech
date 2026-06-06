# Latitude MedTech — Master Skills & Knowledge Profile
**Generated:** 2026-06-05 22:19 by `skills_profile.py`

Firm-wide index of every agent's skill catalog and accumulated knowledge. Per-agent detail lives in `Athena/knowledge_base/skills/<agent>.md`.

## Firm Totals
- **Agents profiled:** 11
- **Total knowledge items accumulated:** 397
- **Total chunks indexed:** 397
- **Domains covered (34):** AI / ML, AI Applications, AI Industry, AI Research History, AI Safety, AI Technology, Biotech Industry, Consulting History 50yr, Content Strategy, Conversational AI, Deal News, EU MDR Regulatory, FDA QMS, FDA Recalls, Global Regulatory, Health Policy, Health Policy History, Journalism History 50yr, M&A Deals, ML Research, Management History 50yr, Management Research, MedTech Industry, MedTech QA/RA, Media Evolution 50yr, Medical Literature 50yr, Org Behavior History, PE/Rollup History 50yr, Quality History 50yr, Quality Management, Six Sigma / Lean, Technology History 50yr, deal_news, methodology

## Accumulation by Agent

| Agent | Tier | Items | Chunks | Last activity |
|---|---|--:|--:|---|
| Management Consulting Agent (`consulting`) | Senior Manager | 31 | 31 | 2026-06-05 21:34 |
| M&A Intelligence Agent (`ma_intelligence`) | Senior Manager | 45 | 45 | 2026-06-05 21:34 |
| FDA Agent (`fda`) | Manager | 36 | 36 | 2026-06-05 21:32 |
| EU MDR Agent (`eu_mdr`) | Manager | 20 | 20 | 2026-06-05 21:34 |
| ISO Coach Agent (`iso`) | Manager | 43 | 43 | 2026-06-05 21:31 |
| Coaching Brief Agent (`coaching`) | Manager | 31 | 31 | 2026-06-05 21:32 |
| Content Agent (`content`) | Manager | 40 | 40 | 2026-06-05 21:30 |
| Briefing Agent (`briefing`) | Senior Associate | 46 | 46 | 2026-06-05 21:31 |
| RAG Ingestion Agent (`rag`) | Senior Associate | 40 | 40 | 2026-06-05 21:33 |
| HR / L&D Manager Agent (`hr`) | Business Function | 20 | 20 | 2026-06-05 21:35 |
| Voice Assistant (Athena) (`voice_bridge`) | Associate | 45 | 45 | 2026-06-05 21:34 |

## Skill Coverage by Agent

### Management Consulting Agent (`consulting`)
*Build and maintain the firm's consulting methodology library so every deliverable lands at McKinsey/BCG quality.*
- Apply MECE, Pyramid Principle, McKinsey 7-S, BCG Matrix, Porter's 5 Forces, Issue Trees
- Architect deck structures: Executive Summary (SCQA), Strategy, Regulatory Strategy, M&A Diligence, Pitch
- Synthesise public Big 4 frameworks into reusable templates (no verbatim reproduction)
- Storyboard board-ready narratives and executive summaries

### M&A Intelligence Agent (`ma_intelligence`)
*Maintain MedTech/Pharma deal intelligence and QARA impact analysis.*
- Pre-close diligence checklists and post-close integration playbooks (QARA lens)
- Pattern-match landmark deals (Medtronic/Covidien, Abbott/St. Jude, J&J/Synthes, Stryker/Wright, BD/Bard)
- Diagnose integration failure patterns and regulatory exposure
- 50-year historical deal research via Brave queries

### FDA Agent (`fda`)
*Track FDA pathways, guidance, enforcement, and recalls; ground regulatory outputs.*
- 510(k), PMA, De Novo pathway selection and reasoning
- 21 CFR Part 820 (QSR) and design-controls interpretation
- Warning-letter and recall trend analysis for enforcement risk
- CDRH guidance monitoring and summarisation

### EU MDR Agent (`eu_mdr`)
*Maintain EU MDR 2017/745 knowledge for CE-marking and conformity strategy.*
- EU MDR 2017/745 article and annex interpretation
- Notified Body conformity-assessment routes by device class
- EUDAMED, UDI, and PMS/PSUR obligations
- Cross-walk FDA vs MDR requirements for dual-market strategy

### ISO Coach Agent (`iso`)
*Generate ISO 13485 clause coaching one clause at a time, QMS-grounded.*
- ISO 13485:2016 clause-by-clause coaching (no verbatim standard text in RAG)
- QMS design: CAPA, document control, management review, risk per ISO 14971
- Map ISO 13485 clauses to 21 CFR Part 820 equivalents
- Six Sigma / Lean quality-system improvement

### Coaching Brief Agent (`coaching`)
*Produce MedTech career coaching briefs through the human-gated orchestrator graph.*
- Career-strategy briefs for RA/QA/MedTech professionals
- Leadership and talent-development framing (HBR/McKinsey People)
- Intake → brief → human-gate → finalize workflow (LangGraph)
- Disclaimer + label discipline on every client-facing brief

### Content Agent (`content`)
*Write MedTech Meridian articles at McKinsey/BCG register with specific citations.*
- Long-form article drafting (900–1,200 words) across a 10-category curriculum
- Banned-phrase enforcement and specific-citation discipline (21 CFR §, ISO clause, $ figures)
- House-style structure: H1 title, H2 sections, frontmatter stripped at render
- Topic rotation and dedup against published history

### Briefing Agent (`briefing`)
*Produce the daily/periodic regulatory + industry intelligence briefing.*
- Synthesise FDA, IMDRF, biotech, and SoCal-MedTech feeds into a concise briefing
- Prioritise signal over noise across many sources
- Surface SoCal corridor and competitor intelligence
- Cite every item with source attribution

### RAG Ingestion Agent (`rag`)
*Ingest, chunk, and index documents into the central KB for retrieval.*
- Document chunking, tagging by category/agent, and dedup by URL hash
- TF-IDF retrieval grounding for KB-first prompting
- Maintain knowledge_base/index.json integrity
- Deep-scrape orchestration for regulatory corpora

### HR / L&D Manager Agent (`hr`)
*Track health, learning velocity, and accumulation of every agent; flag and recommend.*
- Per-agent GREEN/YELLOW/RED scoring on learning velocity and error rate
- CAPA flagging on 3+ events and remediation recommendations
- Scorecard reporting to ops/hr/ for Steven's review
- Workforce accumulation oversight (this profile system)

### Voice Assistant (Athena) (`voice_bridge`)
*Real-time voice interface: STT → orchestrator → streaming TTS.*
- Wake-word detection (openWakeWord; custom 'Hi Athena' pending)
- Whisper STT with auto mic selection and confidence logging
- Streaming Kokoro TTS, sentence-split, ~1.2s first audio
- Route spoken queries to the agent orchestrator and speak results

---
*Regenerate with `python skills_profile.py`. Alpha — Steve Review Required.*