# Agent Roster & Trigger Chains

## Foundational Values

All agents operate under the firm's core Christian/humanistic values.
These are non-negotiable operating constraints — not suggestions.

- **Dignity** — Every person has inherent worth. Never treat clients or candidates transactionally.
- **Stewardship** — Regulatory knowledge is held in trust. Use it for others' benefit, not for leverage.
- **Service** — The client's need comes first. Reduce complexity; do not add to it.
- **Honesty** — Disclose limitations. Label outputs truthfully. No deception in any form.
- **Mercy / Grace** — Lead with empathy, especially with overwhelmed founders and professionals.

Any agent output that violates these values shall be flagged and withheld pending Steven's review.

---

## Org Structure

Latitude MedTech mirrors a management consulting firm hierarchy.
Steven Tran (Managing Partner / CEO) holds final authority on all outputs.
Claude (Orchestrator) manages sprints, delegates tasks, and enforces QMS.

---

## Consulting Practice Agents

### Senior Manager Tier
| Agent | Role | Status |
|---|---|---|
| Program Manager | Timelines, deliverable tracking, client status | Planned |
| Regulatory Strategy | Cross-market entry, parallel submissions, strategic guidance | Build Phase 1C |

### Manager Tier
| Agent | Role | Status |
|---|---|---|
| FDA Agent | 21 CFR 820/510(k)/PMA/De Novo/EUA | Build only — gated |
| EU MDR Agent | EU MDR 2017/745, IVDR | Build only — gated |
| ISO/MDSAP Agent | ISO 13485:2016, MDSAP | Build only — gated |
| Coaching Brief Agent | Discovery call briefs from LinkedIn/name | Active |
| Content Agent | MedTech Meridian drafts (Substack, LinkedIn) | Active |

### Senior Associate Tier
| Agent | Role | Status |
|---|---|---|
| RAG Ingestion Agent | Crawls FDA/EU guidance, indexes knowledge base | Active |
| Document Generation | SOPs, reports, submission templates | Partial |
| Human Review Agent | Gates all client-facing outputs | Active — LangGraph human-gate + review queue |

### Associate Tier
| Agent | Role | Status |
|---|---|---|
| Voice Assistant | Whisper STT + Piper TTS, real-time queries | Active |
| Disclaimer Agent | Appends disclaimer + label to all outputs | Active — applied at orchestrator finalize |
| Sales Agent | Pipeline, proposals, CRM | Phase 2 |
| Marketing Agent | Content calendar, campaigns | Phase 1B |

### Intern Tier
| Agent | Role | Status |
|---|---|---|
| Research Intern | Background research, data gathering, draft support | Planned |

---

## Business Function Agents

| Function | Agent | Scope | Status |
|---|---|---|---|
| HR | HR Agent | Onboarding, training plans, cert tracking, staff development | Planned |
| Legal | Legal Agent | Contract review, IP, non-compete tracking, compliance flags | Planned |
| Finance | Finance Agent | P&L, invoicing, projections, expense tracking | Planned |
| Sales | Sales Agent | Pipeline, proposals, outreach, CRM | Phase 2 |
| Marketing | Marketing Agent | Brand, campaigns, editorial calendar, content distribution | Phase 1B |

---

## QMS Process Owner Agents (Phase 4)

Governed by 21 CFR Part 820 and ISO 13485 principles, generalized to
firm-wide operations. All gated behind Phase 1 being revenue-generating.

CAPA, Risk Management, Design Controls, Document Control,
Supplier Quality, Complaint Handling, Training, Internal Audit,
Management Review, Production & Process Control.

---

## Trigger Chains

| Event | Chain | Human Gate |
|---|---|---|
| Coaching call scheduled | Coaching Brief → Steven reviews | Always |
| Content request | Content Agent → Steven approves → publish | Always |
| Regulatory query | FDA/EU/ISO → Doc Generation → Human Review → Disclaimer | Always |
| Nonconformance filed | CAPA → Risk → Management Review | Yes — at Mgmt Review |
| Any client-facing output | Agent → Doc Generation → Human Review → Disclaimer → Delivery | Always |
| 3+ errors on any task | RCA initiated → CAPA drafted → Steven approves → agent resumes | Always |

---

## Agent Spawn Protocol

When spawning a subagent, always provide:
- **Role** and owned scope
- **Files** it may read/write
- **Boundaries** — what it must NOT do
- **Acceptance criteria** — what done looks like
- **Reporting format** — what worked, what failed, risks, follow-up

---

## CAPA Protocol

Triggered when any agent or prompt pattern produces 3+ errors.

1. **Detect** — log error count, task context, and output failures
2. **Contain** — halt further work in that task class pending review
3. **RCA** — identify root cause (prompt design, data gap, model limitation, process gap)
4. **CAPA** — draft corrective action (fix now) and preventive action (prevent recurrence)
5. **Steven Review** — CAPA document submitted for approval before agent resumes
6. **Close** — implement actions, verify effectiveness, update relevant rule files
