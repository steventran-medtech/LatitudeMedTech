"""
Latitude MedTech — M&A Intelligence Agent
==========================================
Tracks, analyses, and synthesises MedTech/Pharma/Life Sciences M&A activity.
Historical scope: 50 years (1976 Medical Device Act → present).

Builds a deal intelligence KB that all other agents can query for:
  — Deal context and precedents
  — QARA implications of M&A
  — Success/failure patterns
  — Regulatory consequences post-merger

Run:
    python ma_intelligence_agent.py              # learning run
    python ma_intelligence_agent.py --analyse    # generate deal analysis report
    python ma_intelligence_agent.py --historical # historical deep-dive
"""

import os
import sys
import json
import logging
import argparse
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import feedparser

load_dotenv(Path.home() / "Athena" / "voice" / ".env")
sys.path.insert(0, str(Path.home() / "Athena" / "agents"))

from memory import Memory
from agent_base import AgentBase

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
BRAVE_API_KEY     = os.getenv("BRAVE_API_KEY", "")
KB_DIR   = Path.home() / "Athena" / "knowledge_base" / "ma"
LOG_DIR  = Path.home() / "Athena" / "logs"
OUT_DIR  = Path.home() / "Athena" / "ops" / "ma_intelligence"
KB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "ma_intelligence_agent.log"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger("ma_intelligence")

mem  = Memory()
base = AgentBase("ma_intelligence")

# ── Current M&A news sources ──────────────────────────────────────────────────

MA_SOURCES = [
    {"name": "BioPharma Dive",         "url": "https://www.biopharmadive.com/feeds/news/",    "category": "deal_news"},
    {"name": "MedTech Dive",           "url": "https://www.medtechdive.com/feeds/news/",       "category": "deal_news"},
    {"name": "Fierce Biotech",         "url": "https://www.fiercebiotech.com/rss/xml",         "category": "deal_news"},
    {"name": "Fierce MedTech",         "url": "https://www.fiercemedtech.com/rss/xml",         "category": "deal_news"},
    {"name": "STAT News",              "url": "https://www.statnews.com/feed/",                "category": "deal_analysis"},
    {"name": "MedCity News",           "url": "https://medcitynews.com/feed/",                 "category": "deal_news"},
    {"name": "Reuters Healthcare",     "url": "https://feeds.reuters.com/reuters/healthNews",  "category": "deal_news"},
    {"name": "McKinsey Healthcare",    "url": "https://www.mckinsey.com/feeds/rss/healthcare", "category": "deal_analysis"},
    {"name": "Evaluate Vantage",       "url": "https://www.evaluate.com/vantage/rss",          "category": "deal_analysis"},
    {"name": "BCG Healthcare",         "url": "https://www.bcg.com/rss/healthcare",            "category": "deal_analysis"},
    {"name": "Deloitte Life Sciences", "url": "https://www2.deloitte.com/us/en/insights/industry/life-sciences/life-sciences-insights.rss", "category": "industry_analysis"},
]

# ── Historical deal knowledge base (synthesised from public record) ───────────

