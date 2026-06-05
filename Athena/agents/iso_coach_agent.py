"""
Agent 4 — ISO 13485 Coaching Content Agent
============================================
Generates structured coaching lesson content for Latitude MedTech
clients working through ISO 13485 fundamentals.

Produces:
- Lesson explanations (plain English)
- Real-world examples
- Quiz questions with answers
- Key terms glossary
- Common audit findings related to each clause

Usage:
    python iso_coach_agent.py              (interactive menu)
    python iso_coach_agent.py --clause 4.2 (specific clause)
    python iso_coach_agent.py --all        (generate all clauses)

Output: ~/Athena/coaching/iso13485/
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv(Path.home() / 'Athena' / 'voice' / '.env')

sys.path.insert(0, str(Path.home() / 'Athena' / 'agents'))
try:
    from agent_base import AgentBase
    _base = AgentBase("iso")
except Exception:
    _base = None

try:
    from kb_query import KBQuery
    _kb = KBQuery()
except Exception:
    _kb = None

CONTENT_DIR = Path.home() / 'Athena' / 'coaching' / 'iso13485'
LOG_DIR     = Path.home() / 'Athena' / 'logs'
CONTENT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / 'iso_coach.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('iso_coach')

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# ── ISO 13485:2016 clause map ─────────────────────────────────────────────────
CLAUSES = {
    "4.1":  "General QMS Requirements",
    "4.2":  "Documentation Requirements",
    "4.2.3":"Medical Device File",
    "4.2.4":"Document Control",
    "4.2.5":"Records Control",
    "5.1":  "Management Commitment",
    "5.2":  "Customer Focus",
    "5.3":  "Quality Policy",
    "5.4":  "Planning",
    "5.5":  "Responsibility and Authority",
    "5.6":  "Management Review",
    "6.1":  "Resource Management",
    "6.2":  "Human Resources",
    "6.3":  "Infrastructure",
    "6.4":  "Work Environment",
    "7.1":  "Planning of Product Realization",
    "7.2":  "Customer-Related Processes",
    "7.3":  "Design and Development",
    "7.4":  "Purchasing",
    "7.5":  "Production and Service Provision",
    "7.6":  "Control of Monitoring Equipment",
    "8.1":  "Measurement, Analysis and Improvement",
    "8.2":  "Monitoring and Measurement",
    "8.2.1":"Feedback",
    "8.2.2":"Internal Audit",
    "8.2.3":"Process Monitoring",
    "8.2.4":"Product Monitoring",
    "8.3":  "Control of Nonconforming Product",
    "8.4":  "Analysis of Data",
    "8.5":  "Improvement — CAPA",
    "8.5.2":"Corrective Action",
    "8.5.3":"Preventive Action",
}

COACH_SYSTEM = """You are a medical device QMS expert writing coaching content for Latitude MedTech LLC.

Your audience is early-career QA/RA professionals (0-3 years) in the medical device industry who are learning ISO 13485:2016 for the first time.

Writing rules:
- Plain English. No unnecessary jargon. When you must use a term, define it immediately.
- Practical and grounded. Use realistic medical device company examples (not pharma, not abstract).
- Honest about what's hard. Don't oversimplify.
- Conversational but authoritative — like a knowledgeable colleague explaining something over coffee.
- No filler phrases. No "Great question!" No "It's important to note that..."

IMPORTANT: This is educational content only. Not regulatory advice. Always note that readers should refer to the actual ISO 13485:2016 standard for official requirements."""


def generate_lesson(clause_num: str, clause_name: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # KB grounding — pull relevant chunks before hitting the API
    kb_ctx = ""
    if _kb and _kb.has_content():
        chunks = _kb.search(f"ISO 13485 clause {clause_num} {clause_name}", top_k=3)
        kb_ctx = _kb.format_context(chunks, max_chars=1500)
    kb_block = f"\n\nKNOWLEDGE BASE CONTEXT:\n{kb_ctx}\n" if kb_ctx else ""

    prompt = f"""Generate a complete coaching lesson for ISO 13485:2016 Clause {clause_num}: {clause_name}.
{kb_block}

IMPORTANT: Do NOT include a title heading. The title is added automatically by the system.
Start your response directly with the first section heading below.

Structure the lesson with these exact sections:

## What This Clause Is About
(2-3 sentences. Plain English. What problem does this clause solve?)

## What It Requires (The Essentials)
(The 3-5 most important requirements in plain language. Not exhaustive — the things an early-career professional must understand.)

