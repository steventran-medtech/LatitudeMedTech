"""
Agent 6 — Daily MedTech Intelligence Briefing (v2 — Brave Enhanced)
=====================================================================
RSS feeds + Brave Search for real-time coverage.
Brave catches breaking news that hasn't hit RSS yet.

.env variables:
    ANTHROPIC_API_KEY=...
    BRAVE_API_KEY=...

Usage:
    python briefing_agent.py
    python briefing_agent.py --week
"""

import os
import re
import sys
import json
import logging
import hashlib
import feedparser
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import anthropic

from pathconfig import ENV_FILE, AGENTS_DIR, BRIEFINGS_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

try:
    from kb_query import KBQuery
    _kb = KBQuery()
except ImportError:
    _kb = None

try:
    from agent_base import AgentBase
    _base = AgentBase("briefing")
except Exception:
    _base = None

try:
    from memory import Memory
    mem = Memory()
except ImportError:
    mem = None

LOG_DIR   = LOGS_DIR
SEEN_FILE = BRIEFINGS_DIR / '.seen_items.json'
BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'briefing_agent.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('briefing_agent')

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
BRAVE_API_KEY     = os.getenv('BRAVE_API_KEY', '')

# ── RSS sources ───────────────────────────────────────────────────────────────
RSS_SOURCES = [
    {"name": "FDA Medical Device Safety",  "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml", "category": "Regulatory", "priority": "high"},
    {"name": "FDA Recalls",                "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",          "category": "Recalls",    "priority": "high"},
    {"name": "FDA MedWatch",               "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml",          "category": "Safety",     "priority": "high"},
    {"name": "FDA CDRH Guidance",          "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/guidance/rss.xml",          "category": "Regulatory", "priority": "high"},
    {"name": "IMDRF",                      "url": "https://www.imdrf.org/rss.xml",                                                               "category": "Regulatory", "priority": "medium"},
    {"name": "MassDevice",                 "url": "https://www.massdevice.com/feed/",                                                            "category": "Industry",   "priority": "medium"},
    {"name": "Medical Design & Outsourcing","url": "https://www.medicaldesignandoutsourcing.com/feed/",                                          "category": "Industry",   "priority": "medium"},
    {"name": "DeviceTalks",                "url": "https://www.devicetalks.com/feed/",                                                           "category": "Industry",   "priority": "medium"},
    {"name": "RAPS News",                  "url": "https://www.raps.org/raps/media/news/rss.ashx",                                               "category": "Regulatory", "priority": "high"},
    {"name": "Emergo by UL",               "url": "https://www.emergobyul.com/blog/feed",                                                        "category": "Regulatory", "priority": "medium"},
    {"name": "Medical Device Academy",     "url": "https://medicaldeviceacademy.com/feed/",                                                      "category": "QA/RA",      "priority": "medium"},
    {"name": "greenlight.guru",            "url": "https://www.greenlight.guru/blog/rss.xml",                                                    "category": "QA/RA",      "priority": "medium"},
    {"name": "Biocom California",          "url": "https://www.biocom.org/feed/",                                                                "category": "SoCal",      "priority": "medium"},
    {"name": "MedCity News",               "url": "https://medcitynews.com/feed/",                                                               "category": "Industry",   "priority": "medium"},
    {"name": "BioPharma Dive",             "url": "https://www.biopharmadive.com/feeds/news/",                                                   "category": "M&A",        "priority": "medium"},
    {"name": "Fierce Biotech",             "url": "https://www.fiercebiotech.com/rss/xml",                                                       "category": "M&A",        "priority": "medium"},
    {"name": "STAT News",                  "url": "https://www.statnews.com/feed/",                                                              "category": "Industry",   "priority": "medium"},
]

# ── Brave search queries — always dynamic, never static ──────────────────────
def get_brave_queries():
    """
    Date-stamped queries so Brave returns current 2026 results.
    Always use dynamic dates — the static fallback list has been removed
    because it caused stale 2024/2025 data to be returned.
    """
    today = datetime.now().strftime("%B %Y")           # e.g. "June 2026"
    week  = datetime.now().strftime("week of %B %d %Y")
    year  = datetime.now().strftime("%Y")              # "2026"
    return [
        # Regulatory
        f"FDA medical device recall warning letter {today}",
        f"FDA CDRH guidance document released {today}",
        f"EU MDR MDCG guidance update medical device {today}",
        f"medical device company FDA approval clearance {week}",
        # M&A and financial — added per CAPA on stale data
        f"MedTech medical device M&A merger acquisition {today}",
        f"MedTech medical device funding raise IPO valuation {year}",
        f"life sciences biotech deal investment {today}",
        # Industry and career
        f"San Diego MedTech biotech news {today}",
        f"Biocom Southern California medical device {year}",
        "ISO 13485 MDSAP audit regulatory news",
    ]

