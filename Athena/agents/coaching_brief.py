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

    if client_input["type"] == "topic":
        prompt = _topic_prompt(client_input["topic"], programs_text)
    elif client_input["type"] == "linkedin":
        context = f"LinkedIn profile URL: {client_input['url']}\nName inferred from URL: {client_input['name']}"
        instructions = "The LinkedIn URL is provided but you cannot browse it. Generate the brief based on the name and URL slug, noting that full profile context is unavailable. Ask sharp discovery questions that will surface the information you need."
        prompt = _person_prompt(context, instructions, programs_text)
    else:  # name
        context = f"Client name: {client_input['name']}"
        instructions = "Only a name is provided — no LinkedIn or other context. You have essentially no profile signal, so keep hypotheses minimal and tie each one to a discovery question rather than asserting it as fact."
        prompt = _person_prompt(context, instructions, programs_text)

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _person_prompt(context: str, instructions: str, programs_text: str) -> str:
    return f"""You are preparing a discovery call brief for the founder of Latitude MedTech LLC — a San Diego-based MedTech coaching company.

Client information:
{context}

{instructions}

Latitude MedTech Programs:
{programs_text}

Generate a concise discovery call prep brief with these sections:

## What We Know
(Summarize available context. Be honest about what is unknown.)

## Likely Profile
(Hypotheses ONLY — career stage, possible background, probable pain points. Label as assumptions and phrase each as something to confirm, not a fact. If you have only a name, say so plainly and keep this short.)

## Recommended Program Match
(Which program tier is the most likely fit and why. Include a second option if close. Frame as conditional on what the call confirms.)

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


def _topic_prompt(topic: str, programs_text: str) -> str:
    """Topic-mode brief: no client identity, so we do NOT invent a persona. We prep
    the coach to run discovery around the topic itself and identify who it implies."""
    return f"""You are preparing a discovery call prep brief for the founder of Latitude MedTech LLC — a San Diego-based MedTech coaching company.

This lead came in as a TOPIC SIGNAL, not a person. There is NO name, LinkedIn, company, or role — only the topic the inquiry was tagged to:

TOPIC: {topic}

Critical honesty rule: you have ZERO information about the individual. Do NOT fabricate a persona, background, experience level, or pain points as if they were known. Build the brief around the TOPIC and the questions that will reveal who this person actually is.

Latitude MedTech Programs:
{programs_text}

Generate a concise topic-prep brief with these sections:

## What We Know
(Only the topic signal. State plainly that no client identity was provided and that everything else must be learned on the call.)

## What This Topic Tells Us
(Substantive: what does "{topic}" mean in MedTech QA/RA? Why would someone seek coaching on it? What range of roles/experience levels typically engage with it — stated as a RANGE of possibilities, not an assumption about this person.)

## What We Don't Know Yet
(The specific gaps to close on the call: who they are, their role, seniority, employer context, why now, timeline.)

## Discovery Call Objectives
(3-4 specific things to learn to identify the person and confirm fit.)

## Suggested Opening Questions
(5 sharp, open-ended questions — topic-aware. Use "{topic}" as the natural entry point to surface role, experience level, the specific pain behind the inquiry, motivation, and timeline.)

## Possible Program Fits
(Map the plausible programs to the experience RANGE this topic implies — explicitly conditional on what the call reveals. Do not pick one as if the person were known.)

## Watch-Outs
(Signals that would indicate poor fit, scope mismatch, or a need to refer elsewhere.)

## Talking Points if Asked About Pricing
(Brief, confident framing for each program tier without being salesy.)

Keep it tight — under 2 minutes to read before the call.
Tone: like a smart colleague prepping you, not a formal report.

IMPORTANT: Do NOT include a document title or heading at the top of your response. Start directly with "## What We Know". The title is added by the system automatically."""


# ── Save brief ────────────────────────────────────────────────────────────────

def save_brief(client_input: dict, brief: str) -> Path:
    date_str  = datetime.now().strftime("%Y-%m-%d")
    label     = client_input.get("label") or client_input.get("name", "")
    name_slug = re.sub(r"[^a-z0-9_]", "", label.lower().replace(" ", "_"))[:50] or "brief"
    is_topic  = client_input.get("type") == "topic"
    filename  = f"{date_str}_{'topic_' if is_topic else ''}{name_slug}.md"
    out_path  = BRIEFS_DIR / filename

    title = brief_title(client_input)
    # A topic brief has no client identity — record the topic, not a fake client.
    subject_lines = (
        f"topic: {client_input['topic']}\nclient: Not provided (topic-only lead)"
        if is_topic else
        f"client: {client_input['name']}\nlinkedin: {client_input.get('url') or 'Not provided'}"
    )
    header = f"""---
{subject_lines}
date: {date_str}
type: {'Topic Prep Brief' if is_topic else 'Discovery Call Brief'}
generated_by: Latitude MedTech Coaching Brief Agent
status: Review before call
---

# {title}
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
    if client_input["type"] == "insufficient":
        log.error("Input too short — enter a client name, LinkedIn URL, or topic.")
        sys.exit(1)

    label = client_input.get("label", client_input["name"])
    log.info(f"Generating {client_input['type']} brief for: {label}")
    print(f"Generating {client_input['type']} brief for {label}...")

    try:
        brief    = generate_brief(client_input)
        out_path = save_brief(client_input, brief)
        # Submit to human review queue (Phase 1A gate)
        try:
            from memory import Memory as _Mem
            _Mem().submit_for_review(
                'coaching_brief', 'brief', brief_title(client_input), str(out_path))
        except Exception: pass

        subject = "Topic " if client_input["type"] == "topic" else "Client"
        print(f"""
+----------------------------------------------------------+
|  Brief Ready                                             |
+----------------------------------------------------------+
|  {subject:<7}: {label[:46]:<46}|
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
