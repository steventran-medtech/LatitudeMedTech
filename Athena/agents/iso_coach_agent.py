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

from pathconfig import ENV_FILE, AGENTS_DIR, ISO_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

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

CONTENT_DIR     = ISO_DIR
ISO14971_DIR    = ISO_DIR.parent / "iso14971"
LOG_DIR         = LOGS_DIR
CONTENT_DIR.mkdir(parents=True, exist_ok=True)
ISO14971_DIR.mkdir(parents=True, exist_ok=True)
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

# ── ISO 14971:2019 clause map ─────────────────────────────────────────────────
CLAUSES_14971 = {
    "14971.4":     "General Requirements for a Risk Management System",
    "14971.5":     "Risk Analysis",
    "14971.5.2":   "Intended Use and Reasonably Foreseeable Misuse",
    "14971.5.3":   "Hazard Identification",
    "14971.5.4":   "Estimation of Risk",
    "14971.6":     "Risk Evaluation",
    "14971.7":     "Risk Control",
    "14971.7.1":   "Risk Control Option Analysis",
    "14971.7.2":   "Implementation of Risk Control Measures",
    "14971.7.3":   "Residual Risk Evaluation After Risk Control",
    "14971.7.4":   "Benefit-Risk Analysis",
    "14971.7.5":   "Risks Arising from Risk Control Measures",
    "14971.7.6":   "Completeness of Risk Control",
    "14971.8":     "Evaluation of Overall Residual Risk",
    "14971.9":     "Risk Management Review",
    "14971.10":    "Production and Post-Production Activities",
}

COACH_SYSTEM = """You are a medical device QMS expert writing coaching content for Latitude MedTech LLC.

Your audience is early-career QA/RA professionals (0-3 years) in the medical device industry who are learning ISO 13485:2016 for the first time.

Writing rules:
- Plain English. No unnecessary jargon. When you must use a term, define it immediately.
- Practical and grounded. Use realistic medical device company examples (not pharma, not abstract).
- Honest about what's hard. Don't oversimplify.
- Conversational but authoritative — like a knowledgeable colleague explaining something over coffee.
- No filler phrases. No "Great question!" No "It's important to note that..."
- Case studies must be specific: name the device type, company size, the exact failure, and the consequence.

IMPORTANT: This is educational content only. Not regulatory advice. Always note that readers should refer to the actual ISO 13485:2016 standard for official requirements."""

COACH_SYSTEM_14971 = """You are a medical device risk management expert writing coaching content for Latitude MedTech LLC.

Your audience is early-career QA/RA professionals (0-3 years) learning ISO 14971:2019 — the international standard for risk management of medical devices.

Writing rules:
- Plain English. When you use a term (hazard, hazardous situation, harm, severity, probability), define it immediately with a device-specific example.
- Practical: show the risk management process in action with specific device types — implants, diagnostics, SaMD, consumables.
- Honest about judgment calls: risk acceptability criteria and benefit-risk tradeoffs are not black-and-white.
- Conversational but authoritative.
- Case studies must be specific: name the device type, the hazard, the harm pathway, the risk control, and the outcome.

IMPORTANT: This is educational content only. Not regulatory advice. Readers should refer to the actual ISO 14971:2019 standard."""


