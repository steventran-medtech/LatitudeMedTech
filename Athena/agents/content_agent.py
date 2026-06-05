"""
Agent 2 — MedTech Meridian Content Agent
=========================================
Monitors regulatory news and MedTech trends, then drafts a
full Substack article for MedTech Meridian ready for your review.

Run manually : python content_agent.py
Run weekly   : use Task Scheduler (see run_content.bat)

Output: ~/Athena/content/drafts/YYYY-MM-DD_title.md
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import json
import logging
import feedparser
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import anthropic

from pathconfig import ENV_FILE, AGENTS_DIR, DRAFTS_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

try:
    from kb_query import KBQuery
    kb = KBQuery()
except ImportError:
    kb = None

try:
    from memory import Memory
    mem = Memory()
except ImportError:
    mem = None

# ── Paths ─────────────────────────────────────────────────────────────────────
LOG_DIR = LOGS_DIR
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "content_agent.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("content_agent")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# ── Style guide sources ───────────────────────────────────────────────────────
STYLE_GUIDES = [
    {
        "name": "MedTech Dive",
        "url":  "https://www.medtechdive.com/",
        "type": "industry_news",
    },

]

def fetch_style_examples(max_chars=2000) -> str:
    """Fetch recent headlines/snippets from style guide sources for tone reference."""
    import requests
    from bs4 import BeautifulSoup
    import re

    examples = []
    headers  = {"User-Agent": "LatitudeMedTech-ContentAgent/1.0"}

    for source in STYLE_GUIDES:
        try:
            r    = requests.get(source["url"], headers=headers, timeout=4)
            soup = BeautifulSoup(r.content, "html.parser")

            # Extract headlines and first sentences
            texts = []
            for tag in soup.find_all(["h2", "h3", "h4"])[:8]:
                t = tag.get_text(strip=True)
                if len(t) > 20:
                    texts.append(t)

            # Get a few article snippets
            for p in soup.find_all("p")[:6]:
                t = p.get_text(strip=True)
                if len(t) > 60:
                    texts.append(t[:200])

            if texts:
                examples.append(f"\n--- {source['name']} style examples ---\n" + "\n".join(texts[:6]))
        except Exception as e:
            log.warning(f"Could not fetch style guide {source['name']}: {e}")

    combined = "\n".join(examples)
    return combined[:max_chars] if combined else ""

# ── News sources ──────────────────────────────────────────────────────────────
NEWS_FEEDS = [
    {"name": "FDA Medical Device News",   "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml"},
    {"name": "FDA Recalls",               "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml"},
    {"name": "IMDRF",                     "url": "https://www.imdrf.org/rss.xml"},
]

def _load_consulting_standards() -> str:
    """Pull Big 4 quality + values sections from CLAUDE.md for grounding."""
    claude_md = Path(r"C:\Users\huann\LatitudeMedTech\CLAUDE.md")
    if not claude_md.exists():
        return ""
    raw = claude_md.read_text(encoding="utf-8")
    sections, out = ["## Core Values", "## Agent Principles", "## North Star"], []
    for s in sections:
        start = raw.find(s)
        if start != -1:
            end = raw.find("\n## ", start + 1)
            out.append(raw[start: end if end != -1 else start + 600])
    return "\n".join(out)

MERIDIAN_VOICE = """You are writing for MedTech Meridian — a Substack by Steven Tran, founder of Latitude MedTech LLC, a San Diego-based MedTech consulting and coaching firm.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-NEGOTIABLE QUALITY GATE — READ THIS FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before writing a single word, ask: "Would a McKinsey EM or BCG Project Leader sign off on this?"
If the answer is no — rewrite it. This is not a content farm article. This is not a LinkedIn post.
This is a practitioner-written, insight-led piece that earns trust through specificity and honesty.