LANDMARK_DEALS = [
    {
        "acquirer": "Medtronic", "target": "Covidien",
        "year": 2015, "value_bn": 49.9, "type": "Acquisition",
        "rationale": "Tax inversion + diversification into hospital products",
        "qara_impact": "Major QMS integration challenge — two different regulatory frameworks. Covidien had strong EU MDR compliance; Medtronic had FDA-first culture. Required 3-year harmonisation program.",
        "outcome": "Successfully integrated but took longer than projected. Some product line rationalisation.",
        "lessons": "M&A of this scale requires dedicated QMS integration team day-1. Regulatory pathway transitions need 18+ months planning.",
    },
    {
        "acquirer": "Abbott", "target": "St. Jude Medical",
        "year": 2017, "value_bn": 25.0, "type": "Acquisition",
        "rationale": "Strengthen cardiovascular and neuromodulation portfolio",
        "qara_impact": "St. Jude had several open FDA warning letters at close. Abbott had to inherit and remediate. Cardiac rhythm management products had supply chain quality issues.",
        "outcome": "Integration largely successful. Cybersecurity vulnerabilities in legacy St. Jude devices required costly post-merger patching under FDA oversight.",
        "lessons": "Pre-close regulatory due diligence must include: open warning letters, 483 history, ongoing FDA correspondence, product cybersecurity status.",
    },
    {
        "acquirer": "J&J (DePuy)", "target": "Synthes",
        "year": 2012, "value_bn": 21.3, "type": "Acquisition",
        "rationale": "Expand orthopaedic trauma and spine portfolio",
        "qara_impact": "Synthes was under DOJ investigation for off-label promotion at close. J&J inherited $22.2M criminal fine. QMS integration complex across 50+ countries.",
        "outcome": "Eventually successful. Now DePuy Synthes is #1 ortho player globally. But regulatory and legal tail took 5+ years to clear.",
        "lessons": "Off-label use investigations are acquirer's problem post-close. Legal due diligence must include DOJ/OIG correspondence.",
    },
    {
        "acquirer": "Stryker", "target": "Wright Medical",
        "year": 2020, "value_bn": 4.0, "type": "Acquisition",
        "rationale": "Expand extremities and biologics portfolio",
        "qara_impact": "Wright had significant product recall history (metal-on-metal hip failures). Stryker absorbed recall liability and had to remediate supply chain quality.",
        "outcome": "Integration ongoing. Extremities franchise performing well but recall tail still being worked.",
        "lessons": "Recall history is not a deal-breaker but must be fully priced in. Post-merger recall management requires dedicated team.",
    },
    {
        "acquirer": "BD", "target": "Bard",
        "year": 2017, "value_bn": 24.0, "type": "Acquisition",
        "rationale": "Transform BD into a diversified medical technology company",
        "qara_impact": "Bard had extensive pelvic mesh litigation. BD inherited $3.9B in settlement costs. Quality systems integration took 3+ years.",
        "outcome": "BD transformed successfully but litigation tail was severe. QMS harmonisation required significant investment.",
        "lessons": "Litigation history (not just regulatory) must be fully diligenced. Mass tort exposure in medical devices can be existential.",
    },
]

QARA_MA_FRAMEWORKS = {
    "pre_close_diligence": [
        "FDA inspection history — any 483s, warning letters, consent decrees in last 5 years",
        "EU MDR / IVDR compliance status — notified body certificates, technical file status",
        "ISO 13485 certificate status — current, suspended, or expired",
        "MDSAP participation and audit history",
        "Open recalls and MDRs (mandatory device reports)",
        "Off-label promotion investigations (DOJ, OIG correspondence)",
        "Product liability litigation and mass tort exposure",
        "Supply chain audit status — critical supplier qualification",
        "Design history files — completeness, gaps",
        "Clinical data quality — study integrity, data management",
    ],
    "post_close_integration": [
        "Assign single QMS integration leader day-1",
        "Gap analysis between acquirer and target QMS within 90 days",
        "Regulatory pathway transitions — 510(k) ownership transfers, CE mark transitions",
        "ISO 13485 scope expansion — updated certificate to include acquired entities",
        "CAPA harmonisation — unified CAPA process, open CAPAs remediated",
        "Document control harmonisation — SOPs, work instructions, controlled documents",
        "Training — all employees on acquirer QMS within 6 months",
        "Supplier qualification — acquired suppliers re-qualified under acquirer standards",
    ],
    "failure_patterns": [
        "Closing before open FDA warning letter is remediated",
        "Underestimating litigation tail (mesh, hip, spine)",
        "Assuming target's QMS is 'good enough' without audit",
        "Failing to budget for QMS integration (typical: 1-3% of deal value)",
        "Ignoring off-label promotion culture in acquired sales force",
        "Not planning regulatory pathway transitions before close",
        "Two different ERP/QMS systems running in parallel too long",
    ],
}

