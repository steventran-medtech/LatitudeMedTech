"""
Latitude MedTech — Agent Base
================================
Shared utilities for all agents:
- Load agent context from .claude/agents/<name>.md
- KB-first query helper (search before calling Claude API)
- Standardised system prompt builder
- Memory logging

Usage:
    from agent_base import AgentBase
    base = AgentBase("content")
    system = base.system_prompt("Write a draft about CAPA")
    kb_ctx = base.kb_context("CAPA corrective action")
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from pathconfig import ATHENA_ROOT, ENV_FILE, AGENTS_DIR, RULES_DIR, CLAUDE_MD

load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

# Shared memory + KB
try:
    from memory import Memory
    _mem = Memory()
except Exception:
    _mem = None

try:
    from kb_query import KBQuery
    _kb = KBQuery()
except Exception:
    _kb = None


# 50-year domain evolution summaries injected into every agent's system prompt.
# Kept concise (~120 chars each) so they add context without bloating token count.
HISTORICAL_CONTEXT = {
    "fda": (
        "FDA device regulation evolved: 1976 MDA (first framework) → 1990 SMDA (MDR reporting) "
        "→ 1997 FDAMA (510k reforms) → 2012 FDASIA (breakthrough devices) → 2016 21st Century Cures "
        "(De Novo). Oversight shifted from minimal pre-market review to risk-tiered clearance with "
        "real-time post-market surveillance."
    ),
    "iso": (
        "QMS evolved: 1987 ISO 9001 first edition → 1996 ISO 13485 (medical devices) → 2003 "
        "risk-alignment → 2016 ISO 13485:2016 (risk-based thinking) → 2019 ISO 14971:2019. "
        "Approach shifted from inspection-based to process-based to risk-based management."
    ),
    "coaching": (
        "MedTech careers evolved: 1976–1990 RA profession emerged post-MDA → 2000 RAC credential "
        "established → 2010s hybrid RA/engineering roles (combination products, digital health) "
        "→ 2020s AI reshaping compliance and quality roles. Demand for strategic, cross-functional "
        "professionals has consistently grown."
    ),
    "consulting": (
        "Management consulting evolved: 1970s BCG Growth-Share Matrix, McKinsey 7S → 1980 Porter "
        "Five Forces → 1990s Six Sigma/Lean → 2000s Balanced Scorecard, Blue Ocean → 2010s digital "
        "transformation → 2020s AI-augmented delivery. Small firms can now match Big 4 output quality."
    ),
    "ma_intelligence": (
        "MedTech M&A evolved: 1970s–80s fragmented industry → 1990s serial acquirers emerge "
        "(Medtronic, J&J, Stryker) → 2000s mega-mergers → 2010s digital health bolt-ons → 2020s PE "
        "rollups and COVID-driven divestitures. QARA integration failure has been a persistent deal "
        "risk across all eras."
    ),
    "briefing": (
        "Regulatory landscape evolved: 1976 MDA (US only) → 1990 MDR mandatory reporting → "
        "2012 IMDRF (global harmonization) → 2017 EU MDR 2017/745 enacted → 2021 EU MDR mandatory. "
        "Monitoring now requires simultaneous coverage of FDA, EU MDR, IMDRF, and national CAs."
    ),
    "content": (
        "MedTech content channels evolved: 1980s trade journals dominated → 2000s web publishing "
        "and early newsletters → 2010s LinkedIn/blogs for practitioners → 2020s Substack and podcast "
        "circuit. Practitioner-authored newsletters now consistently outperform trade publications "
        "for RA/QA audience reach."
    ),
    "rag": (
        "AI/RAG evolved: 1974 MYCIN expert system → 1987 backpropagation → 1990s SVM and "
        "statistical NLP → 2017 Transformer architecture → 2020 GPT-3 + early RAG → 2023–25 "
        "hybrid vector/keyword retrieval as enterprise standard. Grounded generation replaced "
        "hallucination-prone zero-shot LLM responses."
    ),
    "voice_bridge": (
        "Voice AI evolved: 1970s DARPA SUR project → 1990 Dragon Dictate (HMM ASR) → 2000s "
        "Nuance commercial ASR → 2011 Siri (consumer wake word) → 2018 BERT → 2022 Whisper "
        "(neural ASR) + neural TTS (Kokoro, ElevenLabs). Voice has matured from isolated-word "
        "recognition to streaming, contextual, multi-turn conversation."
    ),
    "eu_mdr": (
        "EU device regulation evolved: 1993 MDD 93/42/EEC (CE marking) → 2007 IVDD revision "
        "→ 2017 EU MDR 2017/745 enacted (risk reclassification, UDI, PMCF) → 2021 mandatory "
        "→ 2024–25 transition extensions (notified body capacity). PMCF and real-world evidence "
        "requirements represent the largest post-market shift since MDD."
    ),
    "hr": (
        "HR evolved: 1970s Personnel departments → 1980s Strategic HR (Ulrich model) → 1990s "
        "competency frameworks and 360-degree feedback → 2000s talent management systems "
        "→ 2010s people analytics → 2020s AI agent oversight and remote-first workforce models. "
        "Performance management shifted from annual reviews to continuous feedback loops."
    ),
    "marketing": (
        "B2B MedTech marketing evolved: 1976–1990 trade shows and print → 2000s web presence "
        "and SEO → 2010s LinkedIn content marketing and thought leadership → 2020s Substack "
        "newsletters and podcast circuit. Practitioner-authored content now drives more qualified "
        "pipeline than traditional trade advertising."
    ),
    "deck": (
        "Consulting deck craft evolved: 1970s BCG/McKinsey pioneered executive slide format "
        "→ 1987 Minto Pyramid Principle published → 1990s MECE/SCQA as standard → 2000s data "
        "visualization emphasis → 2010s single-idea-per-slide discipline → 2020s AI-assisted "
        "generation. The core standard — lead with recommendation, support with evidence — "
        "has held for 50 years."
    ),
}


PUBLICATION_FORMAT_GUIDE = {
    "briefing": (
        "## Publication Format — MedTech Dive Editorial Standard\n"
        "Structure every briefing output as MedTech Dive-style editorial:\n"
        "- Inverted-pyramid lead: most newsworthy fact in the first sentence\n"
        "- Sections: Lead | Context | Regulatory Implications | So What (for Steven)\n"
        "- No passive voice; use active attribution ('FDA said', 'Medtronic confirmed')\n"
        "- Every claim requires a source citation inline (e.g., 'per FDA.gov, 2026-06-07')\n"
        "- Under 600 words for daily briefings; under 1,200 for deep-dive intelligence\n"
        "- Headline: specific, not generic ('FDA Issues Warning Letter to Boston Scientific CGM Line',"
        " not 'FDA Takes Action')"
    ),
    "ma_intelligence": (
        "## Publication Format — MedTech Dive + McKinsey Hybrid\n"
        "Structure M&A intelligence as a hybrid of MedTech Dive news and McKinsey deal analysis:\n"
        "- Lead with the deal headline and one-sentence strategic rationale\n"
        "- Sections: Deal Overview | Strategic Rationale | QARA Assessment | Historical Pattern | So What\n"
        "- QARA section must be specific: name the devices, certificates, and quality system impact\n"
        "- Pattern section: reference at least one comparable deal from the 50-year arc\n"
        "- Close with 2-3 implications for Latitude MedTech's advisory positioning\n"
        "- Source all financial figures with SEC filing or press release citation"
    ),
    "content": (
        "## Publication Format — Harvard Business Review Executive Standard\n"
        "Structure all content as HBR-quality practitioner writing:\n"
        "- Open with a provocative insight or counterintuitive observation (not background)\n"
        "- Sections: Hook | The Problem | The Framework | The Takeaway | Call to Action\n"
        "- Use the 'manager test': every paragraph must answer 'so what does this mean for me'\n"
        "- Substack: 600-1,000 words with 3-5 subheadings; LinkedIn: 150-300 words single scroll\n"
        "- No jargon without definition; no acronyms on first use\n"
        "- End with one specific action the reader can take this week"
    ),
    "coaching": (
        "## Publication Format — Harvard Business Review Executive Coaching Standard\n"
        "Structure all coaching briefs as HBR-quality coaching documentation:\n"
        "- Sections: Background | Stated Goal | Strategic Context | Talking Points |"
        " Probing Questions | Recommended Next Steps\n"
        "- Talking Points: 3-5 bullets, actionable and specific to this client\n"
        "- Questions: open-ended, designed to surface unspoken constraints\n"
        "- Next Steps: sequenced and time-bound (e.g., 'within 2 weeks: ...')\n"
        "- Write in Steve's voice: direct, experienced, practitioner-level; no generic career advice"
    ),
    "consulting": (
        "## Publication Format — McKinsey Pyramid Principle (SCQA)\n"
        "Structure all consulting deliverables using the McKinsey Pyramid Principle:\n"
        "- SCQA frame: Situation -> Complication -> Question -> Answer (lead with the answer)\n"
        "- Executive summary first: 3-4 sentences stating the recommendation and primary rationale\n"
        "- MECE structure: every section mutually exclusive, collectively exhaustive\n"
        "- Sections: Executive Summary | Situation | Key Findings | Recommendation | Next Steps\n"
        "- Length: 800-2,000 words for strategy memos; 400-600 for weekly deliverables"
    ),
    "deck": (
        "## Publication Format — McKinsey Single-Idea-Per-Slide Discipline\n"
        "Structure all slide content using McKinsey's proven standard:\n"
        "- One insight per slide: the headline IS the conclusion, not a descriptor\n"
        "- Pyramid Principle: answer-first -> supporting evidence -> data\n"
        "- SCQA narrative arc across the full deck\n"
        "- Headline format: action-oriented insight ('Revenue stalls without QARA upgrade')\n"
        "- 3-5 bullets max per slide; never exceed one concept per bullet\n"
        "- Every data chart must have an insight headline above it"
    ),
    "sow": (
        "## Publication Format — McKinsey Engagement Letter Standard\n"
        "Structure all SOWs using McKinsey engagement standard:\n"
        "- Lead with scope, deliverables, and success criteria - not background\n"
        "- Sections: Engagement Objective | Scope of Work | Deliverables | Timeline |"
        " Assumptions | Fees\n"
        "- Each deliverable: specific, measurable, reviewer-assignable\n"
        "- Timeline: milestone table with owner and acceptance criteria per milestone\n"
        "- No ambiguous language: exact commitments or explicit ranges required\n"
        "- Alpha label and disclaimer on every draft"
    ),
    "regulatory_strategy": (
        "## Publication Format — PwC Regulatory Advisory Standard\n"
        "Structure all regulatory strategy documents as PwC-quality advisory:\n"
        "- Executive Summary first: regulatory pathway, timeline, top 3 risks\n"
        "- Sections: Regulatory Classification | Pathway Analysis | Risk Register |"
        " Timeline | Action Plan\n"
        "- Risk Register: each risk rated Likelihood x Impact; mitigation owner named\n"
        "- Cite FDA guidance documents and ISO standards by full title and date\n"
        "- Flag all judgment call areas explicitly\n"
        "- Alpha label and RAC review gate clearly marked on every output"
    ),
    "iso_coach": (
        "## Publication Format — PwC Quality Advisory Standard\n"
        "Structure all ISO/QMS advisory outputs as PwC-quality advisory:\n"
        "- Lead with the audit risk classification: Critical / Major / Minor\n"
        "- Sections: Clause Reference | Current State | Gap | Risk Level |"
        " Recommended Action | Verification\n"
        "- Every gap statement is specific to the client's system - not generic\n"
        "- Recommended actions sequenced: immediate (0-30 days) / near-term (30-90 days) /"
        " strategic (90+ days)\n"
        "- Reference ISO clause numbers specifically (e.g., §7.3.2 Design Controls)\n"
        "- Alpha label and RAC review gate on every output"
    ),
    "qms_simulator": (
        "## Publication Format — PwC Quality Advisory Standard (Training Use)\n"
        "Structure all QMS simulator outputs as PwC-quality mock audit documentation:\n"
        "- DHR/DMR format: ISO 13485:2016 section references on every document header\n"
        "- CAPA records: 5-Why root cause, risk rating, corrective action,"
        " verification method, owner\n"
        "- Risk Management: ISO 14971 table - hazard, severity, probability, RPN, control\n"
        "- SOP references: clause-mapped; every SOP traceable to a standard requirement\n"
        "- Training records: competency-based, with assessment criteria and sign-off fields\n"
        "- DISCLAIMER on every document: fictional for mock audit training only"
    ),
    "marketing": (
        "## Publication Format — Harvard Business Review Practitioner Plan\n"
        "Structure all marketing plans and briefs as HBR-quality practitioner documents:\n"
        "- Lead with the strategic objective and 30-day priority action\n"
        "- Tactic scorecard table: Tactic | Mobility | Cost | Hours/Week | Expected Output\n"
        "- Remote/zero-cost tactics sorted to the top\n"
        "- Sections: Objective | Tactic Scorecard | Weekly Plan | Metrics | Future Pipeline\n"
        "- Every tactic tagged: Remote / Local / [DEFERRED]\n"
        "- Future Pipeline: deferred tactics with explicit unlock triggers"
    ),
}


class AgentBase:
    def __init__(self, agent_name: str):
        self.name    = agent_name
        self._ctx    = None   # lazy-loaded context file
        self._claude = None   # lazy anthropic client
        self._firm_ctx_cache = {}   # cache firm_context reads (file rarely changes)

    # ── Context file ──────────────────────────────────────────────────────────

    def context_file(self) -> str:
        """Load agent persona from .claude/agents/<name>[-agent].md."""
        if self._ctx is not None:
            return self._ctx
        for fname in [f"{self.name}.md", f"{self.name}-agent.md"]:
            f = RULES_DIR / fname
            if f.exists():
                self._ctx = f.read_text(encoding="utf-8")
                return self._ctx
        self._ctx = ""
        return self._ctx

    def historical_framing(self) -> str:
        """Return the 50-year domain evolution summary for this agent, or empty string."""
        return HISTORICAL_CONTEXT.get(self.name, "")

    def firm_context(self, sections=("## Core Values", "## North Star")) -> str:
        """Extract relevant sections from CLAUDE.md for prompt grounding."""
        if sections in self._firm_ctx_cache:
            return self._firm_ctx_cache[sections]
        if not CLAUDE_MD.exists():
            return ""
        raw = CLAUDE_MD.read_text(encoding="utf-8")
        parts = []
        for section in sections:
            start = raw.find(section)
            if start != -1:
                end = raw.find("\n## ", start + 1)
                parts.append(raw[start: end if end != -1 else start + 500])
        self._firm_ctx_cache[sections] = "\n".join(parts)
        return self._firm_ctx_cache[sections]

    # ── KB context ────────────────────────────────────────────────────────────

    def kb_context(self, query: str, top_k: int = 4, max_chars: int = 2500) -> str:
        """Search local KB. Returns formatted context string or empty string."""
        if not _kb or not _kb.has_content():
            return ""
        chunks = _kb.search(query, top_k=top_k)
        return _kb.format_context(chunks, max_chars=max_chars)

    def has_kb(self) -> bool:
        return _kb is not None and _kb.has_content()

    def central_kb_context(self, query: str, top_k: int = 8, max_chars: int = 4000) -> str:
        """
        Query the CENTRAL KB across ALL agent categories.
        Use this for complex tasks that benefit from multi-domain knowledge:
        consulting frameworks + regulatory knowledge + M&A patterns + industry data.
        """
        if not _kb or not _kb.has_content():
            return ""
        chunks = _kb.search(query, top_k=top_k)   # searches all categories
        return _kb.format_context(chunks, max_chars=max_chars)

    # ── System prompt builder ─────────────────────────────────────────────────

    def system_prompt(self, task_context: str = "", include_kb: str = "") -> str:
        """
        Build a complete system prompt:
          firm values + agent persona + 50-year historical context + task context + KB grounding
        """
        parts = [
            "You are an AI agent for Latitude MedTech LLC, a MedTech and Pharma "
            "management consulting firm in San Diego, CA. "
            "You serve Steven Tran, Managing Partner and CEO.\n",
            self.firm_context(),
            "\n## Your Role\n",
            self.context_file(),
        ]
        hist = self.historical_framing()
        if hist:
            parts.append(
                f"\n## Domain Evolution — 50-Year Context\n"
                f"You understand how your domain has evolved over the past 50 years. "
                f"When answering questions or producing deliverables, draw on this historical "
                f"context to show how far the field has come and where current practice sits "
                f"on that arc:\n{hist}"
            )
        fmt = PUBLICATION_FORMAT_GUIDE.get(self.name)
        if fmt:
            parts.append(f"\n{fmt}")
        if task_context:
            parts.append(f"\n## Current Task\n{task_context}")
        if include_kb:
            parts.append(f"\n## Knowledge Base Context\n{include_kb}")
        parts.append(
            "\n\nALWAYS append this disclaimer to any client-facing output:\n"
            "\"DISCLAIMER: This output is produced by Latitude MedTech LLC for "
            "educational and planning purposes only. Not regulatory or legal advice.\"\n"
            "Label all outputs: Alpha — Steve Review Required."
        )
        return "\n".join(parts)

    # ── Claude API helper ─────────────────────────────────────────────────────

    def _get_client(self):
        if self._claude is None:
            import anthropic
            self._claude = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        return self._claude

    def ask(self, prompt: str, system: str = "", model: str = "claude-haiku-4-5",
            max_tokens: int = 1000) -> str:
        """
        Call Claude with KB-grounded system prompt.
        Uses haiku for speed/cost unless explicitly overridden.
        """
        client = self._get_client()
        if not system:
            system = self.system_prompt()
        resp = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = resp.content[0].text.strip()
        if _mem:
            _mem.log_api_call(
                self.name, model,
                resp.usage.input_tokens, resp.usage.output_tokens,
                purpose=f"{self.name}_ask",
            )
        return answer

    # ── Memory helpers ────────────────────────────────────────────────────────

    def log(self, action: str, subject: str = "", metadata: dict = None):
        if _mem:
            _mem.log_event(self.name, action, subject=subject, metadata=metadata)

    def log_api(self, model, input_tok, output_tok, purpose=""):
        if _mem:
            _mem.log_api_call(self.name, model, input_tok, output_tok, purpose=purpose)