# BRAVE_QUERIES static list removed — caused stale data. Always use get_brave_queries().

QA_RA_KEYWORDS = [
    "FDA", "510k", "PMA", "recall", "warning letter", "ISO 13485",
    "EU MDR", "MDR", "MDSAP", "CAPA", "audit", "quality system",
    "design controls", "risk management", "FMEA", "notified body",
    "MDCG", "clinical evaluation", "adverse event", "corrective action",
    "San Diego", "Biocom", "MedTech", "medical device",
]


# ── Seen items ────────────────────────────────────────────────────────────────

def load_seen() -> set:
    if SEEN_FILE.exists():
        try:
            data    = json.loads(SEEN_FILE.read_text())
            cutoff  = (datetime.now() - timedelta(days=30)).isoformat()
            return {k for k, v in data.items() if v > cutoff}
        except Exception:
            return set()
    return set()


def save_seen(seen: set):
    now = datetime.now().isoformat()
    try:
        existing = json.loads(SEEN_FILE.read_text()) if SEEN_FILE.exists() else {}
        existing.update({i: now for i in seen})
        cutoff   = (datetime.now() - timedelta(days=30)).isoformat()
        existing = {k: v for k, v in existing.items() if v > cutoff}
        SEEN_FILE.write_text(json.dumps(existing, indent=2))
    except Exception as e:
        log.warning(f"Could not save seen items: {e}")


def item_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


# ── RSS fetching ──────────────────────────────────────────────────────────────

def fetch_rss_items(seen: set) -> list:
    all_items = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:10]:
                title   = getattr(entry, 'title',   '').strip()
                link    = getattr(entry, 'link',    '').strip()
                summary = getattr(entry, 'summary', '').strip()
                if not title or not link:
                    continue
                iid = item_id(link)
                if iid in seen:
                    continue
                text  = f"{title} {summary}".lower()
                score = sum(1 for kw in QA_RA_KEYWORDS if kw.lower() in text)
                all_items.append({
                    'title':    title,
                    'link':     link,
                    'summary':  summary[:300],
                    'source':   source['name'],
                    'category': source['category'],
                    'priority': source['priority'],
                    'score':    score,
                    'id':       iid,
                    'via':      'rss',
                })
        except Exception as e:
            log.warning(f"RSS failed {source['name']}: {e}")
    return all_items


# ── Brave Search integration ──────────────────────────────────────────────────

def brave_search(query: str, count: int = 5, freshness: str = "pd") -> list:
    """Search using Brave Search API."""
    if not BRAVE_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/news/search",
            headers={
                "Accept":               "application/json",
                "Accept-Encoding":      "gzip",
                "X-Subscription-Token": BRAVE_API_KEY,
            },
            params={
                "q":           query,
                "count":       count,
                "freshness":   freshness,  # "pd" past day, "pw" past week, etc.
                "text_decorations": False,
            },
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        items   = []
        for r in results:
            title = r.get("title", "")
            url   = r.get("url", "")
            desc  = r.get("description", "")
            if title and url:
                items.append({
                    "title":   title,
                    "link":    url,
                    "summary": desc[:300],
                    "source":  "Brave Search",
                })
        return items
    except Exception as e:
        log.warning(f"Brave search failed '{query}': {e}")
        return []


def fetch_brave_items(seen: set, focus: str = "") -> list:
    if not BRAVE_API_KEY:
        log.info("  Brave Search: skipped (BRAVE_API_KEY not set)")
        return []

    queries = get_brave_queries()
    # Focused (override) run: search the requested topic directly. These queries
    # use a wider freshness window and bypass the seen/keyword filters so the
    # user actually gets results on the topic they asked for, even mid-day.
    focus_queries = build_focus_queries(focus) if focus.strip() else []
    log.info(f"  Running {len(queries)} date-aware + {len(focus_queries)} focused Brave searches...")
    all_items = []
    seen_urls = set()

    for query in queries + focus_queries:
        is_focus = query in focus_queries
        results  = brave_search(query, count=4 if is_focus else 3,
                                freshness="pw" if is_focus else "pd")
        for r in results:
            iid = item_id(r["link"])
            if r["link"] in seen_urls:
                continue
            if iid in seen and not is_focus:
                continue  # focused queries are allowed to resurface seen items
            text  = f"{r['title']} {r['summary']}".lower()
            score = sum(1 for kw in QA_RA_KEYWORDS if kw.lower() in text)
            if score == 0 and not is_focus:
                continue  # general feed must match firm keywords; focus is trusted
            all_items.append({
                'title':    r['title'],
                'link':     r['link'],
                'summary':  r['summary'],
                'source':   f"Brave: {query[:40]}",
                'category': "Focus" if is_focus else "Breaking",
                'priority': "high",
                'score':    score + (5 if is_focus else 0),   # focus items float to top
                'id':       iid,
                'via':      'brave',
            })
            seen_urls.add(r["link"])
        import time; time.sleep(0.3)

    log.info(f"  Brave found {len(all_items)} relevant items")
    return all_items


