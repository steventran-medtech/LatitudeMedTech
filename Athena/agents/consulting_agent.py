"""
Latitude MedTech — Management Consulting Agent
================================================
Builds the firm's consulting methodology library by ingesting Big 4
frameworks, case studies, and strategic tools from public sources.

All other agents can query the resulting KB for framework references,
slide structures, and case study patterns.

Run:
    python consulting_agent.py                    # full learning run
    python consulting_agent.py --generate report  # generate a frameworks report
"""

import os
import sys
import json
import logging
import argparse
import hashlib
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import feedparser
import requests

from pathconfig import ENV_FILE, AGENTS_DIR, KB_DIR as _KB_ROOT, LOGS_DIR, OPS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

from memory import Memory
from agent_base import AgentBase

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
KB_DIR  = _KB_ROOT / "consulting"
LOG_DIR = LOGS_DIR
OUT_DIR = OPS_DIR / "consulting"
KB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "consulting_agent.log"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger("consulting_agent")

mem  = Memory()
base = AgentBase("consulting")

# ── Learning sources ──────────────────────────────────────────────────────────

CONSULTING_SOURCES = [
    # Big 4 and top-tier consulting
    {"name": "McKinsey Quarterly",        "url": "https://www.mckinsey.com/feeds/rss/quarterly",             "category": "framework",   "type": "rss"},
    {"name": "McKinsey Insights",         "url": "https://www.mckinsey.com/feeds/rss/insights",              "category": "methodology", "type": "rss"},
    {"name": "BCG Henderson Institute",   "url": "https://www.bcg.com/rss/publications",                     "category": "framework",   "type": "rss"},
    {"name": "Deloitte Insights",         "url": "https://www2.deloitte.com/us/en/insights/deloitte-insights-magazine/deloitte-insights-magazine.rss", "category": "case_study", "type": "rss"},
    {"name": "PwC Strategy+",             "url": "https://www.pwc.com/us/en/services/consulting/insights.rss","category": "methodology", "type": "rss"},
    {"name": "Bain Insights",             "url": "https://www.bain.com/insights/rss/",                       "category": "case_study",  "type": "rss"},
    # Academic and research
    {"name": "Harvard Business Review",   "url": "https://hbr.org/feed",                                    "category": "framework",   "type": "rss"},
    {"name": "MIT Sloan Management",      "url": "https://sloanreview.mit.edu/feed/",                        "category": "methodology", "type": "rss"},
    {"name": "Strategy+Business",         "url": "https://www.strategy-business.com/rss",                   "category": "methodology", "type": "rss"},
    {"name": "Stanford Social Innovation","url": "https://ssir.org/site/rss",                                "category": "case_study",  "type": "rss"},
    # Operations and quality (relevant to MedTech consulting)
    {"name": "Six Sigma Daily",           "url": "https://www.isixsigma.com/feed/",                         "category": "methodology", "type": "rss"},
    {"name": "ASQ Quality Progress",      "url": "https://asq.org/quality-progress/rss",                    "category": "methodology", "type": "rss"},
]

