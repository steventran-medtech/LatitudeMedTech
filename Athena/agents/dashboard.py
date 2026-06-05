"""
Latitude MedTech — Token & Usage Dashboard
============================================
Run anytime to see API usage, token spend, and agent activity.

Usage:
    python dashboard.py           (30-day report)
    python dashboard.py --days 7  (7-day report)
    python dashboard.py --kb      (knowledge base stats)
    python dashboard.py --content (content history)
    python dashboard.py --all     (everything)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

from pathlib import Path as _Path
_AGENTS = _Path(__file__).resolve().parent
sys.path.insert(0, str(_AGENTS))

try:
    from memory import Memory
except ImportError:
    print("ERROR: memory.py not found in agents/")
    sys.exit(1)


def kb_report(mem):
    stats = mem.get_kb_stats()
    print(f"""
+--------------------------------------------------+
|  Knowledge Base                                  |
+--------------------------------------------------+
|  Total documents : {str(stats['total_docs']):<29}|
|  Total chunks    : {str(stats['total_chunks']):<29}|
+--------------------------------------------------+
|  By category:                                    |""")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"|    {cat:<20} {str(count):<25}|")
    print("+--------------------------------------------------+")


def content_report(mem):
    topics = mem.get_recent_topics(days=90)
    print(f"""
+--------------------------------------------------+
|  Content History (last 90 days)                  |
+--------------------------------------------------+
|  Total items: {str(len(topics)):<34}|
+--------------------------------------------------+""")
    for t in topics[:20]:
        date = t['timestamp'][:10]
        title = t['title'][:42]
        print(f"|  {date}  {title:<42}|")
    if len(topics) > 20:
        print(f"|  ... and {len(topics)-20} more                                  |")
    print("+--------------------------------------------------+")


def events_report(mem):
    rows = mem.conn.execute("""
        SELECT agent, action, subject, timestamp
        FROM events
        ORDER BY timestamp DESC
        LIMIT 20
    """).fetchall()
    print(f"""
+--------------------------------------------------+
|  Recent Agent Activity                           |
+--------------------------------------------------+""")
    for r in rows:
        ts    = r['timestamp'][:16].replace('T', ' ')
        agent = r['agent'][:14]
        action = r['action'][:12]
        print(f"|  {ts}  {agent:<14} {action:<12}      |")
    print("+--------------------------------------------------+")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days',    type=int, default=30)
    parser.add_argument('--kb',      action='store_true')
    parser.add_argument('--content', action='store_true')
    parser.add_argument('--events',  action='store_true')
    parser.add_argument('--all',     action='store_true')
    args = parser.parse_args()

    mem = Memory()

    print(f"\nLatitude MedTech Dashboard — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    show_all = args.all or not any([args.kb, args.content, args.events])

    if show_all or not (args.kb or args.content or args.events):
        mem.print_token_report(days=args.days)

    if args.kb or args.all:
        kb_report(mem)

    if args.content or args.all:
        content_report(mem)

    if args.events or args.all:
        events_report(mem)

    mem.close()


if __name__ == '__main__':
    main()