def build_focus_queries(focus: str) -> list:
    """Topic-specific Brave queries for a focused briefing run."""
    topic = focus.strip()
    today = datetime.now().strftime("%B %Y")
    year  = datetime.now().strftime("%Y")
    return [
        f"{topic} medical device {today}",
        f"{topic} MedTech regulatory FDA OR EU MDR {year}",
        f"{topic} medtech news {today}",
    ]


# ── Briefing generation ───────────────────────────────────────────────────────

def generate_briefing(items: list, date_str: str, override: str = "") -> str:
    if not ANTHROPIC_API_KEY or not items:
        return format_simple_briefing(items, date_str)

    client     = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    brave_items = [i for i in items if i.get('via') == 'brave']
    rss_items   = [i for i in items if i.get('via') == 'rss']

    # Pull KB context for top items to enrich summaries
    kb_note = ""
    if _kb and _kb.has_content():
        top_titles = " ".join(i["title"] for i in items[:5])
        chunks     = _kb.search(top_titles, top_k=3)
        kb_ctx     = _kb.format_context(chunks, max_chars=1200)
        if kb_ctx:
            kb_note = f"\n\nRELEVANT REGULATORY BACKGROUND FROM LOCAL KNOWLEDGE BASE:\n{kb_ctx}"

    items_text = "\n\n".join(
        f"[{i['category']} | {i['source']} | via:{i.get('via','rss')}]\nTitle: {i['title']}\nURL: {i['link']}\nSummary: {i['summary']}"
        for i in items[:30]
    )

    brave_note = f"\n\nNote: {len(brave_items)} items came from Brave real-time search (breaking news). {len(rss_items)} from RSS feeds." if brave_items else ""

    # Load agent persona from context file
    agent_persona = _base.context_file() if _base else ""
    system_block  = f"AGENT CONTEXT:\n{agent_persona}\n\n" if agent_persona else ""

    override_block = ""
    if override.strip():
        override_block = (
            f"\n\nUSER FOCUS REQUEST (non-negotiable — this is what was asked for): "
            f"{override.strip()}\n"
            "Prioritise items related to this topic. If no items directly match, "
            "note what was found and what was not, then recommend running a targeted search.\n"
        )

    prompt = f"""{system_block}You are preparing a daily intelligence briefing for the founder of Latitude MedTech LLC — a QA/RA professional and MedTech coach in San Diego.
{override_block}
Today: {date_str}{brave_note}

Items from monitored sources:

{items_text}

Write a tight, management-consultant-grade morning briefing — the register of a
McKinsey / Big-4 daily flash note. Lead with the implication, then the fact.

## Breaking
(Real-time items from Brave search — most recent developments. One sentence each. Skip if none.)

## Need to Know
(2-3 highest-priority regulatory actions, recalls, or guidance updates. For each: a
bolded headline, then the "so what" for a QA/RA leader in one crisp line.)

## Industry Pulse
(3-5 notable industry items. One sentence each.)

## QA/RA Learning
(1-2 educational items.)

## SoCal Watch
(San Diego / Southern California MedTech items. Skip if none.)

## Worth Reading Later
(2-3 interesting but non-urgent items.)

Rules:
- Do NOT write a title, an "# MedTech…" heading, a "BRIEFING:" line, or a date — the
  document header and review label are added automatically. Start directly with "## Breaking".
- Do NOT add an "Alpha — Steve Review Required" line — it is shown as a status badge.
- Cite every item with an inline markdown link woven into the sentence, e.g.
  "…FDA issued an [Early Alert](URL)." Never drop a bare URL or a link on its own line.
- One link per item; put it on the most load-bearing noun, not the word "here".
- Skip sections with no relevant items. No filler, no preamble. Under 450 words total."""

    try:
        import time as _time
        t0   = _time.time()
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1400,
            messages=[{"role": "user", "content": prompt}],
        )
        ms = int((_time.time() - t0) * 1000)
        if mem:
            mem.log_api_call('briefing_agent', 'claude-haiku-4-5',
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens,
                purpose='daily briefing summary',
                duration_ms=ms)
        return resp.content[0].text.strip()
    except Exception as e:
        log.warning(f"AI briefing failed: {e}")
        return format_simple_briefing(items, date_str)