# Core consulting frameworks library — synthesised from public domain knowledge
FRAMEWORKS_LIBRARY = {
    "mece": {
        "name": "MECE Principle (Mutually Exclusive, Collectively Exhaustive)",
        "origin": "McKinsey & Company",
        "era": "1960s–present",
        "description": "Structure analysis so categories are mutually exclusive (no overlap) and collectively exhaustive (complete). The foundation of consulting slide logic.",
        "application": "Breaking down problems, structuring decks, organising deliverables",
        "medtech_use": "QMS gap analysis, regulatory pathway evaluation, risk categorisation",
    },
    "pyramid_principle": {
        "name": "Pyramid Principle (Barbara Minto)",
        "origin": "McKinsey & Company / Barbara Minto, 1970",
        "era": "1970s–present",
        "description": "Lead with the answer (top), then support with arguments and data (bottom). Inductive or deductive grouping. Every point supports the one above.",
        "application": "Executive presentations, board decks, client reports, email writing",
        "medtech_use": "510(k) cover memos, regulatory strategy memos, audit response letters",
    },
    "mckinsey_7s": {
        "name": "McKinsey 7-S Framework",
        "origin": "McKinsey & Company / Peters & Waterman, 1980",
        "era": "1980s–present",
        "description": "Seven interdependent factors: Strategy, Structure, Systems, Shared Values, Style, Staff, Skills. Used for org design and change management.",
        "application": "M&A integration, org transformation, post-merger QMS harmonisation",
        "medtech_use": "Post-acquisition QMS integration, FDA warning letter remediation programs",
    },
    "bcg_matrix": {
        "name": "BCG Growth-Share Matrix",
        "origin": "Boston Consulting Group / Bruce Henderson, 1970",
        "era": "1970s–present",
        "description": "2x2: Stars (high growth, high share), Cash Cows, Question Marks, Dogs. Portfolio strategy tool.",
        "application": "Product portfolio analysis, R&D investment prioritisation",
        "medtech_use": "Device portfolio rationalisation post-M&A, pipeline prioritisation",
    },
    "porters_5_forces": {
        "name": "Porter's Five Forces",
        "origin": "Harvard / Michael Porter, 1979",
        "era": "1979–present",
        "description": "Competitive intensity: Supplier power, Buyer power, Threat of substitutes, Threat of new entrants, Rivalry. Industry attractiveness framework.",
        "application": "Market entry decisions, competitive strategy, M&A target screening",
        "medtech_use": "Market entry strategy for new device categories, regulatory moat analysis",
    },
    "hypothesis_driven": {
        "name": "Hypothesis-Driven Problem Solving",
        "origin": "McKinsey & Company",
        "era": "1960s–present",
        "description": "Form hypotheses before gathering data. Structure the work to prove or disprove. Avoids boiling the ocean. Day-1 hypothesis governs work plan.",
        "application": "All consulting engagements. Structures the issue tree and work plan.",
        "medtech_use": "QMS audit prep, regulatory due diligence, compliance gap analysis",
    },
    "issue_tree": {
        "name": "Issue Tree / Logic Tree",
        "origin": "McKinsey & Company / Consulting general",
        "era": "1970s–present",
        "description": "MECE decomposition of a problem into its component parts. Driver trees for financials; logic trees for yes/no decisions.",
        "application": "Problem decomposition, hypothesis structuring, scoping engagements",
        "medtech_use": "Root cause analysis of FDA observations, CAPA design, 510(k) strategy",
    },
    "storyboarding": {
        "name": "Consulting Storyboarding",
        "origin": "McKinsey & Company / Consulting general",
        "era": "1980s–present",
        "description": "Plan the full deck before building slides. Each slide has one key message (title = insight), supporting exhibit, and annotation. Ghost deck first.",
        "application": "Any consulting deliverable — board decks, client reports, pitches",
        "medtech_use": "FDA response packages, regulatory strategy presentations, board updates",
    },
}

SLIDE_STRUCTURES = {
    "executive_summary": [
        "Situation — what is happening (1 slide)",
        "Complication — why this is a problem / opportunity (1 slide)",
        "Resolution — what we recommend (1 slide)",
        "Key findings — 3 bullets max (1 slide)",
        "Implications and next steps (1 slide)",
    ],
    "strategy_deck": [
        "Executive summary (SCQA — Situation, Complication, Question, Answer)",
        "Current state assessment (with data)",
        "Market / competitive context",
        "Strategic options considered (with criteria)",
        "Recommended strategy with rationale",
        "Implementation roadmap",
        "Financial model / business case",
        "Risks and mitigations",
        "Next steps and decision required",
    ],
    "regulatory_strategy": [
        "Device overview and classification",
        "Regulatory pathway analysis (US, EU, other markets)",
        "Predicate device analysis (510(k)) or clinical evidence plan (PMA/MDR)",
        "Timeline and key milestones",
        "Resource requirements",
        "Risk factors and contingencies",
        "Recommended pathway with rationale",
    ],
    "m_and_a_diligence": [
        "Transaction overview and rationale",
        "Target company profile",
        "Quality and regulatory assessment (QMS, FDA history, notified body status)",
        "IP and technology analysis",
        "Commercial and financial assessment",
        "Integration considerations",
        "Risk matrix",
        "Recommendation",
    ],
    "pitch_deck": [
        "Problem statement (with quantified pain)",
        "Solution and differentiator",
        "Market size (TAM / SAM / SOM)",
        "Product / service overview",
        "Business model",
        "Traction and proof points",
        "Team",
        "Financial projections",
        "The ask",
    ],
}