BANNED IMMEDIATELY — these words/phrases result in a failed article:
  ✗ "it is important to note"  ✗ "in today's rapidly evolving"  ✗ "leveraging synergies"
  ✗ "in conclusion"            ✗ "The medical device industry…"  ✗ "robust"  ✗ "streamline"
  ✗ Any generic opener         ✗ Vague claims without citation    ✗ Passive voice piled on passive voice

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIENCE:
  — Primary: QA/RA professionals (0–7 yrs) who are smart, time-pressed, and allergic to fluff
  — Secondary: Students / career-changers entering MedTech who need context
  Write for both simultaneously: specific enough that the 5-year QA engineer learns something new.
  Clear enough that the sophomore biology major in San Diego follows every sentence.

VOICE — Steven Tran, not a textbook:
  ✓ First person singular ("I", "my", "I've seen") — this is a personal publication
  ✓ Conversational authority: like a former FDA reviewer explaining things over coffee
  ✓ Honest about complexity, honest about limitations, honest about what you don't know
  ✓ San Diego / SoCal MedTech corridor texture when relevant: Biocom, Dexcom, Masimo, BD, UCSD
  ✓ Real stakes: dollars lost, time wasted, careers advanced or stalled — make it vivid

SUBSTANCE REQUIREMENTS:
  ✓ Open with a specific, true-feeling scene: a real company (public), a real FDA letter, a real clause number, a real dollar amount, a real career moment — NOT a hypothetical
  ✓ Every regulatory claim: cite the specific regulation (21 CFR §820.30(b)), clause (ISO 13485 §7.3.4), or document title (FDA Guidance: Design Controls for Medical Devices, 1997)
  ✓ Every technical term defined in plain English on first use, in parentheses
  ✓ One analogy that earns the right to go technical: "think of it like..." before the deep dive
  ✓ At least one concrete, actionable takeaway the reader can execute this week
  ✓ Minimum one data point or statistic (FDA's 2025 510(k) average review time, RAPS salary survey, etc.)

MANDATORY STRUCTURE — use exactly these heading levels and section names:

# [Article title — specific, compelling, a promise not a label. Normal title case. Not ALL CAPS.]

[Opening hook — no heading. Specific scene, 150–200 words. Drop the reader into the story immediately.]

## Why This Matters to Your Career
[Bridge: connect regulatory concept to career impact. Job titles, salary bands, interview questions. 150–200 words.]

## The Real Mechanics
[The substantive core. Specific regulations, clause numbers, process steps, real examples. What auditors look for. What FDA actually rejected and why. 350–500 words.]

## What to Do This Week
[Two concrete actions. Not "research this topic" — specific: name the FDA database, the exact LinkedIn search, the precise certification exam. 100–150 words.]

## The Long Game
[Zoom out. 10-year career trajectory. Where SoCal MedTech is heading. What's changing and why it matters for someone at 0 years vs 7 years in. 100–150 words.]

---
*Disclaimer: Educational content only. Nothing here is regulatory, legal, or compliance advice. Consult qualified professionals and official guidance documents.*

LENGTH: 900–1,200 words. Not 700. Not 1,500. Every paragraph earns its place.

FINAL CHECK before submitting: Read the first sentence. Is it specific? Is it surprising? Would someone who reads McKinsey Quarterly find it worth their time? If not — rewrite the opening."""



# ── Topic curriculum ──────────────────────────────────────────────────────────
# 10 distinct categories. select_topic rotates through them and avoids
# recent coverage, preventing the "all CAPA all the time" pattern.

TOPIC_CURRICULUM = {
    "regulatory_pathways": {
        "label": "Regulatory Pathways",
        "examples": ["510(k) substantial equivalence deep dive", "De Novo explained simply",
                     "When PMA is actually required", "EU MDR Article 61 — when do you need clinical trials",
                     "MDSAP vs ISO 13485 — what actually differs"],
        "prompt_seed": "regulatory submission pathways, 510k, PMA, De Novo, EU MDR, clinical evidence",
    },
    "career_strategy": {
        "label": "Career Strategy",
        "examples": ["How to negotiate a QA/RA salary with specifics", "The RA Specialist to Manager jump",
                     "What a RAPS RAC certification actually gets you", "How to read a MedTech job description",
                     "Breaking into QA from a non-regulated background"],
        "prompt_seed": "MedTech career development, QA RA jobs, salary, certifications, career path",
    },
    "fda_enforcement": {
        "label": "FDA Enforcement & Warning Letters",
        "examples": ["A real warning letter dissected clause by clause", "What FDA inspectors actually look for",
                     "How to respond to a Form 483", "The anatomy of a recall — what really went wrong"],
        "prompt_seed": "FDA warning letters, 483 observations, recalls, enforcement actions, CDRH",
    },
    "design_controls": {
        "label": "Design Controls & Risk",
        "examples": ["21 CFR 820.30 explained for someone who just got assigned to it",
                     "ISO 14971 risk management without the jargon", "DHF vs DMR — what goes where",
                     "When design verification and validation actually differ"],
        "prompt_seed": "design controls, DHF, risk management, ISO 14971, verification validation",
    },
    "quality_systems": {
        "label": "Quality Systems (Beyond CAPA)",
        "examples": ["Document control that doesn't slow everything down", "Supplier qualification for small companies",
                     "What management review actually has to cover", "Internal audit findings that don't get closed"],
        "prompt_seed": "QMS quality management, document control, supplier quality, management review, internal audit",
    },
    "industry_intelligence": {
        "label": "MedTech Industry Intelligence",
        "examples": ["San Diego MedTech companies hiring right now", "AI in medical devices — the FDA's actual position",
                     "What the EU MDR transition is doing to small companies",
                     "Why Class II devices are eating Class III's lunch"],
        "prompt_seed": "medical device industry trends, FDA approvals, EU MDR, AI medical devices, SoCal biotech",
    },
    "capa_and_nonconformance": {
        "label": "CAPA & Nonconformance",
        "examples": ["Your first CAPA — what they don't teach you", "Root cause analysis methods that actually work",
                     "When a nonconformance becomes a recall", "Effectiveness checks that pass FDA inspection"],
        "prompt_seed": "CAPA corrective preventive action, nonconformance, root cause analysis, effectiveness",
    },
    "clinical_regulatory": {
        "label": "Clinical & Post-Market",
        "examples": ["What a clinical evaluation report actually contains", "PMCF — what it means and who has to do it",
                     "MDR (medical device reporting) demystified", "Complaint handling that builds evidence"],
        "prompt_seed": "clinical evaluation, post-market surveillance, PMCF, MDR reporting, complaint handling",
    },
    "softskills_leadership": {
        "label": "Professional Skills & Leadership",
        "examples": ["How to present to the executive team as a QA analyst", "Stakeholder management in regulated industries",
                     "Writing a deviation report that's actually clear", "Cross-functional influence without authority"],
        "prompt_seed": "professional development, communication, leadership, writing skills, cross-functional teams",
    },
    "biotech_pharma_crossover": {
        "label": "Biotech & Pharma Crossover",
        "examples": ["Moving from pharma to MedTech — what transfers and what doesn't",
                     "Combination products — when FDA requires both paths", "GMP vs GMP — device vs drug manufacturing"],
        "prompt_seed": "biotech pharma MedTech crossover, combination products, GMP, drug device",
    },
}

def _get_next_topic_category(mem_obj) -> dict:
    """
    Pick the topic category least recently covered.
    Prevents CAPA dominance and ensures curriculum variety.
    """
    if not mem_obj:
        import random
        return random.choice(list(TOPIC_CURRICULUM.values()))
    try:
        # Get coverage counts per category from content_items
        rows = mem_obj.conn.execute(
            "SELECT metadata FROM content_items WHERE content_type='article' ORDER BY timestamp DESC LIMIT 30"
        ).fetchall()
        covered = {}
        for row in rows:
            if row["metadata"]:
                try:
                    m = json.loads(row["metadata"])
                    cat = m.get("topic_category", "")
                    if cat:
                        covered[cat] = covered.get(cat, 0) + 1
                except Exception:
                    pass
        # Pick least-covered category
        all_cats = list(TOPIC_CURRICULUM.keys())
        chosen = min(all_cats, key=lambda c: covered.get(c, 0))
        return {"key": chosen, **TOPIC_CURRICULUM[chosen]}
    except Exception:
        import random
        key = random.choice(list(TOPIC_CURRICULUM.keys()))
        return {"key": key, **TOPIC_CURRICULUM[key]}


# ── News fetching ─────────────────────────────────────────────────────────────

def fetch_recent_news() -> list:
    import random
    all_items = []
    # Shuffle feeds for variation
    feeds = NEWS_FEEDS.copy()
    random.shuffle(feeds)
    for feed_info in feeds:
        try:
            feed  = feedparser.parse(feed_info["url"])
            items = feed.entries[:5]
            for item in items:
                all_items.append({
                    "source":  feed_info["name"],
                    "title":   getattr(item, "title", ""),
                    "summary": getattr(item, "summary", "")[:300],
                    "link":    getattr(item, "link", ""),
                    "date":    getattr(item, "published", ""),
                })
        except Exception as e:
            log.warning(f"Could not fetch {feed_info['name']}: {e}")
    return all_items


# ── Topic selection ───────────────────────────────────────────────────────────

def select_topic(news_items: list, override: str = "") -> dict:
    if not ANTHROPIC_API_KEY:
        return {"title": "The QA/RA Career Path Nobody Talks About", "angle": "career development"}

    client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    news_summary = "\n".join(
        f"- [{item['source']}] {item['title']}: {item['summary']}"
        for item in news_items[:10]
    )

    # Get recently covered topics to avoid repetition
    recent = []
    if mem:
        recent = [t['title'] for t in mem.get_recent_topics(content_type='article', days=90)]
    avoid_note = f"\n\nIMPORTANT: Do NOT suggest topics similar to these recently covered articles:\n" + "\n".join(f"- {t}" for t in recent[:10]) if recent else ""

    # When an override is given, skip topic selection entirely and build directly from it
    if override.strip():
        return {
            "title":      override.strip(),
            "angle":      f"Requested focus: {override.strip()}",
            "hook":       f"A deep dive into: {override.strip()}",
            "key_points": [override.strip()],
            "why_now":    "Directly requested by the user.",
            "_override":  override.strip(),
        }

    # Pick the topic category least covered so far (diversity enforcement)
    category = _get_next_topic_category(mem)
    cat_label   = category.get("label", "MedTech")
    cat_seed    = category.get("prompt_seed", "")
    cat_key     = category.get("key", "")
    cat_examples = category.get("examples", [])
    import random as _rnd
    example_hint = _rnd.choice(cat_examples) if cat_examples else ""

    avoid_note = ""
    if recent:
        avoid_note = f"\n\nCRITICAL — Do NOT suggest any topic similar to these recently published articles:\n" + \
                     "\n".join(f"- {t}" for t in recent[:10])

    prompt = f"""You are the editorial director for MedTech Meridian — a Substack for QA/RA professionals, written by the founder of a San Diego MedTech consulting firm.

ASSIGNED CATEGORY THIS WEEK: {cat_label}
(The editorial calendar is rotating through topics to avoid repetition. This week MUST be in this category.)

Category focus: {cat_seed}
Example topics in this category (do not copy verbatim — use as inspiration only): {example_hint}

Recent regulatory news to weave in where relevant:
{news_summary}
{avoid_note}

Your job: suggest ONE specific, compelling article topic within the {cat_label} category.

Requirements:
- The title must be SPECIFIC — a promise to the reader, not a label (bad: "Understanding CAPA"; good: "The Reason Your CAPA Keeps Getting Rejected at FDA Inspection")
- It must work for both a QA engineer with 5 years experience AND a college junior considering MedTech
- It must be something the reader can't get from a Google search — genuine insight or a reframe
- It must connect to the Southern California / San Diego MedTech corridor when possible

Respond with JSON only — no markdown fences:
{{
  "title": "Specific, compelling article title",
  "angle": "One sentence — the unique insight or reframe that makes this worth reading",
  "hook": "The specific opening scene (a real device, real company, real moment) that pulls the reader in",
  "key_points": ["specific point 1 with detail", "specific point 2 with detail", "specific point 3 with detail"],
  "why_now": "Why a QA/RA professional needs to read this THIS week",
  "topic_category": "{cat_key}"
}}"""

    try:
        import time as _time
        t0   = _time.time()
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        if mem:
            mem.log_api_call('content_agent', 'claude-haiku-4-5',
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens,
                purpose='topic selection')
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        # Ensure category is recorded
        result.setdefault("topic_category", cat_key)
        return result
    except Exception as e:
        log.warning(f"Topic selection failed: {e}. Using curriculum fallback.")
        # Fallback picks a random category — not always CAPA
        fallbacks = [
            {"title": "The 510(k) Sections That Sink More Submissions Than Any Other",
             "angle": "Most rejections come from the same three places — here's how to fix them before you submit",
             "hook": "A pacemaker lead manufacturer in Carlsbad, CA just got their 510(k) kicked back for the fourth time.",
             "key_points": ["Predicate selection errors", "Substantial equivalence arguments that don't hold", "Performance testing gaps"],
             "why_now": "FDA's review times are up 30% — you cannot afford a round-trip",
             "topic_category": "regulatory_pathways"},
            {"title": "What a $180,000 QA/RA Career Actually Looks Like — and How to Get There",
             "angle": "The salary ceiling in this field is higher than most people realise, but the path is specific",
             "hook": "Last month I coached someone who went from $72k to $145k in 18 months. Here's exactly what changed.",
             "key_points": ["The certifications that actually move the needle", "The job titles that unlock six figures", "What hiring managers look for at Director level"],
             "why_now": "Biocom's latest workforce report shows a 22% shortage of senior RA professionals in SoCal",
             "topic_category": "career_strategy"},
        ]
        return _rnd.choice(fallbacks)


# ── Article drafting ──────────────────────────────────────────────────────────

def draft_article(topic: dict, news_items: list, kb_context: str = "") -> str:
    if not ANTHROPIC_API_KEY:
        return f"# {topic['title']}\n\n[API key required to generate article draft]\n"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    news_context = "\n".join(
        f"- {item['title']} ({item['source']})"
        for item in news_items[:5]
    )

    # Fetch style guide examples - non-blocking, 5s max
    import concurrent.futures
    style_examples = ""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(fetch_style_examples)
            style_examples = future.result(timeout=5)
    except Exception:
        style_examples = ""  # Skip if slow or unavailable
    style_note = f"""
Style reference (use these as tone/format guides only — do not copy content):
{style_examples}
""" if style_examples else ""

    kb_header = ("KNOWLEDGE BASE GROUNDING:\n" + kb_context) if kb_context else ""
    override_header = (
        f"REQUIRED TOPIC (non-negotiable — write specifically about this):\n{topic['_override']}\n"
    ) if topic.get('_override') else ""

    # ── Image suggestions ──────────────────────────────────────────────────
    # Unsplash Source API — free, no API key, embeds directly in Markdown.
    # Keywords derived from topic title and angle.
    import urllib.parse as _ul
    topic_words = " ".join(topic['title'].split()[:4])
    img_keywords = _ul.quote_plus(f"medical device {topic_words}".lower()[:60])
    hero_img = f"https://source.unsplash.com/1200x500/?{img_keywords}"
    inline_img = f"https://source.unsplash.com/800x400/?{_ul.quote_plus('regulatory compliance laboratory science')}"

    prompt = f"""{override_header}Write a complete MedTech Meridian Substack article based on this brief:

Title: {topic['title']}
Angle: {topic['angle']}
Hook: {topic['hook']}
Key points to cover: {', '.join(topic.get('key_points', []))}
Why this week: {topic.get('why_now', '')}

Recent industry context (weave in naturally where relevant):
{news_context}
{style_note}
{kb_header}

IMAGES — embed these exactly after the H1 title line (do not put them in the body text):
![{topic['title']}]({hero_img})

If the article references numerical data or a comparison, include ONE markdown table to present it cleanly. Tables must have real data, not placeholders.

Write the full article now. Follow the MedTech Meridian voice and structure. 900-1200 words.
Include the images exactly as specified above. Do not omit them."""

    try:
        import time as _time
        t0   = _time.time()
        consulting_standards = _load_consulting_standards()
        full_system = MERIDIAN_VOICE
        if consulting_standards:
            full_system += f"\n\nFIRM STANDARDS (Big 4 quality — apply to this article):\n{consulting_standards}"
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,     # CAPA-Content-001: raised to ensure complete 1200-word articles
            system=full_system,
            messages=[{"role": "user", "content": prompt}],
        )
        ms = int((_time.time() - t0) * 1000)
        if mem:
            mem.log_api_call('content_agent', 'claude-sonnet-4-6',
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens,
                purpose='article draft',
                duration_ms=ms)
        return resp.content[0].text.strip()
    except Exception as e:
        log.error(f"Article drafting failed: {e}")
        return f"# {topic['title']}\n\n[Draft generation failed: {e}]\n"


# ── Save draft ────────────────────────────────────────────────────────────────

def save_draft(topic: dict, article: str) -> Path:
    date_str  = datetime.now().strftime("%Y-%m-%d")
    slug      = topic["title"].lower()
    slug      = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug      = "_".join(slug.split())[:50]
    filename  = f"{date_str}_{slug}.md"
    out_path  = DRAFTS_DIR / filename

    metadata = f"""---
title: {topic['title']}
date: {date_str}
status: DRAFT — needs your review before publishing
publication: MedTech Meridian (Substack)
angle: {topic['angle']}
generated_by: Latitude MedTech Content Agent
---

"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(metadata + article)

    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--override", type=str, default="", help="Topic or instruction override for this run")
    args, _ = parser.parse_known_args()

    log.info("=" * 44)
    log.info("  Latitude MedTech Content Agent")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("============================================")

    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set. Check ~/Athena/voice/.env")
        sys.exit(1)

    log.info("Fetching recent regulatory news...")
    news = fetch_recent_news()
    log.info(f"Found {len(news)} news items across {len(NEWS_FEEDS)} sources.")

    log.info("Selecting article topic...")
    topic = select_topic(news, override=args.override)
    if args.override:
        topic['_override'] = args.override
    log.info(f"Topic: {topic['title']}")
    # Check memory — skip if covered recently using keywords
    if mem:
        keywords = topic.get('key_points', []) + [topic['title'].split(':')[0]]
        # Try up to 3 times to get a fresh topic
        attempts = 0
        while attempts < 3:
            existing = mem.topic_exists(keywords, content_type='article', days=45)
            if not existing:
                break
            log.info(f"  Similar topic covered recently ({existing}) — retrying...")
            topic = select_topic(news, override=args.override)
            keywords = topic.get('key_points', []) + [topic['title'].split(':')[0]]
            attempts += 1
        if attempts == 3:
            log.info("  Could not find unique topic after 3 attempts — proceeding anyway")

    log.info("Drafting article...")
    # Query local KB for relevant context
    kb_context = ""
    if kb and kb.has_content():
        keywords = f"{topic['title']} {topic.get('angle', '')}"
        chunks   = kb.search(keywords, top_k=4)
        kb_context = kb.format_context(chunks, max_chars=2000)
        if kb_context:
            log.info(f"  KB: injecting {len(chunks)} chunks from local knowledge base")
    article = draft_article(topic, news, kb_context=kb_context)

    out_path = save_draft(topic, article)
    log.info(f"Draft saved: {out_path}")
    if mem:
        keywords = topic.get('key_points', []) + [topic['title']]
        mem.register_content('content_agent', 'article', topic['title'],
            topic_keywords=keywords, status='draft', file_path=str(out_path),
            metadata={"topic_category": topic.get("topic_category", "")})
        mem.log_event('content_agent', 'draft_saved', topic['title'])
        mem.submit_for_review('content_agent', 'article', topic['title'], str(out_path))

    print(f"""
╔============================================══════════╗
|  MedTech Meridian Draft Ready                        |
╠============================================══════════╣
|  Title : {topic['title'][:48]:<48}|
|  File  : {str(out_path.name)[:48]:<48}|
|  Status: Ready for your review                       |
╚============================================══════════╝

Open: {out_path}
""")


if __name__ == "__main__":
    main()