def format_simple_briefing(items: list, date_str: str) -> str:
    by_cat = {}
    for item in items:
        cat = item['category']
        by_cat.setdefault(cat, []).append(item)
    lines = [f"## MedTech Briefing - {date_str}\n"]
    for cat, cat_items in sorted(by_cat.items()):
        lines.append(f"\n### {cat}")
        for item in cat_items[:5]:
            lines.append(f"- [{item['title']}]({item['link']})")
    return '\n'.join(lines)


def save_briefing(content: str, date_str: str, item_count: int, brave_count: int,
                  focus: str = "") -> Path:
    # A focused (override) run is an *additional* briefing for the day — give it
    # its own filename so it never clobbers the morning daily briefing.
    if focus.strip():
        slug    = re.sub(r'[^a-z0-9]+', '_', focus.lower()).strip('_')[:30] or 'focus'
        stamp   = datetime.now().strftime('%H%M')
        out_path = BRIEFINGS_DIR / f"{date_str}_briefing_{slug}_{stamp}.md"
        title    = f"MedTech Intelligence Briefing — {focus.strip()}"
    else:
        out_path = BRIEFINGS_DIR / f"{date_str}_briefing.md"
        title    = f"MedTech Intelligence Briefing - {datetime.now().strftime('%B %d, %Y')}"
    header   = f"""---
date: {date_str}
status: Alpha — Steve Review Required
focus: {focus.strip() or 'general daily'}
items_reviewed: {item_count}
brave_items: {brave_count}
rss_sources: {len(RSS_SOURCES)}
brave_queries: {len(get_brave_queries())}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# {title}

"""
    out_path.write_text(header + content, encoding='utf-8')
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--override", type=str, default="",
                        help="Focus the briefing on a specific topic. Also enables "
                             "same-day re-runs (saved as a separate focused briefing).")
    parser.add_argument("--week", action="store_true")
    # parse_known_args so a multi-word --override value (passed unquoted by the UI)
    # never trips the parser the way a second strict parser used to.
    args, _ = parser.parse_known_args()
    override = args.override.strip()

    date_str = datetime.now().strftime('%Y-%m-%d')
    log.info(f"Latitude MedTech Briefing Agent v2 - {date_str}")
    log.info(f"Brave Search: {'enabled' if BRAVE_API_KEY else 'disabled (no key)'}")

    # Only the plain daily run is guarded against accidental same-day overwrite.
    # A focused (--override) run is always allowed and saved to its own file.
    existing = BRIEFINGS_DIR / f"{date_str}_briefing.md"
    if existing.exists() and not args.week and not override:
        print(f"\nToday's briefing already exists: {existing}")
        print("Use --override 'topic' to generate a focused briefing on a specific topic.")
        return

    seen = load_seen()
    # Also check memory DB for seen items
    if mem:
        seen = seen | {hashlib.md5(url.encode()).hexdigest()[:12]
                       for url in []}  # memory checked per-item below
    rss_items  = fetch_rss_items(seen)
    brave_items = fetch_brave_items(seen, focus=override)
    all_items  = rss_items + brave_items

    log.info(f"Total new items: {len(all_items)} ({len(rss_items)} RSS, {len(brave_items)} Brave)")

    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_items.sort(key=lambda x: (priority_order.get(x['priority'], 2), -x['score']))

    if not all_items:
        content = f"No new items found today across {len(RSS_SOURCES)} RSS sources and {len(get_brave_queries())} Brave searches."
    else:
        log.info("Generating briefing...")
        content = generate_briefing(all_items, date_str, override=override)

    out_path = save_briefing(content, date_str, len(all_items), len(brave_items), focus=override)
    new_seen = {i['id'] for i in all_items}
    save_seen(seen | new_seen)
    if mem:
        mem.mark_briefing_items('briefing_agent', [i['link'] for i in all_items])
        mem.log_event('briefing_agent', 'briefing_generated', metadata={'items': len(all_items), 'brave': len(brave_items)})

    print(f"""
+--------------------------------------------------+
|  Latitude MedTech Daily Briefing                 |
+--------------------------------------------------+
|  Date    : {date_str:<38}|
|  RSS     : {str(len(rss_items)):<38}|
|  Brave   : {str(len(brave_items)):<38}|
+--------------------------------------------------+

Open: {out_path}
""")
    print("-" * 60)
    print(content)
    print("-" * 60)


if __name__ == '__main__':
    main()
