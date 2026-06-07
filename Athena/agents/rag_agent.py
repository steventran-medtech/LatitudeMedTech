"""
Agent 1 — RAG Ingestion Agent (v2 — Tavily Enhanced)
======================================================
Crawls public regulatory guidance sources AND uses Tavily
to actively search for new regulatory documents, guidance
updates, and MedTech content.

Tavily finds what RSS feeds miss.

Run manually : python rag_agent.py
Run nightly  : Task Scheduler via schedule_rag.bat

.env variables:
    ANTHROPIC_API_KEY=...
    TAVILY_API_KEY=...
"""

import os
import sys
import json
import time
import hashlib
import logging
import requests
import feedparser
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from pathconfig import ENV_FILE, KB_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
LOG_DIR = LOGS_DIR
KB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = KB_DIR / 'index.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'rag_agent.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('rag_agent')

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
TAVILY_API_KEY    = os.getenv('TAVILY_API_KEY', '')

# ── Static documents (ingested once) ─────────────────────────────────────────
STATIC_DOCS = [
    {
        "name":     "FDA 21 CFR Part 820 Quality System Regulation",
        "url":      "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-820",
        "category": "FDA",
        "id":       "21cfr820",
    },
    {
        "name":     "FDA Design Controls Guidance",
        "url":      "https://www.fda.gov/media/116573/download",
        "category": "FDA",
        "id":       "design_controls_guidance",
    },
    {
        "name":     "EU MDR 2017/745 Full Text",
        "url":      "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32017R0745",
        "category": "EU_MDR",
        "id":       "eu_mdr_2017_745",
    },
]

# ── RSS sources ───────────────────────────────────────────────────────────────
RSS_SOURCES = [
    {"name": "FDA CDRH Guidance", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/guidance/rss.xml",       "category": "FDA"},
    {"name": "IMDRF",             "url": "https://www.imdrf.org/rss.xml",                                                             "category": "IMDRF"},
]

# ── Tavily search queries — run nightly to find new content ──────────────────
TAVILY_QUERIES = [
    # FDA
    "FDA CDRH guidance document 2025 2026 medical device",
    "FDA 510k guidance update medical device quality",
    "FDA warning letter medical device quality system",
    "FDA recall Class I medical device",
    # EU MDR
    "MDCG guidance document EU MDR 2025 2026",
    "EU MDR notified body medical device regulatory",
    "EU MDR technical documentation guidance update",
    # ISO / MDSAP
    "ISO 13485 audit finding MDSAP medical device quality",
    "MDSAP audit approach update 2025 2026",
    # General QA/RA
    "medical device CAPA corrective action best practice",
    "medical device design controls DHF regulatory guidance",
    "ISO 14971 risk management medical device update",
    # San Diego / SoCal
    "San Diego medical device company FDA approval 2025 2026",
    "Biocom California medical device regulatory news",
    # Historical QARA — 50-year knowledge base
    "FDA medical device regulatory history Medical Device Amendments 1976 evolution",
    "21 CFR 820 Quality System Regulation history evolution GMP 1978 1996",
    "ISO 13485 medical devices quality management history evolution standard 1990s 2000s",
    "EU medical devices directive MDD 93/42/EEC history evolution MDR 2017",
    "good manufacturing practice GMP history pharmaceutical medical device FDA origin 1970s",
    "CAPA corrective action preventive action history origin ISO quality management 1980s 1990s",
    "IMDRF GHTF history origin global harmonization medical device regulatory 2000s",
]

CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64


# ── Index ─────────────────────────────────────────────────────────────────────

def load_index():
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text())
        except Exception:
            pass
    return {"documents": {}, "last_run": None}


def save_index(index):
    INDEX_FILE.write_text(json.dumps(index, indent=2))