# ── Historical search queries (50-year scope) ─────────────────────────────────

def get_historical_queries():
    year = datetime.now().year
    return [
        # Current deals
        f"MedTech medical device merger acquisition {year}",
        f"pharma life sciences M&A deal {year}",
        # Historical patterns
        "medical device industry merger history 1990s 2000s",
        "pharmaceutical acquisition QARA regulatory implications 50 years",
        "FDA warning letter post-merger medical device history",
        "medical device recall post-acquisition integration failure",
        "Medtronic Stryker BD Abbott acquisition history regulatory",
        # QARA-specific
        "QMS integration failure medical device merger",
        "ISO 13485 acquisition integration challenge",
        "FDA consent decree medical device company acquisition",
    ]

# ── Brave search helper ───────────────────────────────────────────────────────

def _brave_search(query: str, count: int = 5) -> list:
    if not BRAVE_API_KEY: return []
    try:
        import requests
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY},
            params={"q": query, "count": count},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json().get("web", {}).get("results", [])
    except Exception: pass
    return []

# ── KB save helper ─────────────────────────────────────────────────────────────

def _chunk(text: str, size: int = 400) -> list:
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size - 50)] if words else []

def _save_to_kb(source: str, category: str, title: str, url: str, text: str) -> int:
    if not text.strip(): return 0
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    fname    = KB_DIR / f"ma_{url_hash}.json"
    chunks   = _chunk(text)
    data     = {
        "agent":    "ma_intelligence",
        "doc_name": title,
        "category": f"ma_{category}",
        "source":   source,
        "url":      url,
        "ingested": datetime.now().isoformat(),
        "chunks":   [{"text": c, "doc_name": title, "category": f"ma_{category}"} for c in chunks],
    }
    fname.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(chunks)

def ingest_landmark_deals():
    """Save the built-in landmark deals library to the KB."""
    text = "LANDMARK M&A DEALS — MedTech QARA Intelligence Library\n\n"
    for deal in LANDMARK_DEALS:
        text += (
            f"## {deal['acquirer']} / {deal['target']} ({deal['year']}) — ${deal['value_bn']}B\n"
            f"Rationale: {deal['rationale']}\n"
            f"QARA Impact: {deal['qara_impact']}\n"
            f"Outcome: {deal['outcome']}\n"
            f"Lessons: {deal['lessons']}\n\n"
        )
    text += "\n\nQARA M&A FRAMEWORKS:\n\n"
    for key, items in QARA_MA_FRAMEWORKS.items():
        text += f"### {key.replace('_',' ').title()}\n" + "\n".join(f"- {i}" for i in items) + "\n\n"

    chunks = _chunk(text)
    data   = {
        "agent":    "ma_intelligence",
        "doc_name": "Landmark M&A Deals & QARA Frameworks",
        "category": "ma_landmark_deals",
        "source":   "Latitude MedTech Synthesis",
        "url":      "internal://ma-landmark-deals",
        "ingested": datetime.now().isoformat(),
        "chunks":   [{"text": c, "doc_name": "Landmark M&A Deals", "category": "ma_landmark_deals"} for c in chunks],
    }
    (KB_DIR / "ma_landmark_deals.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Landmark deals: {len(LANDMARK_DEALS)} deals + frameworks saved to KB")

# ── Main learning run ─────────────────────────────────────────────────────────