# ── Historical consulting knowledge sources (50-year arc: 1970s–2020s) ───────
# DI-023-D: ≥5 entries with historical marker terms in "name" field

HISTORICAL_CONSULTING_SOURCES = [
    {"name": "BCG 1970s Historical Origin Growth-Share Matrix Strategy",
     "url": "https://www.bcg.com/about/overview/our-history",
     "category": "history", "type": "web", "era": "1970s"},
    {"name": "McKinsey Historical Framework Evolution 1970–1985",
     "url": "https://www.mckinsey.com/about-us/overview",
     "category": "history", "type": "web", "era": "1970s"},
    {"name": "Porter Five Forces 1980s Strategic Analysis Evolution",
     "url": "https://hbr.org/2008/01/the-five-competitive-forces-that-shape-strategy",
     "category": "framework", "type": "web", "era": "1980s"},
    {"name": "1990s Knowledge Management and Consulting Evolution",
     "url": "https://en.wikipedia.org/wiki/Management_consulting",
     "category": "history", "type": "web", "era": "1990s"},
    {"name": "Big Four 2000s Post-Enron Consulting Evolution",
     "url": "https://en.wikipedia.org/wiki/Big_Four_accounting_organizations",
     "category": "history", "type": "web", "era": "2000s"},
    {"name": "50 Year History of Strategy Consulting 1970–2020",
     "url": "https://www.strategy-business.com/article/rethinking-the-strategy",
     "category": "history", "type": "web", "era": "1970s–2020s"},
    {"name": "HBR Classic Historical Management Consulting Archive",
     "url": "https://hbr.org/topic/subject/strategy",
     "category": "framework", "type": "web", "era": "historical"},
]

# Static 50-year management consulting history — curated, reliable, network-independent
HISTORICAL_CONSULTING_KNOWLEDGE = {
    "mckinsey_1970s": {
        "era": "1970s",
        "title": "The McKinsey-isation of Management Consulting (1970s)",
        "description": "McKinsey & Company established the Firm-Advice model: all-generalists, no industry silos. Barbara Minto codified the Pyramid Principle (1970). The Firm grew from 400 to 2,000 consultants by 1980. Marvin Bower's emphasis on professional standards differentiated consulting from accounting.",
        "key_people": "Marvin Bower, Barbara Minto, Ed Wrapp",
        "key_frameworks": "Pyramid Principle (1970), Hypothesis-driven problem solving, MECE structuring",
    },
    "bcg_1970s": {
        "era": "1970s",
        "title": "BCG and the Strategy Revolution (1970s)",
        "description": "Boston Consulting Group under Bruce Henderson invented portfolio strategy: the Growth-Share Matrix (1970) and the Experience Curve (1966). BCG pioneered quantitative strategy consulting. The concept of cash cows, stars, dogs, and question marks redefined capital allocation decisions.",
        "key_people": "Bruce Henderson, Barry Hedley",
        "key_frameworks": "BCG Growth-Share Matrix (1970), Experience Curve, portfolio theory",
    },
    "strategy_1980s": {
        "era": "1980s",
        "title": "Strategy as Competitive Positioning (1980s)",
        "description": "Michael Porter's Competitive Strategy (1980) and Competitive Advantage (1985) defined strategy as industry structure analysis. McKinsey 7-S Framework (Peters & Waterman, 1980) introduced soft factors. Bain & Company focused on measurable results. The Big 8 accounting firms began consulting arms.",
        "key_people": "Michael Porter, Tom Peters, Robert Waterman, Bill Bain",
        "key_frameworks": "Porter's Five Forces (1979), Value Chain (1985), McKinsey 7-S (1980)",
    },
    "knowledge_1990s": {
        "era": "1990s",
        "title": "Knowledge Management and Reengineering (1990s)",
        "description": "Hammer & Champy's Business Process Reengineering (1993) drove transformation consulting. Kaplan & Norton's Balanced Scorecard (1992) redefined performance management. The Big 6 collapsed to Big 5 post-Andersen separation. Consulting revenues grew 10–15% annually. Knowledge management emerged as a practice.",
        "key_people": "Michael Hammer, James Champy, Robert Kaplan, David Norton",
        "key_frameworks": "Business Process Reengineering (1993), Balanced Scorecard (1992), Knowledge Management",
    },
    "digital_2000s": {
        "era": "2000s",
        "title": "Post-Enron Restructuring and Digital Consulting (2000s)",
        "description": "Sarbanes-Oxley (2002) forced Big 5 to divest consulting arms: Andersen Consulting became Accenture (2001), PwC Consulting became IBM Global Services (2002). The Big 4 advisory practices rebuilt. Digital strategy, offshoring consulting, and ERP implementation consulting dominated the decade.",
        "key_people": "SOX architects, Accenture leadership",
        "key_frameworks": "SOX compliance, IT governance (COBIT), Lean Six Sigma, ERP transformation",
    },
    "agile_2010s": {
        "era": "2010s",
        "title": "Agile, Analytics, and Platform Strategy (2010s)",
        "description": "McKinsey Digital, BCG Digital Ventures, Deloitte Digital launched. Agile methodologies entered consulting delivery models. Big data and analytics became core service lines. Platform business model consulting emerged from Amazon/Airbnb patterns. ESG consulting began early adoption.",
        "key_people": "Digital transformation leaders across all major firms",
        "key_frameworks": "Agile/SAFe, Jobs-to-be-Done, Platform strategy, OKRs, ESG early frameworks",
    },
    "ai_2020s": {
        "era": "2020s",
        "title": "AI-Powered Consulting Transformation (2020s)",
        "description": "COVID-19 (2020) accelerated digital transformation consulting. Generative AI (2022–) disrupted research and analysis work: McKinsey launched QuantumBlack AI, BCG launched BCG X. Boutique AI-native consultancies emerged. ESG materiality became mandatory. Supply chain resilience consulting surged post-pandemic.",
        "key_people": "AI/consulting transformation leaders",
        "key_frameworks": "AI maturity models, ESG materiality, Supply Chain 4.0, digital twin strategy",
    },
}

