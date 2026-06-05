"""
Latitude MedTech — Agent Learning System
==========================================
Each agent has a curated set of learning sources relevant to its domain
and to the broader skills expected of a consulting firm employee:
business strategy, Six Sigma, AI/ML, and industry-specific knowledge.

Run manually:
    python agent_learning.py                  # all agents
    python agent_learning.py --agent content  # one agent

How it works:
1. Fetches RSS/web content from each agent's source list
2. Deduplicates against the knowledge base (skip already-seen URLs)
3. Extracts and chunks article text
4. Ingests into ~/Athena/knowledge_base/ tagged by agent + domain
5. Logs to agent_learning table so HR can track velocity
"""

import os
import sys
import json
import re
import hashlib
import logging
import argparse
import requests
import feedparser
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

from pathconfig import ENV_FILE, AGENTS_DIR, KB_DIR as _KB_ROOT, LOGS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

from memory import Memory
from kb_query import KBQuery

KB_DIR  = _KB_ROOT / 'learning'
LOG_DIR = LOGS_DIR
KB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "agent_learning.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("agent_learning")

mem = Memory()

# ── Learning source registry ──────────────────────────────────────────────────
# The registry now lives in learning_sources.py (dependency-free) so lightweight
# tools — skills_profile.py, dashboards — can import it without pulling in
# feedparser/requests. This module re-exports it unchanged.
from learning_sources import AGENT_SOURCES

# ── Fetch helpers ─────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "LatitudeMedTech-AgentLearning/1.0"}
MAX_ITEMS_PER_SOURCE = 5
MAX_TEXT_CHARS = 2000


def _fetch_rss(url: str) -> List[Dict]:
    try:
        feed  = feedparser.parse(url)
        items = []
        for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
            text = ""
            if hasattr(entry, "summary"):
                text = re.sub(r"<[^>]+>", "", entry.summary)[:MAX_TEXT_CHARS]
            elif hasattr(entry, "content"):
                text = re.sub(r"<[^>]+>", "", entry.content[0].value)[:MAX_TEXT_CHARS]
            items.append({
                "title":   getattr(entry, "title", ""),
                "url":     getattr(entry, "link",  ""),
                "text":    text,
                "date":    getattr(entry, "published", datetime.now().isoformat()),
            })
        return items
    except Exception as e:
        log.warning(f"RSS fetch failed ({url}): {e}")
        return []


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    words  = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks if chunks else [text]


def _save_to_kb(agent: str, source_name: str, domain: str,
                title: str, url: str, text: str) -> int:
    """Chunk and save to knowledge_base/learning/. Returns chunks written."""
    if not text.strip():
        return 0
    slug     = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40]
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    fname    = KB_DIR / f"{agent}_{url_hash}.json"

    chunks = _chunk_text(text)
    data   = {
        "agent":     agent,
        "doc_name":  title,
        "category":  domain,
        "source":    source_name,
        "url":       url,
        "ingested":  datetime.now().isoformat(),
        "chunks": [
            {"text": c, "doc_name": title, "category": domain}
            for c in chunks
        ],
    }
    fname.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(chunks)


# ── Per-agent learning run ────────────────────────────────────────────────────

def learn(agent_name: str, max_new: int = 10) -> Dict:
    """
    Fetch new items for an agent from its source list + shared sources.
    Returns {"agent": ..., "new_items": ..., "chunks": ...}
    """
    sources = AGENT_SOURCES.get(agent_name, []) + AGENT_SOURCES["_shared"]
    new_items = 0
    new_chunks = 0

    log.info(f"[{agent_name}] Starting learning run ({len(sources)} sources)")

    for source in sources:
        if new_items >= max_new:
            break
        items = _fetch_rss(source["url"]) if source["type"] == "rss" else []

        for item in items:
            if not item["url"] or not item["title"]:
                continue
            if mem.learning_ingested(item["url"]):
                continue   # already seen
            if mem.url_ingested(item["url"]):
                continue   # already in main KB

            chunks = _save_to_kb(
                agent_name, source["name"], source["domain"],
                item["title"], item["url"], item["text"]
            )
            if chunks == 0:
                continue

            mem.log_learning(
                agent=agent_name,
                source_name=source["name"],
                title=item["title"],
                source_url=item["url"],
                domain=source["domain"],
                chunks_added=chunks,
            )
            new_items  += 1
            new_chunks += chunks
            log.info(f"  [{agent_name}] Learned: {item['title'][:60]} ({chunks} chunks)")

            if new_items >= max_new:
                break

    # Update agent health record
    mem.upsert_agent_health(
        agent_name,
        last_learning=datetime.now().isoformat() if new_items > 0 else None,
    )

    log.info(f"[{agent_name}] Done — {new_items} new items, {new_chunks} chunks")
    return {"agent": agent_name, "new_items": new_items, "chunks": new_chunks}


# ── Main ──────────────────────────────────────────────────────────────────────

ALL_AGENTS = ["content", "briefing", "iso", "coaching", "fda", "rag",
              "consulting", "ma_intelligence", "voice_bridge"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", type=str, default="",
                        help="Single agent name, or blank for all")
    parser.add_argument("--max",   type=int, default=10,
                        help="Max new items per agent per source run")
    args = parser.parse_args()

    targets = [args.agent] if args.agent else ALL_AGENTS
    results = []

    log.info("=" * 50)
    log.info("  Latitude MedTech — Agent Learning Run")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 50)

    for agent in targets:
        r = learn(agent, max_new=args.max)
        results.append(r)

    total_items  = sum(r["new_items"] for r in results)
    total_chunks = sum(r["chunks"] for r in results)

    log.info("")
    log.info("Learning run complete:")
    for r in results:
        log.info(f"  {r['agent']:<12} {r['new_items']:>3} items  {r['chunks']:>4} chunks")
    log.info(f"  {'TOTAL':<12} {total_items:>3} items  {total_chunks:>4} chunks")


if __name__ == "__main__":
    main()