def learn(max_new: int = 8, historical: bool = False):
    ingest_landmark_deals()
    new_items, new_chunks = 0, 0

    # Current news sources
    for source in MA_SOURCES:
        if new_items >= max_new: break
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:4]:
                if new_items >= max_new: break
                url   = getattr(entry, "link", "")
                title = getattr(entry, "title", "")
                text  = re.sub(r"<[^>]+>", "", getattr(entry, "summary", ""))[:2000]
                if not url or not title or mem.learning_ingested(url): continue
                # Filter for M&A-relevant content
                if not any(w in (title + text).lower() for w in
                          ["acqui", "merger", "deal", "buy", "takeover", "divest", "spin-off", "ipo", "raise", "fund"]):
                    continue
                chunks = _save_to_kb(source["name"], source["category"], title, url, text)
                if not chunks: continue
                mem.log_learning("ma_intelligence", source["name"], title, url, source["category"], chunks)
                new_items += 1; new_chunks += chunks
                log.info(f"  [M&A] {title[:60]} ({chunks} chunks)")
        except Exception as e:
            log.warning(f"  [M&A] {source['name']}: {e}")

    # Historical queries via Brave (50-year scope)
    if historical and BRAVE_API_KEY:
        log.info("Running historical 50-year M&A research via Brave...")
        for query in get_historical_queries():
            if new_items >= max_new * 2: break
            results = _brave_search(query, count=3)
            for r in results:
                url   = r.get("url", "")
                title = r.get("title", "")
                text  = r.get("description", "")[:1500]
                if not url or not title or mem.learning_ingested(url): continue
                chunks = _save_to_kb("Brave Historical", "deal_history", title, url, text)
                if not chunks: continue
                mem.log_learning("ma_intelligence", "Brave Historical", title, url, "deal_history", chunks)
                new_items += 1; new_chunks += chunks
                log.info(f"  [M&A Historical] {title[:60]}")

    mem.upsert_agent_health("ma_intelligence", last_learning=datetime.now().isoformat() if new_items > 0 else None)
    log.info(f"M&A Intelligence: {new_items} new items, {new_chunks} chunks")
    return {"agent": "ma_intelligence", "new_items": new_items, "chunks": new_chunks}

def generate_analysis(topic: str = "") -> Path:
    """Generate an M&A intelligence analysis report."""
    if not ANTHROPIC_API_KEY: return None
    query = topic or "MedTech pharma M&A deal QARA regulatory implications"
    kb_ctx = base.kb_context(query, top_k=6)
    prompt = f"""Generate a comprehensive M&A intelligence briefing for Latitude MedTech LLC.
{f'Focus: {topic}' if topic else ''}

{kb_ctx}

Structure:
1. Recent deal activity (last 12 months) — key transactions, deal values, strategic rationales
2. Historical context — how current activity compares to 10/20/50 year trends
3. QARA implications — what these deals mean for quality systems, regulatory compliance
4. Success/failure patterns — what separates successful integrations from failures
5. Lessons for MedTech founders/consultants — what to know before an M&A event
6. Implications for Latitude MedTech coaching and consulting clients

Quality standard: McKinsey M&A practice quality. Specific data, real deals, actionable insights."""

    resp = base._get_client().messages.create(
        model="claude-sonnet-4-6", max_tokens=3000,
        system=base.system_prompt(),
        messages=[{"role": "user", "content": prompt}]
    )
    content = resp.content[0].text.strip()
    slug     = re.sub(r"[^a-z0-9]+", "_", (topic or "ma_analysis").lower())[:30]
    out_path = OUT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_{slug}.md"
    out_path.write_text(f"# M&A Intelligence Analysis\n*{datetime.now().strftime('%B %d, %Y')}*\n\n{content}", encoding="utf-8")
    log.info(f"M&A analysis: {out_path}")
    return out_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyse",    action="store_true", help="Generate M&A analysis report")
    parser.add_argument("--historical", action="store_true", help="Include 50-year historical Brave searches")
    parser.add_argument("--topic",      type=str, default="", help="Analysis topic override")
    parser.add_argument("--max",        type=int, default=8)
    args = parser.parse_args()
    log.info("=" * 50)
    log.info("  Latitude MedTech — M&A Intelligence Agent")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 50)
    if args.analyse:
        generate_analysis(args.topic)
    else:
        learn(args.max, historical=args.historical)

if __name__ == "__main__":
    main()