def generate_lesson(clause_num: str, clause_name: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    is_14971 = clause_num.startswith("14971.")
    std_label = "ISO 14971:2019" if is_14971 else "ISO 13485:2016"
    display_clause = clause_num.replace("14971.", "") if is_14971 else clause_num
    coach_system = COACH_SYSTEM_14971 if is_14971 else COACH_SYSTEM

    # KB grounding
    kb_ctx = ""
    if _kb and _kb.has_content():
        query = f"{std_label} clause {display_clause} {clause_name}"
        chunks = _kb.search(query, top_k=3)
        kb_ctx = _kb.format_context(chunks, max_chars=1500)
    kb_block = f"\n\nKNOWLEDGE BASE CONTEXT:\n{kb_ctx}\n" if kb_ctx else ""

    if is_14971:
        prompt = f"""Generate a complete coaching lesson for ISO 14971:2019 Clause {display_clause}: {clause_name}.
{kb_block}

IMPORTANT: Do NOT include a title heading. The title is added automatically.
Start directly with the first section heading below.

## What This Clause Is About
(2-3 sentences. What risk management problem does this clause solve? Why does it exist?)

## What It Requires (The Essentials)
(The 3-5 most important requirements in plain language. What must you actually do to comply?)

## Case Study 1 — Real World
(Draw from a real FDA recall, warning letter, or MAUDE adverse event where inadequate application of this clause contributed to patient harm or regulatory action. Name the device category and specific failure. Structure: What happened → What clause element was deficient → What compliant practice looks like. If no precisely matching case exists, use the closest analogous enforcement action and note the connection.)

## Case Study 2 — Hypothetical
(Create a realistic fictional scenario. Specify company type and device — e.g. "ClearPath Diagnostics, a 15-person startup making a portable blood glucose monitor." Walk through: the hazard or risk challenge for this clause, the analysis steps, the control chosen, and one mistake the team might make. Instructive, not a success story.)

## Common Mistakes and Audit Findings
(3-4 concrete mistakes or FDA/notified body observations for this clause. No vague generalities.)

## Key Terms to Know
(5-8 terms with plain-English definitions and a device example for each.)

## Check Your Understanding
(5 questions with answers. Include 2 scenario-based questions tied to the case studies above.)

## How This Connects to Your Career
(1 paragraph. How does mastering this clause make you a better risk engineer? Be direct.)

Total length: 1000-1400 words."""

    else:
        prompt = f"""Generate a complete coaching lesson for ISO 13485:2016 Clause {clause_num}: {clause_name}.
{kb_block}

IMPORTANT: Do NOT include a title heading. The title is added automatically.
Start directly with the first section heading below.

## What This Clause Is About
(2-3 sentences. Plain English. What QMS problem does this clause solve?)

## What It Requires (The Essentials)
(The 3-5 most important requirements. Not exhaustive — what an early-career professional must understand.)

## Case Study 1 — Real World
(Draw from a real FDA 483 observation, warning letter, or recall where non-compliance with this clause was cited. Name the device category and specific deficiency. Structure: What the company did wrong → What the inspector cited → What compliant practice looks like. If no precisely matching case exists, use the closest analogous enforcement action and note the connection.)

## Case Study 2 — Hypothetical
(Create a realistic fictional scenario. Specify the company and device — e.g. "MedCore Systems, a 40-person contract manufacturer making orthopedic implants." Walk through how this company encounters a challenge with this clause, what they initially get wrong, and how a strong QA professional fixes it. Make it memorable and instructive.)

## Common Mistakes and Audit Findings
(3-4 concrete mistakes early-career professionals make, or common FDA/notified body observations. No vague generalities.)

## Key Terms to Know
(5-8 terms with plain-English definitions directly relevant to this clause.)

## Check Your Understanding
(5 questions with answers. Include 2 scenario-based questions tied to the case studies above.)

## How This Connects to Your Career
(1 paragraph. How does understanding this clause make you better at your job? Be direct and practical.)

Total length: 1000-1400 words."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system=coach_system,
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
    is_14971 = lesson['clause'].startswith("14971.")
    name_slug = lesson['name'].lower().replace(' ', '_').replace('/', '_')[:40]

    if is_14971:
        clause_no = lesson['clause'][len("14971."):]
        slug      = clause_no.replace('.', '_')
        filename  = f"14971_{slug}_{name_slug}.md"
        out_path  = ISO14971_DIR / filename
        std_label = "ISO 14971:2019"
        display_clause = clause_no
    else:
        slug      = lesson['clause'].replace('.', '_')
        filename  = f"clause_{slug}_{name_slug}.md"
        out_path  = CONTENT_DIR / filename
        std_label = "ISO 13485:2016"
        display_clause = lesson['clause']

    header = f"""---
clause: {lesson['clause']}
title: {lesson['name']}
standard: {std_label}
generated: {lesson['generated']}
word_count: {lesson['word_count']}
status: DRAFT — review before sharing with clients
---

# {std_label} — Clause {display_clause}: {lesson['name']}

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
        # Check both ISO 13485 and ISO 14971 clause maps
        if args.clause in CLAUSES:
            clauses_to_generate = [(args.clause, CLAUSES[args.clause])]
        elif args.clause in CLAUSES_14971:
            clauses_to_generate = [(args.clause, CLAUSES_14971[args.clause])]
        else:
            all_keys = list(CLAUSES.keys()) + list(CLAUSES_14971.keys())
            print(f"Clause {args.clause} not found. Available: {', '.join(all_keys)}")
            sys.exit(1)

    elif args.next or True:
        # --next OR no args: find the first ungenerated clause and do just that one.
        # This is the safe default — never generates the whole standard at once.
        if args.all:
            # Explicit --all flag required to generate everything
            clauses_to_generate = list(CLAUSES.items()) + list(CLAUSES_14971.items())
            print(f"Generating ALL {len(clauses_to_generate)} clauses (--all flag set)...")
        else:
            # Find next ungenerated ISO 13485 clause first, then ISO 14971
            next_clause = None
            for clause_num, clause_name in CLAUSES.items():
                slug = clause_num.replace('.', '_')
                existing = list(CONTENT_DIR.glob(f"clause_{slug}_*.md"))
                if not existing:
                    next_clause = (clause_num, clause_name)
                    break
            if next_clause is None:
                for clause_num, clause_name in CLAUSES_14971.items():
                    clause_no = clause_num[len("14971."):]
                    slug = clause_no.replace('.', '_')
                    existing = list(ISO14971_DIR.glob(f"14971_{slug}_*.md"))
                    if not existing:
                        next_clause = (clause_num, clause_name)
                        break
            if next_clause is None:
                print("All clauses have already been generated.")
                log.info("All ISO 13485 and ISO 14971 clauses already generated — nothing to do.")
                sys.exit(0)
            clauses_to_generate = [next_clause]
            log.info(f"--next mode: generating Clause {next_clause[0]} — {next_clause[1]}")

    generated = []
    for clause_num, clause_name in clauses_to_generate:
        # Skip if already exists
        if clause_num.startswith("14971."):
            clause_no = clause_num[len("14971."):]
            slug = clause_no.replace('.', '_')
            existing = list(ISO14971_DIR.glob(f"14971_{slug}_*.md"))
        else:
            slug = clause_num.replace('.', '_')
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
