"""
Athena Memory Inspector
========================
Query and inspect the shared agent memory store.

Usage:
    python memory_inspect.py              (stats overview)
    python memory_inspect.py --search "CAPA"
    python memory_inspect.py --agent rag_agent
    python memory_inspect.py --recent 20
    python memory_inspect.py --context   (what Claude sees)
    python memory_inspect.py --clear     (wipe memory - careful!)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent))
from memory import Memory


def main():
    parser = argparse.ArgumentParser(description='Athena Memory Inspector')
    parser.add_argument('--search',  help='Search memory for a topic')
    parser.add_argument('--agent',   help='Show events for a specific agent')
    parser.add_argument('--recent',  type=int, default=10, help='Show N recent events')
    parser.add_argument('--context', action='store_true', help='Show Claude context summary')
    parser.add_argument('--content', help='Show content log by type (article_draft, briefing_item, rag_document)')
    parser.add_argument('--clear',   action='store_true', help='Clear all memory (irreversible)')
    args = parser.parse_args()

    mem = Memory()

    if args.clear:
        confirm = input("Clear ALL memory? This cannot be undone. Type YES to confirm: ")
        if confirm == "YES":
            import sqlite3
            with sqlite3.connect(mem.db_path) as conn:
                conn.execute("DELETE FROM events")
                conn.execute("DELETE FROM content_log")
                conn.execute("DELETE FROM agent_state")
            print("Memory cleared.")
        else:
            print("Cancelled.")
        return

    if args.context:
        print("\n[Claude Context Summary]")
        print("-" * 50)
        print(mem.context_summary())
        print("-" * 50)
        return

    if args.search:
        results = mem.search(args.search, limit=20)
        print(f"\nSearch results for '{args.search}': {len(results)} found\n")
        for r in results:
            ts = r['created_at'][:16]
            print(f"  [{ts}] {r.get('agent','?')} | {r.get('action','?')}")
            if r.get('data'):
                try:
                    d = json.loads(r['data']) if isinstance(r['data'], str) else r['data']
                    if isinstance(d, dict):
                        for k, v in list(d.items())[:3]:
                            print(f"    {k}: {str(v)[:80]}")
                except Exception:
                    print(f"    {str(r['data'])[:80]}")
            print()
        return

    if args.content:
        items = mem.recent_content(type=args.content, limit=args.recent)
        print(f"\nContent log [{args.content}]: {len(items)} items\n")
        for item in items:
            ts = item['created_at'][:16]
            print(f"  [{ts}] {item.get('title','?')[:70]}")
            if item.get('url'):
                print(f"    {item['url'][:80]}")
        return

    if args.agent:
        events = mem.recent(agent=args.agent, limit=args.recent)
        print(f"\nEvents for [{args.agent}]: {len(events)} recent\n")
        for e in events:
            ts = e['created_at'][:16]
            print(f"  [{ts}] {e['action']}")
            if e.get('data'):
                try:
                    d = json.loads(e['data'])
                    if isinstance(d, dict):
                        for k, v in list(d.items())[:2]:
                            print(f"    {k}: {str(v)[:60]}")
                except Exception:
                    pass
        return

    # Default: stats overview
    mem.print_stats()

    print("\nRecent activity:")
    print("-" * 50)
    events = mem.recent(limit=args.recent)
    for e in events:
        ts    = e['created_at'][:16]
        agent = e['agent'][:15].ljust(15)
        action = e['action'][:20].ljust(20)
        print(f"  [{ts}] {agent} {action}")

    print(f"\nContext summary (what Claude sees):")
    print("-" * 50)
    print(mem.context_summary())


if __name__ == '__main__':
    main()