def doc_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, doc_id: str, doc_name: str, category: str) -> list:
    words  = text.split()
    chunks = []
    i = 0
    n = 0
    while i < len(words):
        chunk_words = words[i:i + CHUNK_SIZE]
        chunks.append({
            "id":        f"{doc_id}_chunk_{n}",
            "doc_id":    doc_id,
            "doc_name":  doc_name,
            "category":  category,
            "chunk_num": n,
            "text":      " ".join(chunk_words),
            "word_count":len(chunk_words),
        })
        i += CHUNK_SIZE - CHUNK_OVERLAP
        n += 1
    return chunks


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_url(url: str, timeout=20) -> str:
    headers = {"User-Agent": "LatitudeMedTech-RAGAgent/2.0"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        import re
        text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()
        return text
    except Exception as e:
        log.warning(f"fetch_url failed {url}: {e}")
        return ""


def save_document(doc_id, doc_name, category, chunks, source="static"):
    cat_dir  = KB_DIR / category
    cat_dir.mkdir(exist_ok=True)
    out_file = cat_dir / f"{doc_id}.json"
    data = {
        "doc_id":      doc_id,
        "doc_name":    doc_name,
        "category":    category,
        "source":      source,
        "ingested_at": datetime.now().isoformat(),
        "chunk_count": len(chunks),
        "chunks":      chunks,
    }
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    log.info(f"  Saved {len(chunks)} chunks -> {out_file.name}")


# ── Tavily integration ────────────────────────────────────────────────────────

def tavily_search(query: str, max_results: int = 5) -> list:
    """Search using Tavily API and return list of result dicts."""
    if not TAVILY_API_KEY:
        return []
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key":          TAVILY_API_KEY,
                "query":            query,
                "search_depth":     "basic",
                "include_answer":   False,
                "include_raw_content": True,
                "max_results":      max_results,
                "include_domains":  [
                    "fda.gov", "eur-lex.europa.eu", "health.ec.europa.eu",
                    "imdrf.org", "iso.org", "emergobyul.com",
                    "raps.org", "medicaldeviceacademy.com",
                    "greenlight.guru", "massdevice.com",
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        log.warning(f"Tavily search failed for '{query}': {e}")
        return []


def ingest_tavily_results(index: dict, results: list, query: str) -> dict:
    """Ingest Tavily search results into knowledge base."""
    ingested = 0
    for result in results:
        url     = result.get("url", "")
        title   = result.get("title", url)
        content = result.get("raw_content") or result.get("content", "")

        if not url or not content or len(content.split()) < 50:
            continue

        doc_id = "tavily_" + doc_hash(url)
        if doc_id in index["documents"]:
            continue

        # Infer category from URL/content
        category = "General"
        url_lower = url.lower()
        if "fda.gov" in url_lower:
            category = "FDA"
        elif "eur-lex.europa.eu" in url_lower or "health.ec.europa.eu" in url_lower:
            category = "EU_MDR"
        elif "imdrf.org" in url_lower:
            category = "IMDRF"
        elif "raps.org" in url_lower:
            category = "Regulatory"

        chunks = chunk_text(content, doc_id, title, category)
        save_document(doc_id, title, category, chunks, source=f"tavily:{query}")
        index["documents"][doc_id] = {
            "name":       title,
            "category":   category,
            "url":        url,
            "chunks":     len(chunks),
            "ingested_at":datetime.now().isoformat(),
            "source":     f"tavily:{query}",
            "hash":       doc_hash(content[:500]),
        }
        ingested += 1

    return index, ingested


# ── Ingestion pipeline ────────────────────────────────────────────────────────

def ingest_static_docs(index):
    log.info("-- Static documents --")
    for doc in STATIC_DOCS:
        if doc["id"] in index["documents"]:
            log.info(f"  SKIP: {doc['name']}")
            continue
        log.info(f"  Fetching: {doc['name']}")
        text = fetch_url(doc["url"])
        if not text:
            continue
        chunks = chunk_text(text, doc["id"], doc["name"], doc["category"])
        save_document(doc["id"], doc["name"], doc["category"], chunks)
        index["documents"][doc["id"]] = {
            "name":       doc["name"],
            "category":   doc["category"],
            "url":        doc["url"],
            "chunks":     len(chunks),
            "ingested_at":datetime.now().isoformat(),
            "hash":       doc_hash(text[:1000]),
        }
        log.info(f"  OK: {doc['name']} ({len(chunks)} chunks)")
        time.sleep(2)
    return index


def ingest_rss(index):
    log.info("-- RSS sources --")
    for source in RSS_SOURCES:
        try:
            feed      = feedparser.parse(source["url"])
            new_count = 0
            for entry in feed.entries[:20]:
                link    = getattr(entry, "link", "")
                title   = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "")
                if not link:
                    continue
                doc_id = "rss_" + doc_hash(link)
                if doc_id in index["documents"]:
                    continue
                content = summary or title
                if len(content.split()) < 30 and link:
                    time.sleep(1)
                    content = fetch_url(link) or content
                chunks = chunk_text(f"{title}\n\n{content}", doc_id, title, source["category"])
                save_document(doc_id, title, source["category"], chunks, source="rss")
                index["documents"][doc_id] = {
                    "name":       title,
                    "category":   source["category"],
                    "url":        link,
                    "chunks":     len(chunks),
                    "ingested_at":datetime.now().isoformat(),
                    "hash":       doc_hash(content[:500]),
                }
                new_count += 1
                time.sleep(1)
            log.info(f"  {source['name']}: {new_count} new documents")
        except Exception as e:
            log.warning(f"  RSS failed {source['name']}: {e}")
    return index


def ingest_tavily(index):
    if not TAVILY_API_KEY:
        log.info("-- Tavily: skipped (TAVILY_API_KEY not set) --")
        return index

    # Deterministic day-of-year rotation — same weekday always hits same query window
    day_bucket  = datetime.now().timetuple().tm_yday
    n           = len(TAVILY_QUERIES)
    offset      = (day_bucket * 8) % n
    run_queries = [TAVILY_QUERIES[(offset + i) % n] for i in range(min(8, n))]
    log.info(f"-- Tavily search ({len(run_queries)}/{len(TAVILY_QUERIES)} queries, rotated) --")
    total_new = 0

    for query in run_queries:
        log.info(f"  Searching: {query[:60]}")
        results = tavily_search(query, max_results=3)
        if results:
            index, count = ingest_tavily_results(index, results, query)
            total_new += count
            if count:
                log.info(f"  +{count} new documents")
        time.sleep(0.5)  # Rate limit respect

    log.info(f"  Tavily total: {total_new} new documents ingested")
    return index


def print_summary(index):
    total_docs   = len(index["documents"])
    total_chunks = sum(d.get("chunks", 0) for d in index["documents"].values())
    by_category  = {}
    by_source    = {"static": 0, "rss": 0, "tavily": 0}

    for d in index["documents"].values():
        cat = d.get("category", "Unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        src = d.get("source", "static")
        if src == "static":
            by_source["static"] += 1
        elif src == "rss":
            by_source["rss"] += 1
        elif "tavily" in src:
            by_source["tavily"] += 1

    print(f"""
+------------------------------------------+
|   Latitude MedTech Knowledge Base        |
+------------------------------------------+
|  Total documents : {total_docs:<22}|
|  Total chunks    : {total_chunks:<22}|
+------------------------------------------+
|  By category:                            |""")
    for cat, count in sorted(by_category.items()):
        print(f"|    {cat:<16}: {count:<22}|")
    print(f"""+------------------------------------------+
|  By source:                              |
|    Static docs  : {by_source['static']:<22}|
|    RSS feeds    : {by_source['rss']:<22}|
|    Tavily search: {by_source['tavily']:<22}|
+------------------------------------------+""")


def main():
    log.info("=" * 44)
    log.info("  Latitude MedTech RAG Ingestion Agent v2")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Tavily: {'enabled' if TAVILY_API_KEY else 'disabled (no key)'}")
    log.info("=" * 44)

    index = load_index()
    docs_before_set = set(index["documents"].keys())
    index = ingest_static_docs(index)
    index = ingest_rss(index)
    index = ingest_tavily(index)
    index["last_run"] = datetime.now().isoformat()
    save_index(index)
    print_summary(index)
    log.info("RAG ingestion complete.")

    # Submit a rich ingestion report to the review queue for Steven's approval.
    try:
        from memory import Memory as _Mem
        _dt         = datetime.now()
        new_doc_ids = set(index["documents"].keys()) - docs_before_set
        new_docs    = len(new_doc_ids)
        total       = len(index["documents"])
        cats: dict  = {}
        for _d in index["documents"].values():
            _c = _d.get("category", "General")
            cats[_c] = cats.get(_c, 0) + 1
        cat_line = ", ".join(f"{v} {k}" for k, v in sorted(cats.items()))
        _date_h  = f"{_dt.strftime('%B')} {_dt.day}, {_dt.year}"
        title    = (f"RAG Ingestion — {new_docs} new doc{'s' if new_docs != 1 else ''} "
                    f"({cat_line}), {_date_h}")

        # Build newly-ingested table rows
        if new_doc_ids:
            table_rows = []
            for _id in sorted(new_doc_ids):
                _meta   = index["documents"][_id]
                _title  = _meta.get("name", _id)
                _url    = _meta.get("url", "")
                _cat    = _meta.get("category", "General")
                _chunks = _meta.get("chunks", 0)
                _link   = f"[{_title}]({_url})" if _url else _title
                table_rows.append(f"| {_link} | {_cat} | {_chunks} |")
            newly_ingested_section = (
                "## Newly Ingested Documents\n\n"
                "| Document | Category | Chunks |\n"
                "|---|---|---|\n" +
                "\n".join(table_rows)
            )
        else:
            newly_ingested_section = (
                "## Newly Ingested Documents\n\n"
                "No new documents ingested this run."
            )

        summary_path = LOG_DIR / f"rag_summary_{_dt.strftime('%Y%m%d_%H%M%S')}.md"
        summary_path.write_text(
            f"# {title}\n\n"
            f"**Run completed:** {_date_h} at {_dt.strftime('%I:%M %p')}\n"
            f"**Total KB documents:** {total}\n"
            f"**New this run:** {new_docs}\n\n"
            "## By Category\n\n" +
            "\n".join(f"- **{k}**: {v} document{'s' if v != 1 else ''}"
                      for k, v in sorted(cats.items())) +
            f"\n\n{newly_ingested_section}\n",
            encoding="utf-8",
        )
        _Mem().submit_for_review("rag_agent", "ingestion_summary", title, str(summary_path))
        log.info(f"  Ingestion summary queued for review: {title}")
    except Exception as _e:
        log.warning(f"  Could not submit ingestion summary for review: {_e}")


if __name__ == "__main__":
    main()
