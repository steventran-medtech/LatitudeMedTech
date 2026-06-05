"""
Agent 3 — Coaching Brief Agent
================================
Takes a client name or LinkedIn URL and generates a
personalized discovery call prep brief in under 30 seconds.

Usage:
    python coaching_brief.py "Jane Smith"
    python coaching_brief.py "https://linkedin.com/in/janesmith"
    python coaching_brief.py  (prompts you to enter)

Output: Athena/coaching/briefs/YYYY-MM-DD_name.md
"""

import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import anthropic

from pathconfig import ENV_FILE, BRIEFS_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
LOG_DIR = LOGS_DIR

# ── Paths ─────────────────────────────────────────────────────────────────────
BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "coaching_brief.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("coaching_brief")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Latitude MedTech program tiers ────────────────────────────────────────────
PROGRAMS = {
    "career_prep": {
        "name":   "Career Preparation",
        "price":  "$699",
        "target": "Students and early-career professionals entering MedTech",
        "length": "1 month",
        "focus":  "Resume, LinkedIn, interview prep, professional identity",
    },
    "early_career": {
        "name":   "Early Career QA/RA",
        "price":  "$1,499",
        "target": "0-3 years experience in MedTech QA or regulatory",
        "length": "3 months",
        "focus":  "QMS fluency, CAPA, nonconformance, design control fundamentals",
    },
    "mid_career": {
        "name":   "Mid-Career Acceleration",
        "price":  "$1,899",
        "target": "3-7 years, moving toward senior or leadership roles",
        "length": "3 months",
        "focus":  "Knowledge gaps, salary negotiation, executive presence, leadership",
    },
    "career_transition": {
        "name":   "Career Transition",
        "price":  "$2,299",
        "target": "Professionals from adjacent fields entering MedTech",
        "length": "4 months",
        "focus":  "Full repositioning, FDA landscape, network introductions",
    },
}


# ── Input parsing ─────────────────────────────────────────────────────────────

# Domain terms that mark an input as a *topic* rather than a person's name.
TOPIC_SIGNALS = re.compile(
    r"\b(iso|fda|mdr|mdsap|capa|510\(?k\)?|pma|qms|qa|ra|risk|hazard|14971|13485|"
    r"820|part\s*11|compliance|regulatory|quality|audit|design\s*control|validation|"
    r"verification|framework|reporting|submission|clinical|post[- ]?market|"
    r"nonconformance|complaint|ce\s*mark|notified\s*body|gmp|gdp|software|saas|samd)\b",
    re.IGNORECASE,
)

def _looks_like_person(raw: str) -> bool:
    """Conservative person-name heuristic: 1–3 alphabetic tokens, no digits, no
    domain jargon. Ambiguous multi-word inputs fall through to 'topic'."""
    tokens = raw.split()
    if not (1 <= len(tokens) <= 3):
        return False
    if any(ch.isdigit() for ch in raw) or TOPIC_SIGNALS.search(raw):
        return False
    return all(re.fullmatch(r"[A-Za-z][A-Za-z.'\-]*", tok) for tok in tokens)


def parse_input(raw: str) -> dict:
    raw = (raw or "").strip()
    if len(raw) < 2:
        return {"type": "insufficient", "name": raw, "label": raw, "url": None}

    if "linkedin.com/in/" in raw.lower():
        match = re.search(r"linkedin\.com/in/([^/\?]+)", raw, re.IGNORECASE)
        slug  = match.group(1) if match else "unknown"
        name  = slug.replace("-", " ").replace(".", " ").title()
        return {"type": "linkedin", "url": raw, "name": name, "slug": slug, "label": name}

    if _looks_like_person(raw):
        return {"type": "name", "name": raw, "url": None, "label": raw}

    # Anything else is a topic signal, not a client identity.
    return {"type": "topic", "topic": raw, "name": raw, "url": None, "label": raw}


def brief_title(client: dict) -> str:
    """Title reflects the input type — a topic is never labeled as a client."""
    if client.get("type") == "topic":
        return f"Discovery Call Prep — Topic: {client['topic']}"
    return f"Discovery Call Brief — {client['name']}"


# ── Brief generation ──────────────────────────────────────────────────────────

