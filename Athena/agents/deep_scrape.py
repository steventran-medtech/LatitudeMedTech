"""
Latitude MedTech — Deep Historical Knowledge Scraper
======================================================
One-time deep scrape covering 2010–present.

Focus areas:
1. Major MedTech M&A deals (2010–present)
2. FDA recalls of products post-acquisition/merger
3. Warning letters tied to acquired companies
4. Regulatory failures following M&A integration

Runs ONCE. Memory prevents re-ingestion on subsequent runs.
Estimated runtime: 10–20 minutes depending on connection speed.

Run:
    python deep_scrape.py
"""

import os
import sys
import json
import time
import hashlib
import logging
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from pathconfig import ENV_FILE, AGENTS_DIR, KB_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

try:
    from memory import Memory
    mem = Memory()
except ImportError:
    mem = None

LOG_DIR = LOGS_DIR
KB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'deep_scrape.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('deep_scrape')

TAVILY_API_KEY    = os.getenv('TAVILY_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64

# ── M&A + Recall search queries ───────────────────────────────────────────────
# Structured to minimize API calls while maximizing coverage
# Each query targets a specific year range or topic cluster

MA_QUERIES = [
    # Major M&A deals by era
    "medical device acquisition merger 2010 2011 2012 FDA regulatory",
    "medical device acquisition merger 2013 2014 2015 FDA regulatory",
    "medical device acquisition merger 2016 2017 2018 FDA regulatory",
    "medical device acquisition merger 2019 2020 2021 FDA regulatory",
    "medical device acquisition merger 2022 2023 2024 2025 FDA regulatory",

    # Post-acquisition recalls
    "FDA recall medical device post acquisition integration failure 2010 2015",
    "FDA recall medical device post acquisition integration failure 2016 2020",
    "FDA recall medical device post acquisition integration failure 2021 2025",

    # Warning letters post M&A
    "FDA warning letter acquired company quality system failure medical device",
    "FDA 483 observations post merger acquisition medical device manufacturer",

    # Specific high-profile cases
    "Medtronic acquisition recall FDA warning letter quality system",
    "Abbott acquisition recall FDA warning letter quality system",
    "Stryker acquisition recall FDA warning letter quality system",
    "Boston Scientific acquisition recall FDA warning letter",
    "Johnson Johnson medical device acquisition recall FDA",
    "Becton Dickinson acquisition recall FDA warning letter",
    "Zimmer Biomet acquisition recall FDA quality system",
    "Edwards Lifesciences acquisition recall FDA",
    "Integra LifeSciences acquisition recall FDA warning",
    "Natus Medical acquisition recall FDA",

    # Integration failure patterns
    "medical device quality system breakdown post acquisition FDA inspection",
    "CAPA failure post merger medical device recall FDA",
    "design controls failure acquired medical device company recall",
    "post market surveillance failure acquisition medical device FDA",

    # EU MDR M&A impact
    "EU MDR acquisition merger medical device regulatory compliance failure",
    "CE mark withdrawal post acquisition medical device EU",

    # ISO 13485 M&A
    "ISO 13485 audit failure post acquisition medical device MDSAP",
    "quality management system integration failure medical device merger",

    # Recall databases
    "FDA class I recall cardiovascular device acquisition 2010 2020",
    "FDA class I recall orthopedic device acquisition 2010 2020",
    "FDA class I recall diagnostic device acquisition 2010 2020",
    "FDA class I recall surgical device acquisition 2015 2025",
]

# Static high-value URLs to scrape directly
STATIC_URLS = [
    {
        "name":     "FDA Enforcement Reports Index",
        "url":      "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
        "category": "FDA_Recalls",
        "id":       "fda_recalls_index",
    },
    {
        "name":     "FDA Warning Letters Medical Devices",
        "url":      "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters",
        "category": "FDA_Warning_Letters",
        "id":       "fda_warning_letters_index",
    },
    {
        "name":     "FDA Device Recalls Database",
        "url":      "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfRES/res.cfm",
        "category": "FDA_Recalls",
        "id":       "fda_device_recalls_db",
    },
    {
        "name":     "MedTech M&A Overview Emergo",
        "url":      "https://www.emergobyul.com/blog/medical-device-mergers-acquisitions",
        "category": "MA_Analysis",
        "id":       "emergo_ma_overview",
    },
    {
        "name":     "FDA CDRH Recalls 2010-2025",
        "url":      "https://www.fda.gov/medical-devices/medical-device-recalls/2023-medical-device-recalls",
        "category": "FDA_Recalls",
        "id":       "fda_recalls_2023",
    },
]


# ── Utilities ─────────────────────────────────────────────────────────────────

def doc_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:16]


def chunk_text(text, doc_id, doc_name, category):
    words  = text.split()
    chunks = []
    i, n   = 0, 0
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


def save_document(doc_id, doc_name, category, chunks, source="deep_scrape"):
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