## What This Looks Like in Practice
(A realistic example at a small-to-mid size medical device company. Walk through how a real team handles this. Be specific — mention real document names, job titles, workflows.)

## Common Mistakes and Audit Findings
(3-4 specific mistakes early-career professionals make or common FDA/notified body findings related to this clause. Be concrete.)

## Key Terms to Know
(5-8 terms with plain-English definitions. Only terms directly relevant to this clause.)

## Check Your Understanding
(5 quiz questions with answers. Mix of conceptual and applied. Include 2 scenario-based questions.)

## How This Connects to Your Career
(1 paragraph. How does understanding this clause make you better at your job and more valuable to employers? Be direct and practical.)

Keep each section focused and useful. Total length: 800-1200 words."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=COACH_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    content = resp.content[0].text.strip()

    return {
        "clause":     clause_num,
        "name":       clause_name,
        "content":    content,
        "generated":  datetime.now().isoformat(),
        "word_count": len(content.split()),
    }


def save_lesson(lesson: dict) -> Path:
    slug     = lesson['clause'].replace('.', '_')
    filename = f"clause_{slug}_{lesson['name'].lower().replace(' ', '_').replace('/', '_')[:40]}.md"
    out_path = CONTENT_DIR / filename

    header = f"""---
clause: {lesson['clause']}
title: {lesson['name']}
generated: {lesson['generated']}
word_count: {lesson['word_count']}
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause {lesson['clause']}: {lesson['name']}

"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header + lesson['content'])

    return out_path


def show_menu():
    print("\nISO 13485 Coaching Content Agent")
    print("=" * 40)
    print("\nAvailable clauses:\n")
    items = list(CLAUSES.items())
    for i, (num, name) in enumerate(items):
        print(f"  {i+1:2}. Clause {num:<6} {name}")
    print(f"\n  {len(items)+1:2}. Generate ALL clauses")
    print(f"  {len(items)+2:2}. Exit\n")
    return items


def main():
    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--clause', help='Specific clause number e.g. 8.5')
    parser.add_argument('--next',   action='store_true',
                        help='Generate the next ungenerated clause only (default from UI)')
    parser.add_argument('--all',    action='store_true',
                        help='Generate ALL clauses (use with caution)')
    args = parser.parse_args()

    if args.clause:
        # Generate one specific clause
        if args.clause not in CLAUSES:
            print(f"Clause {args.clause} not found. Available: {', '.join(CLAUSES.keys())}")
            sys.exit(1)
        clauses_to_generate = [(args.clause, CLAUSES[args.clause])]

    elif args.next or True:
        # --next OR no args: find the first ungenerated clause and do just that one.
        # This is the safe default — never generates the whole standard at once.
        if args.all:
            # Explicit --all flag required to generate everything
            clauses_to_generate = list(CLAUSES.items())
            print(f"Generating ALL {len(clauses_to_generate)} clauses (--all flag set)...")
        else:
            # Find next ungenerated clause
            next_clause = None
            for clause_num, clause_name in CLAUSES.items():
                slug = clause_num.replace('.', '_')
                existing = list(CONTENT_DIR.glob(f"clause_{slug}_*.md"))
                if not existing:
                    next_clause = (clause_num, clause_name)
                    break
            if next_clause is None:
                print("All clauses have already been generated.")
                log.info("All ISO 13485 clauses already generated — nothing to do.")
                sys.exit(0)
            clauses_to_generate = [next_clause]
            log.info(f"--next mode: generating Clause {next_clause[0]} — {next_clause[1]}")

    generated = []
    for clause_num, clause_name in clauses_to_generate:
        # Skip if already exists
        slug     = clause_num.replace('.', '_')
        existing = list(CONTENT_DIR.glob(f"clause_{slug}_*.md"))
        if existing:
            log.info(f"  SKIP (exists): Clause {clause_num} — {clause_name}")
            continue

        log.info(f"  Generating: Clause {clause_num} — {clause_name}")
        try:
            lesson   = generate_lesson(clause_num, clause_name)
            out_path = save_lesson(lesson)
            generated.append((clause_num, clause_name, out_path))
            log.info(f"  Saved: {out_path.name} ({lesson['word_count']} words)")
        except Exception as e:
            log.error(f"  Failed {clause_num}: {e}")

    print(f"\n{'=' * 50}")
    print(f"  Generated {len(generated)} lessons")
    print(f"  Location: {CONTENT_DIR}")
    print(f"{'=' * 50}\n")
    for num, name, path in generated:
        print(f"  Clause {num}: {path.name}")


if __name__ == '__main__':
    main()