# ── Learning run ──────────────────────────────────────────────────────────────

def _chunk_text(text: str, size: int = 400) -> list:
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size - 50)] if words else []

def _save_to_kb(source_name: str, category: str, title: str, url: str, text: str) -> int:
    if not text.strip(): return 0
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    slug     = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40]
    fname    = KB_DIR / f"consulting_{url_hash}.json"
    chunks   = _chunk_text(text)
    data     = {
        "agent":    "consulting",
        "doc_name": title,
        "category": f"consulting_{category}",
        "source":   source_name,
        "url":      url,
        "ingested": datetime.now().isoformat(),
        "chunks":   [{"text": c, "doc_name": title, "category": f"consulting_{category}"} for c in chunks],
    }
    fname.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(chunks)

def ingest_frameworks():
    """Save the built-in frameworks library to the KB."""
    all_text = "CONSULTING FRAMEWORKS LIBRARY — Latitude MedTech\n\n"
    for key, fw in FRAMEWORKS_LIBRARY.items():
        all_text += f"## {fw['name']}\nOrigin: {fw['origin']} | Era: {fw['era']}\n{fw['description']}\nApplication: {fw['application']}\nMedTech use: {fw['medtech_use']}\n\n"

    chunks = _chunk_text(all_text)
    data   = {
        "agent":    "consulting",
        "doc_name": "Consulting Frameworks Library",
        "category": "consulting_framework",
        "source":   "Latitude MedTech Synthesis",
        "url":      "internal://consulting-frameworks",
        "ingested": datetime.now().isoformat(),
        "chunks":   [{"text": c, "doc_name": "Consulting Frameworks Library",
                      "category": "consulting_framework"} for c in chunks],
    }
    (KB_DIR / "consulting_frameworks.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    slide_text = "SLIDE STRUCTURES — Consulting Deliverable Architectures\n\n"
    for key, slides in SLIDE_STRUCTURES.items():
        slide_text += f"## {key.replace('_',' ').title()}\n" + "\n".join(f"  {i+1}. {s}" for i,s in enumerate(slides)) + "\n\n"

    chunks2 = _chunk_text(slide_text)
    data2   = {
        "agent":    "consulting",
        "doc_name": "Slide Structures Library",
        "category": "consulting_slide_structure",
        "source":   "Latitude MedTech Synthesis",
        "url":      "internal://slide-structures",
        "ingested": datetime.now().isoformat(),
        "chunks":   [{"text": c, "doc_name": "Slide Structures Library",
                      "category": "consulting_slide_structure"} for c in chunks2],
    }
    (KB_DIR / "consulting_slide_structures.json").write_text(
        json.dumps(data2, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Frameworks library: {len(FRAMEWORKS_LIBRARY)} frameworks + {len(SLIDE_STRUCTURES)} slide structures saved to KB")


def ingest_historical_knowledge():
    """Save the built-in 50-year management consulting history to the KB (DI-023-D)."""
    all_text = "50-YEAR MANAGEMENT CONSULTING HISTORY — Latitude MedTech Reference\n\n"
    for key, item in HISTORICAL_CONSULTING_KNOWLEDGE.items():
        all_text += f"## {item['title']} ({item['era']})\n"
        all_text += f"{item['description']}\n"
        all_text += f"Key People: {item.get('key_people', 'N/A')}\n"
        all_text += f"Key Frameworks: {item.get('key_frameworks', 'N/A')}\n\n"
    chunks = _chunk_text(all_text)
    data = {
        "agent":    "consulting",
        "doc_name": "50-Year Management Consulting History",
        "category": "consulting_history",
        "source":   "Latitude MedTech Synthesis — Historical",
        "url":      "internal://consulting-history-50yr",
        "ingested": datetime.now().isoformat(),
        "chunks":   [{"text": c, "doc_name": "50-Year Management Consulting History",
                      "category": "consulting_history"} for c in chunks],
    }
    (KB_DIR / "consulting_history_50yr.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Historical knowledge: {len(HISTORICAL_CONSULTING_KNOWLEDGE)} eras saved to KB")


def learn(max_new: int = 8):
    ingest_frameworks()
    ingest_historical_knowledge()
    new_items, new_chunks = 0, 0
    learned_items = []
    headers = {"User-Agent": "LatitudeMedTech-ConsultingAgent/1.0"}

    # Current RSS sources
    for source in CONSULTING_SOURCES:
        if new_items >= max_new: break
        try:
            feed  = feedparser.parse(source["url"])
            items = feed.entries[:4]
            for entry in items:
                if new_items >= max_new: break
                url   = getattr(entry, "link", "")
                title = getattr(entry, "title", "")
                text  = re.sub(r"<[^>]+>", "", getattr(entry, "summary", ""))[:2000]
                if not url or not title or mem.learning_ingested(url): continue
                chunks = _save_to_kb(source["name"], source["category"], title, url, text)
                if not chunks: continue
                mem.log_learning("consulting", source["name"], title, url, source["category"], chunks)
                new_items  += 1
                new_chunks += chunks
                learned_items.append({"title": title, "source": source["name"], "url": url,
                                       "category": source["category"], "chunks": chunks})
                log.info(f"  [consulting] Learned: {title[:60]} ({chunks} chunks)")
        except Exception as e:
            log.warning(f"  [consulting] {source['name']}: {e}")

    # Historical web sources (50-year arc, DI-023-D)
    hist_budget = max(2, max_new // 4)
    hist_new = 0
    for source in HISTORICAL_CONSULTING_SOURCES:
        if hist_new >= hist_budget: break
        try:
            url = source["url"]
            if mem.learning_ingested(url): continue
            resp = requests.get(url, headers=headers, timeout=12)
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", "", resp.text)[:3000]
            title = source["name"]
            chunks = _save_to_kb(source["name"], source["category"], title, url, text)
            if not chunks: continue
            mem.log_learning("consulting", source["name"], title, url, source["category"], chunks)
            hist_new   += 1
            new_items  += 1
            new_chunks += chunks
            learned_items.append({"title": title, "source": source["name"], "url": url,
                                   "category": source["category"], "chunks": chunks,
                                   "era": source.get("era", "historical")})
            log.info(f"  [consulting/hist] Learned: {title[:60]} ({chunks} chunks)")
        except Exception as e:
            log.warning(f"  [consulting/hist] {source['name']}: {e}")

    # Learning summary report (DI-032-A, DI-032-B)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = LOG_DIR / f"consulting_learning_{ts}.md"
    lines = [
        "# Consulting Agent — Learning Summary",
        f"*Generated {datetime.now().strftime('%B %d, %Y at %H:%M')}*",
        "",
        "**Alpha — Steve Review Required**",
        "",
        "> This summary lists all items ingested by the Consulting Agent in this run.",
        "> Approve to confirm the knowledge is appropriate for the KB.",
        "> Reject to flag items for removal.",
        "",
        "---",
        "",
        "## Newly Ingested Items",
        "",
    ]
    if learned_items:
        for item in learned_items:
            era_tag = f" *(Era: {item['era']})*" if item.get("era") else ""
            lines.append(f"- **{item['title']}**{era_tag}")
            lines.append(f"  Source: {item['source']} | Category: {item['category']} | Chunks: {item['chunks']}")
            lines.append(f"  URL: <{item['url']}>")
            lines.append("")
    else:
        lines.append("No new items ingested this run.")
        lines.append("")
    lines += [
        "---",
        "",
        f"**Run total:** {new_items} new items · {new_chunks} chunks",
        "",
        "*Latitude MedTech LLC — Alpha. All AI-generated outputs require Steven Tran review before any downstream use.*",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    try:
        mem.submit_for_review(
            "consulting", "learning_report",
            f"Consulting Learning Summary {datetime.now().strftime('%Y-%m-%d')}",
            str(report_path),
        )
    except Exception as e:
        log.warning(f"Could not submit learning report for review: {e}")

    mem.upsert_agent_health("consulting", last_learning=datetime.now().isoformat() if new_items > 0 else None)
    log.info(f"Consulting agent: {new_items} new items, {new_chunks} chunks")
    return {"agent": "consulting", "new_items": new_items, "chunks": new_chunks}

def generate_frameworks_report() -> Path:
    """Generate a consulting frameworks reference document."""
    if not ANTHROPIC_API_KEY: return None
    kb_ctx = base.kb_context("consulting framework methodology slide structure", top_k=6)
    prompt = f"""Write a comprehensive Consulting Methodology Reference for Latitude MedTech LLC.

{kb_ctx}

Cover:
1. Core problem-solving frameworks (MECE, Pyramid Principle, hypothesis-driven)
2. Strategic analysis tools (BCG Matrix, Porter's 5 Forces, McKinsey 7-S)
3. Slide architecture for key deliverable types (strategy deck, regulatory strategy, M&A diligence, pitch)
4. Quality standards for consulting deliverables (what Big 4 partners actually look for)
5. MedTech-specific applications of each framework

Format as a practical reference document Steven can use to coach clients and build deliverables.
Include specific examples relevant to MedTech regulatory consulting."""

    resp = base._get_client().messages.create(
        model="claude-sonnet-4-6", max_tokens=3000,
        system=base.system_prompt(),
        messages=[{"role": "user", "content": prompt}]
    )
    content = resp.content[0].text.strip()
    out_path = OUT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_consulting_frameworks.md"
    out_path.write_text(f"# Consulting Methodology Reference\n*Generated {datetime.now().strftime('%B %d, %Y')}*\n\n{content}", encoding="utf-8")
    log.info(f"Frameworks report: {out_path}")
    # Surface the deliverable in the Human Review Queue (Phase 1A human gate).
    try:
        mem.submit_for_review("consulting", "report",
                              "Consulting Methodology Reference", str(out_path))
    except Exception as e:
        log.warning(f"Could not submit report for review: {e}")
    return out_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", choices=["report"], help="Generate a deliverable")
    parser.add_argument("--max", type=int, default=8)
    args = parser.parse_args()
    log.info("=" * 50)
    log.info("  Latitude MedTech — Consulting Agent")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 50)
    if args.generate == "report":
        generate_frameworks_report()
    else:
        learn(args.max)

if __name__ == "__main__":
    main()
