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

load_dotenv(Path.home() / "Athena" / "voice" / ".env")
sys.path.insert(0, str(Path.home() / "Athena" / "agents"))

from memory import Memory
from agent_base import AgentBase

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
KB_DIR   = Path.home() / "Athena" / "knowledge_base" / "consulting"
LOG_DIR  = Path.home() / "Athena" / "logs"
OUT_DIR  = Path.home() / "Athena" / "ops" / "consulting"
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

def learn(max_new: int = 8):
    ingest_frameworks()
    new_items, new_chunks = 0, 0
    headers = {"User-Agent": "LatitudeMedTech-ConsultingAgent/1.0"}

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
                log.info(f"  [consulting] Learned: {title[:60]} ({chunks} chunks)")
        except Exception as e:
            log.warning(f"  [consulting] {source['name']}: {e}")

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