def generate_brief(client_input: dict) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    programs_text = "\n".join(
        f"- {p['name']} ({p['price']}, {p['length']}): {p['focus']} — Target: {p['target']}"
        for p in PROGRAMS.values()
    )

    if client_input["type"] == "linkedin":
        context = f"LinkedIn profile URL: {client_input['url']}\nName inferred from URL: {client_input['name']}"
        instructions = "The LinkedIn URL is provided but you cannot browse it. Generate the brief based on the name and URL slug, noting that full profile context is unavailable. Ask sharp discovery questions that will surface the information you need."
    else:
        context = f"Client name: {client_input['name']}"
        instructions = "No LinkedIn or additional context provided. Generate discovery questions that efficiently surface background, experience level, goals, and fit."

    prompt = f"""You are preparing a discovery call brief for the founder of Latitude MedTech LLC — a San Diego-based MedTech coaching company.

Client information:
{context}

{instructions}

Latitude MedTech Programs:
{programs_text}

Generate a concise discovery call prep brief with these sections:

## What We Know
(Summarize available context. Be honest about what is unknown.)

## Likely Profile
(Based on name/URL, hypothesize: career stage, likely background, probable pain points. Mark these as assumptions.)

## Recommended Program Match
(Which program tier is the most likely fit and why. Include a second option if close.)

## Discovery Call Objectives
(3-4 specific things to learn during the call to confirm fit and program match.)

## Suggested Opening Questions
(5 sharp, open-ended questions — not generic. Designed to quickly surface: experience level, current role, specific pain, motivation for reaching out, timeline.)

## Watch-Outs
(Any signals that might indicate poor fit, scope mismatch, or need to refer elsewhere.)

## Talking Points if Asked About Pricing
(Brief, confident framing for each program tier without being salesy.)

Keep it tight. This brief should take under 2 minutes to read before the call.
Tone: like a smart colleague prepping you, not a formal report.

IMPORTANT: Do NOT include a document title or heading at the top of your response. Start directly with "## What We Know". The title is added by the system automatically."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


# ── Save brief ────────────────────────────────────────────────────────────────

def save_brief(client_input: dict, brief: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    name_slug = client_input["name"].lower().replace(" ", "_")
    name_slug = re.sub(r"[^a-z0-9_]", "", name_slug)
    filename  = f"{date_str}_{name_slug}.md"
    out_path  = BRIEFS_DIR / filename

    header = f"""---
client: {client_input['name']}
linkedin: {client_input.get('url', 'Not provided')}
date: {date_str}
type: Discovery Call Brief
generated_by: Latitude MedTech Coaching Brief Agent
status: Review before call
---

# Discovery Call Brief — {client_input['name']}
*Generated {datetime.now().strftime("%B %d, %Y at %I:%M %p")}*

---

"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + brief)

    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("""
+----------------------------------------------+
|  Latitude MedTech Coaching Brief Agent       |
+----------------------------------------------+
""")

    if not ANTHROPIC_API_KEY:
        log.error(f"ANTHROPIC_API_KEY not set. Check {ENV_FILE}")
        sys.exit(1)

    # Get input from command line or prompt
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    else:
        print("Enter client name or LinkedIn URL:")
        raw_input = input("> ").strip()

    if not raw_input:
        log.error("No client input provided.")
        sys.exit(1)

    client_input = parse_input(raw_input)
    log.info(f"Generating brief for: {client_input['name']}")

    print(f"Generating discovery call brief for {client_input['name']}...")

    try:
        brief    = generate_brief(client_input)
        out_path = save_brief(client_input, brief)
        # Submit to human review queue (Phase 1A gate)
        try:
            from memory import Memory as _Mem
            _Mem().submit_for_review(
                'coaching_brief', 'brief',
                f"Discovery Call Brief — {client_input['name']}", str(out_path))
        except Exception: pass

        print(f"""
+----------------------------------------------------------+
|  Brief Ready                                             |
+----------------------------------------------------------+
|  Client : {client_input['name']:<48}|
|  File   : {str(out_path.name)[:48]:<48}|
+----------------------------------------------------------+

Open: {out_path}
""")
        # Print brief to terminal too
        print("─" * 60)
        print(brief)
        print("─" * 60)

    except Exception as e:
        log.error(f"Brief generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