def already_ingested(url):
    if mem and mem.url_ingested(url):
        return True
    url_hash = doc_hash(url)
    # Also check KB dir
    for f in KB_DIR.rglob(f"*{url_hash}*.json"):
        return True
    return False


def fetch_url(url, timeout=15):
    headers = {"User-Agent": "LatitudeMedTech-DeepScrape/1.0"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        import re
        text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()
        return text[:50000]  # Cap at 50k chars per page
    except Exception as e:
        log.warning(f"  fetch failed {url}: {e}")
        return ""


# ── Tavily deep search ────────────────────────────────────────────────────────

def tavily_search(query, max_results=8):
    if not TAVILY_API_KEY:
        return []
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key":           TAVILY_API_KEY,
                "query":             query,
                "search_depth":      "advanced",  # Deep search
                "include_answer":    False,
                "include_raw_content": True,
                "max_results":       max_results,
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        log.warning(f"  Tavily failed '{query[:50]}': {e}")
        return []


def ingest_tavily_result(result, category="MA_Recalls"):
    url     = result.get("url", "")
    title   = result.get("title", url)
    content = result.get("raw_content") or result.get("content", "")

    if not url or not content or len(content.split()) < 30:
        return False

    if already_ingested(url):
        return False

    # Infer category
    url_l = url.lower()
    if "fda.gov" in url_l:
        cat = "FDA_Recalls" if "recall" in url_l or "recall" in title.lower() else "FDA"
    elif "warning" in url_l or "warning" in title.lower():
        cat = "FDA_Warning_Letters"
    else:
        cat = category

    doc_id = "deep_" + doc_hash(url)
    chunks = chunk_text(content, doc_id, title, cat)
    save_document(doc_id, title, cat, chunks)

    if mem:
        mem.register_document('deep_scrape', title, url=url,
                              category=cat, chunks=len(chunks))

    return True


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    log.info("=" * 56)
    log.info("  Latitude MedTech Deep Historical Scraper")
    log.info("  MedTech M&A + Post-Acquisition Recalls 2010–Present")
    log.info(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Tavily: {'enabled' if TAVILY_API_KEY else 'DISABLED — set TAVILY_API_KEY'}")
    log.info("=" * 56)

    if not TAVILY_API_KEY:
        log.error("TAVILY_API_KEY not set. Cannot run deep scrape.")
        log.error(f"Check {ENV_FILE}")
        sys.exit(1)

    total_new = 0
    start     = datetime.now()

    # ── Phase 1: Static high-value URLs ──────────────────────────────────────
    log.info(f"\nPhase 1: Scraping {len(STATIC_URLS)} static sources...")
    for doc in STATIC_URLS:
        if already_ingested(doc['url']):
            log.info(f"  SKIP (exists): {doc['name']}")
            continue
        log.info(f"  Fetching: {doc['name']}")
        text = fetch_url(doc['url'])
        if not text:
            continue
        chunks = chunk_text(text, doc['id'], doc['name'], doc['category'])
        save_document(doc['id'], doc['name'], doc['category'], chunks)
        if mem:
            mem.register_document('deep_scrape', doc['name'], url=doc['url'],
                                  category=doc['category'], chunks=len(chunks))
        log.info(f"  OK: {len(chunks)} chunks")
        total_new += 1
        time.sleep(1)

    # ── Phase 2: Tavily M&A queries ───────────────────────────────────────────
    log.info(f"\nPhase 2: Running {len(MA_QUERIES)} targeted M&A queries via Tavily...")
    log.info("Each query uses deep search (advanced mode) for maximum coverage.\n")

    for i, query in enumerate(MA_QUERIES):
        elapsed = (datetime.now() - start).seconds
        log.info(f"  [{i+1}/{len(MA_QUERIES)}] ({elapsed}s elapsed) {query[:65]}")

        results = tavily_search(query, max_results=8)
        new_this_query = 0

        for result in results:
            if ingest_tavily_result(result):
                new_this_query += 1
                total_new += 1

        log.info(f"  -> {new_this_query} new documents ingested")
        time.sleep(0.8)  # Respectful rate limiting

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start).seconds
    if mem:
        stats = mem.get_kb_stats()
        mem.log_event('deep_scrape', 'complete', metadata={
            'new_docs': total_new, 'elapsed_sec': elapsed
        })

    # Count what's in KB now
    total_files = sum(1 for _ in KB_DIR.rglob('*.json') if _.name != 'index.json')

    print(f"""
+----------------------------------------------------------+
|  Deep Scrape Complete                                    |
+----------------------------------------------------------+
|  New documents ingested : {str(total_new):<32}|
|  Total KB files         : {str(total_files):<32}|
|  Elapsed time           : {str(elapsed) + 's':<32}|
+----------------------------------------------------------+
|  Knowledge base: {str(KB_DIR):<39}|
+----------------------------------------------------------+
""")

    log.info("Deep scrape complete.")


if __name__ == '__main__':
    main()
