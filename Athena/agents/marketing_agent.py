"""
Latitude MedTech — Marketing & Sales Agent
===========================================
Guerilla marketing manager for Latitude MedTech LLC.
Focus: SoCal MedTech corridor, off-LinkedIn channels.

Channels tracked:
  - Conference / event circuit (MD&M, Biocom, RAPS, AdvaMed)
  - Podcast outreach (targeted placements, not ads)
  - Speaking engagements (Biocom chapters, UC extensions, FDA workshops)
  - Substack / MedTech Meridian newsletter
  - Regulatory clinic model (free office hours → paid engagements)
  - Referral network (Biocom members, former colleagues)
  - FDA docket participation (comment submissions → public credibility)
  - Warm direct outreach (email to QA/RA Directors, not cold LinkedIn)

Usage:
    python marketing_agent.py                      # weekly brief (default)
    python marketing_agent.py --plan               # 30-60-90 day guerilla plan
    python marketing_agent.py --outreach "TARGET"  # personalised outreach copy
    python marketing_agent.py --pipeline           # view/update pipeline
    python marketing_agent.py --events             # upcoming SoCal MedTech events
    python marketing_agent.py --scorecard          # marketing KPIs vs targets
    python marketing_agent.py learn                # ingest new targets into KB
"""

import os
import sys
import json
import logging
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, date
from textwrap import dedent

import anthropic
from dotenv import load_dotenv

from pathconfig import ENV_FILE, LOGS_DIR, KB_DIR, MEMORY_DIR, OPS_DIR, AGENTS_DIR
import sys as _sys
_sys.path.insert(0, str(AGENTS_DIR))

load_dotenv(ENV_FILE)

try:
    from memory import Memory as _Memory
    _mem = _Memory()
except Exception:
    _mem = None

LOGS_DIR.mkdir(parents=True, exist_ok=True)
MARKETING_DIR = OPS_DIR / "marketing"
MARKETING_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_DB   = MARKETING_DIR / "pipeline.db"
OUTREACH_DIR  = MARKETING_DIR / "outreach"
OUTREACH_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "marketing_agent.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("marketing_agent")

MODEL        = "claude-sonnet-4-6"
CURRENT_DATE = date.today().isoformat()

# ── Pipeline DB ───────────────────────────────────────────────────────────────

def init_db():
    """Initialise the marketing pipeline database."""
    with sqlite3.connect(PIPELINE_DB) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS targets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                type        TEXT NOT NULL,     -- conference|podcast|speaking|referral|prospect|clinic
                org         TEXT,
                contact     TEXT,
                status      TEXT DEFAULT 'identified',
                                               -- identified|contacted|in_discussion|converted|closed
                priority    INTEGER DEFAULT 2, -- 1=high 2=medium 3=low
                notes       TEXT,
                next_action TEXT,
                next_date   TEXT,
                created_at  TEXT DEFAULT (date('now')),
                updated_at  TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS activities (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id   INTEGER REFERENCES targets(id),
                type        TEXT NOT NULL,     -- email|call|event|content|podcast|speak
                description TEXT NOT NULL,
                outcome     TEXT,
                logged_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS kpis (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start  TEXT NOT NULL,
                outreach    INTEGER DEFAULT 0,  -- new contacts made
                responses   INTEGER DEFAULT 0,  -- responses received
                meetings    INTEGER DEFAULT 0,  -- discovery calls booked
                conversions INTEGER DEFAULT 0,  -- paid engagements started
                notes       TEXT
            );
        """)
    log.info(f"Pipeline DB ready: {PIPELINE_DB}")


def seed_pipeline():
    """Seed initial high-priority targets if pipeline is empty."""
    with sqlite3.connect(PIPELINE_DB) as conn:
        count = conn.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
        if count > 0:
            return

        seed = [
            # --- Conferences ---
            ("MD&M West 2027",          "conference", "UBM/Informa",          None, "identified", 1,
             "Anaheim, Feb 2027. Largest device trade show on West Coast. Target: booth, speaking slot, corridor networking.",
             "Submit abstract for regulatory track", "2026-09-01"),
            ("Biocom Annual Conference", "conference", "Biocom",               None, "identified", 1,
             "San Diego, Q1 annually. Core SoCal network event. Biocom member access.",
             "Register + request exhibitor table as member", "2026-07-01"),
            ("RAPS Convergence 2026",    "conference", "RAPS",                  None, "identified", 1,
             "Sept/Oct 2026. Regulatory affairs professional society. Direct audience: RA leaders.",
             "Submit session proposal on AI-assisted regulatory strategy", "2026-06-15"),
            ("AdvaMed MedTech Conference","conference","AdvaMed",               None, "identified", 2,
             "DC, Oct 2026. National device industry. High brand-building value.",
             "Identify networking events, attend as delegate", "2026-07-01"),
            ("LSX World Congress",       "conference", "LSX",                   None, "identified", 2,
             "Life sciences dealmaking. Target: M&A advisory positioning.",
             "Apply for delegate pass", "2026-08-01"),

            # --- Podcast outreach ---
            ("The Medical Device Podcast","podcast", "Greenlight Guru",        "Jon Speer", "identified", 1,
             "Top-rated MedTech podcast. 20k+ listeners, QA/RA audience. Perfect fit.",
             "Draft guest pitch: AI-native regulatory consulting, Athena demo story", "2026-06-15"),
            ("MedTech Talk",              "podcast", "MedTech Talk Media",     None, "identified", 1,
             "SoCal-adjacent, industry insiders. Strong brand fit.",
             "Identify host, draft pitch email", "2026-06-20"),
            ("Regulatory Compliance Podcast","podcast","RCFM",                 None, "identified", 2,
             "Niche RA/QA compliance audience. Steven's expertise directly relevant.",
             "Research host, listener profile, draft pitch", "2026-06-25"),
            ("Emergo Podcast",            "podcast", "Emergo by UL",           None, "identified", 2,
             "Global regulatory focus. EU MDR and MDSAP episodes popular.",
             "Draft pitch emphasising EU MDR + AI analysis angle", "2026-07-01"),
            ("The MedTech Strategist",    "podcast", "MedTech Strategist",     None, "identified", 2,
             "Industry strategy and market access focus. More senior audience.",
             "Research and pitch after consulting line activates", "2026-09-01"),

            # --- Speaking engagements ---
            ("Biocom San Diego Chapter",  "speaking", "Biocom",               None, "identified", 1,
             "Monthly chapter events, panels, and workshops in San Diego.",
             "Contact chapter coordinator for guest speaker slot", "2026-06-20"),
            ("UC San Diego Extension",    "speaking", "UCSD",                 None, "identified", 1,
             "MedTech regulatory and business programs. Guest lecture opportunity.",
             "Contact program director for regulatory compliance course", "2026-07-01"),
            ("UC Irvine Merage School",   "speaking", "UCI",                  None, "identified", 2,
             "MBA healthcare track. MedTech startup consulting angle.",
             "Reach out to faculty lead for healthcare management", "2026-07-15"),
            ("FDA Workshop — San Diego",  "speaking", "FDA CDRH",             None, "identified", 2,
             "FDA hosts periodic regional workshops. Attending + Q&A = credibility.",
             "Monitor FDA calendar for San Diego/LA events", "2026-07-01"),
            ("RAPS SoCal Chapter",        "speaking", "RAPS",                 None, "identified", 1,
             "Regional RA chapter. Monthly meetings, direct peer audience.",
             "Join chapter, volunteer for program committee", "2026-06-15"),

            # --- Referral targets ---
            ("Biocom Member Network",     "referral", "Biocom",               None, "identified", 1,
             "600+ member companies in SoCal. Best source of warm introductions.",
             "Activate membership, attend 3 events before end of Q3", "2026-06-30"),
            ("Edwards Lifesciences Alumni","referral","Edwards Lifesciences",  None, "identified", 2,
             "Irvine-based. Large alumni network with QA/RA mobility.",
             "Identify 5 former Edwards colleagues for warm outreach", "2026-07-01"),
            ("Masimo Corp Network",        "referral","Masimo",               None, "identified", 2,
             "Irvine-based device OEM. RA professionals frequently consult externally.",
             "Identify 3 warm contacts", "2026-07-15"),

            # --- Regulatory clinic ---
            ("SoCal Regulatory Clinic",   "clinic", "Latitude MedTech",      None, "identified", 1,
             "Monthly free 45-min office hours at Biocom co-working space. Upsell to paid engagement.",
             "Book Biocom meeting room, draft clinic announcement, set date", "2026-07-01"),

            # --- Prospects ---
            ("SoCal MedTech Startups",    "prospect","Various — Series A/B", None, "identified", 1,
             "Primary ICP: VP/Director level at SoCal device startups needing 510(k) strategy.",
             "Build target list from Biocom directory + Crunchbase SoCal filter", "2026-06-30"),
        ]

        conn.executemany(
            "INSERT INTO targets (name,type,org,contact,status,priority,notes,next_action,next_date) VALUES (?,?,?,?,?,?,?,?,?)",
            seed
        )
        conn.commit()
        log.info(f"Seeded {len(seed)} pipeline targets.")


# ── Claude helpers ────────────────────────────────────────────────────────────

def _client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


SYSTEM_PROMPT = dedent(f"""
    You are the Marketing & Sales director for Latitude MedTech LLC — an AI-native
    MedTech and Pharma management consulting firm in Southern California (San Diego /
    Biocom corridor). The firm is in Alpha phase with two lines:
      1. Coaching (ACTIVE) — MedTech career coaching powered by the Athena AI agent.
      2. Consulting (GATED) — FDA, EU MDR, ISO 13485, MDSAP regulatory advisory.

    CEO: Steven Tran · steven.tran@latitudemedtech.com · linkedin.com/in/huanntran100
    Differentiator vs. Big 3 AI (Lilli, GENE): interactive reasoning with voice as the
    primary interface; 50-year regulatory knowledge base; no 6-month minimums.

    Marketing mandate: GUERILLA ONLY. Saturated channels (LinkedIn feed ads,
    Instagram, YouTube, Google Ads) are explicitly off-limits. Win through:
      - Podcast circuit (The Medical Device Podcast, MedTech Talk, RCFM, Emergo) — guest only, no ads
      - MedTech Meridian Substack newsletter — thought leadership, not promotion
      - FDA docket comments submitted as "Latitude MedTech LLC" — public credibility at zero cost
      - Warm direct email (NOT cold LinkedIn) to QA/RA Directors at SoCal startups
      - Speaking engagements (Biocom SD chapters, RAPS SoCal, UCSD/UCI) — local only, comped entry
      - Referral network activation via existing Biocom membership
      - Regulatory Clinic model — virtual-first (Zoom), local in-person only when explicitly requested
      - Conference corridors (Biocom SD, RAPS SoCal) — attend only if already local, never pay for booths

    BUDGET & MOBILITY CONSTRAINTS — Alpha phase, non-negotiable:
      Remote-first: The backbone of every plan must be zero-travel tactics (Substack posts,
      podcast outreach emails, FDA docket comments, warm email sequences, Zoom clinics).
      These require only Steven's time and the tools already in use.

      Local ceiling: In-person tactics are strictly limited to San Diego and North OC
      (max 45-minute drive from SD). Acceptable local venues: Biocom San Diego, RAPS SoCal
      Chapter, UCSD Extension, UCI Merage, Torrey Pines / UTC-area co-working.

      Travel = Alpha hold: Any event requiring a flight or hotel (AdvaMed DC, J.P. Morgan SF,
      LSX London, MassBio Boston) is deferred until Phase 1 revenue is established.
      Do not recommend these in plans — flag them in a "Future pipeline" section only.

      Zero paid budget: No booth fees, no ad spend, no paid sponsorships, no PR agencies.
      Acceptable cost exceptions: Biocom membership (already paid), conference registration
      ≤$300 only if Steven is a confirmed speaker or panellist.

      Overhead ceiling: Every tactic must be executable by Steven alone in ≤2 hours/week
      aggregate. Do not recommend anything requiring hiring, contracting, or new tool setup.

    Tactic priority order (highest ROI per hour, lowest overhead):
      1. Substack MedTech Meridian post (publish existing draft) — 0 cost, 0 travel
      2. Podcast guest pitch email (1 email, 30 min prep) — 0 cost, 0 travel
      3. FDA docket comment (1-2 hours research + write) — 0 cost, 0 travel
      4. Warm email outreach (personalised, 3-5 targets/week) — 0 cost, 0 travel
      5. Virtual Regulatory Clinic / Zoom office hours — 0 cost, 0 travel
      6. RAPS SoCal or Biocom SD chapter event (attend, not sponsor) — low cost, local
      7. UCSD/UCI guest lecture (speaking slot, comped) — low cost, local
      8. In-person Regulatory Clinic at Biocom SD co-working — low cost, local

    Hard rules:
      - No fabricated statistics or testimonials
      - All client outputs require Steven's review before sending
      - Consulting advisory is gated — do not offer until non-compete cleared + RAC engaged
      - Disclaimer on all content: educational purposes, not regulatory advice (Alpha phase)
      - Today's date: {CURRENT_DATE}
""").strip()


def llm(messages: list, max_tokens: int = 4000) -> str:
    client = _client()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return resp.content[0].text.strip()


# ── Pipeline helpers ──────────────────────────────────────────────────────────

def get_pipeline_summary() -> str:
    with sqlite3.connect(PIPELINE_DB) as conn:
        rows = conn.execute("""
            SELECT type, status, COUNT(*) as n
            FROM targets
            GROUP BY type, status
            ORDER BY type, status
        """).fetchall()
        high = conn.execute("""
            SELECT name, type, next_action, next_date
            FROM targets
            WHERE priority = 1 AND status != 'converted' AND status != 'closed'
            ORDER BY next_date
            LIMIT 10
        """).fetchall()

    lines = ["=== Pipeline Summary ===\n"]
    current_type = None
    for t, s, n in rows:
        if t != current_type:
            lines.append(f"\n[{t.upper()}]")
            current_type = t
        lines.append(f"  {s:<16}  {n}")

    lines.append("\n=== High-Priority Next Actions ===")
    for name, typ, action, next_date in high:
        lines.append(f"  [{next_date}]  {name} ({typ})")
        lines.append(f"             → {action}")

    return "\n".join(lines)


def update_target_status(target_name: str, status: str, notes: str = ""):
    with sqlite3.connect(PIPELINE_DB) as conn:
        conn.execute(
            "UPDATE targets SET status=?, notes=COALESCE(notes,'') || '\n' || ?, updated_at=date('now') WHERE name LIKE ?",
            (status, f"[{CURRENT_DATE}] {notes}", f"%{target_name}%")
        )
        conn.commit()
    log.info(f"Updated '{target_name}' → {status}")


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_plan() -> str:
    """Generate the 30-60-90 day guerilla marketing plan."""
    pipeline = get_pipeline_summary()
    prompt = dedent(f"""
        Generate a detailed 30-60-90 day guerilla marketing and sales plan for Latitude MedTech.
        Today is {CURRENT_DATE}. Phase 1A (coaching) needs its first paying clients within 90 days.

        Current pipeline state:
        {pipeline}

        CRITICAL CONSTRAINTS — every tactic in this plan must satisfy all three:
          1. MOBILITY: Remote (no driving) OR Local SD/OC only (≤45 min drive). No flights.
          2. COST: $0 (free) or ≤$300 (registration only if Steven is speaking). No booths.
          3. OVERHEAD: Executable by Steven alone in ≤2 hours/week additional time.

        Deliverable structure — McKinsey brief format, partner-signable:

        ## Executive Summary
        One sentence: the single quantified objective (e.g., "3 paid coaching clients by Day 90
        through podcast guest appearances, weekly Substack publishing, and warm email to 15
        SoCal QA/RA Directors — zero ad spend, zero travel.").

        ## Tactic Scorecard
        Table with columns: Tactic | Mobility | Cost | Weekly Hours | Expected Output | Priority
        Tag each row: Mobility = Remote / Local / [DEFERRED-TRAVEL]; Cost = $0 / $50 / $300+
        Sort by Expected Output / (Cost + Hours) — highest ROI first.
        Remote and free tactics must appear at the top. Any travel tactic = DEFERRED, not recommended.

        ## 30-Day Sprint (Days 1–30) — Foundation
        Focus: systems and first signals. Zero new tools, zero new costs.
        - Specific actions with day targets (e.g., "Day 7: send podcast pitch to Jon Speer at Greenlight Guru")
        - Each action: Mobility tag | Cost | Time estimate | Success criterion

        ## 60-Day Build (Days 31–60) — Momentum
        Focus: compounding the 30-day signals. Expect first inbound inquiry by Day 60.
        - Specific actions, same format as above
        - Name any local events to attend (Biocom SD or RAPS SoCal only)

        ## 90-Day Close (Days 61–90) — Conversion
        Focus: convert warm contacts to discovery calls, discovery calls to clients.
        - Conversion actions with specific messaging hooks
        - Gate criteria for Phase 2A revenue unlock

        ## Channel ROI Breakdown
        For each active channel: channel name | input (time/week) | expected output (leads/month)
        Remote channels listed first. No travel channels included.

        ## Future Pipeline (Alpha Hold)
        List of tactics explicitly held for post-revenue: travel conferences, booths, sponsorships.
        One sentence each explaining why held and what trigger unlocks them.

        ## Risks & Mitigation
        Top 2 risks with concrete 1-action responses.

        Be specific. Name real events with real dates, real people, real organisations.
        No vague language. Every bullet = specific action + specific metric.
    """).strip()

    print("\nGenerating 30-60-90 day guerilla marketing plan...")
    result = llm([{"role": "user", "content": prompt}], max_tokens=4000)

    out_path = MARKETING_DIR / f"plan_30_60_90_{CURRENT_DATE}.md"
    out_path.write_text(
        f"---\ntitle: Latitude MedTech — Guerilla Marketing Plan\ndate: {CURRENT_DATE}\ntype: marketing-plan\n---\n\n{result}",
        encoding="utf-8"
    )
    log.info(f"Plan saved: {out_path}")
    if _mem:
        _mem.submit_for_review("marketing_agent", "plan", f"30-60-90 Marketing Plan — {CURRENT_DATE}", str(out_path))
    return result


def cmd_brief() -> str:
    """Generate this week's marketing brief."""
    pipeline = get_pipeline_summary()
    prompt = dedent(f"""
        Generate a weekly marketing brief for Latitude MedTech. Today is {CURRENT_DATE}.

        Pipeline state:
        {pipeline}

        Brief format (one page max, MedTechDive register):
        - Week in focus: 3 specific actions for this week — remote-first (no driving unless local SD/OC)
        - Content to publish: one Substack topic with a specific contrarian or data-backed claim
        - Outreach targets: 2–3 specific people or venues with exact ask and exact email hook
          (remote channels only: podcast pitch, warm email, FDA docket, Zoom clinic)
        - Local event on radar (SD/OC only, ≤$300, skip if none this week): one prep action
        - KPI pulse: outreach sent / responses / meetings booked this week vs last (use 0 if no data)
        - Flag: one risk or blocker with a single concrete response action

        Constraint check: before finalising, confirm every recommended action is either (a) remote/digital
        or (b) local San Diego/OC only. Remove any tactic requiring a flight, hotel, or booth fee.
        No motivational filler. Every line = specific action or specific number.
        Label: LATITUDE MEDTECH — WEEKLY MARKETING BRIEF · {CURRENT_DATE}
    """).strip()

    print("\nGenerating weekly marketing brief...")
    result = llm([{"role": "user", "content": prompt}])

    out_path = MARKETING_DIR / f"brief_{CURRENT_DATE}.md"
    out_path.write_text(
        f"---\ntitle: Weekly Marketing Brief\ndate: {CURRENT_DATE}\ntype: marketing-brief\n---\n\n{result}",
        encoding="utf-8"
    )
    log.info(f"Brief saved: {out_path}")
    if _mem:
        _mem.submit_for_review("marketing_agent", "brief", f"Marketing Brief — {CURRENT_DATE}", str(out_path))
    return result


def cmd_outreach(target: str) -> str:
    """Generate personalized outreach copy for a specific target."""
    with sqlite3.connect(PIPELINE_DB) as conn:
        row = conn.execute(
            "SELECT name, type, org, contact, notes FROM targets WHERE name LIKE ? OR org LIKE ?",
            (f"%{target}%", f"%{target}%")
        ).fetchone()

    context = ""
    if row:
        name, typ, org, contact, notes = row
        context = f"Target in pipeline: {name} ({typ}) at {org}. Contact: {contact or 'unknown'}. Notes: {notes}"
    else:
        context = f"Target: {target} (not yet in pipeline)"

    prompt = dedent(f"""
        Write a professional outreach message for the following Latitude MedTech target.

        {context}

        Requirements:
        - Email format (subject line + body)
        - Subject: specific, value-leading, not salesy — max 60 chars
        - Body: 4–6 short paragraphs. Lead with THEIR context, not ours.
        - Make a single specific ask (30-min call OR podcast invite OR event collab)
        - Tone: peer-to-peer, not vendor pitch. Steven reaches out as a fellow practitioner.
        - Do NOT: use buzzwords, generic openers, or anything that reads like a template
        - Close with: Steven Tran, Managing Partner — Latitude MedTech LLC
        - Add a P.S. with one specific, surprising industry insight related to their work
        - Max 250 words body

        Then write a 1-sentence follow-up for 7 days later if no response.
    """).strip()

    print(f"\nGenerating outreach copy for: {target}")
    result = llm([{"role": "user", "content": prompt}])

    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in target)[:40]
    out_path = OUTREACH_DIR / f"outreach_{safe_name}_{CURRENT_DATE}.md"
    out_path.write_text(
        f"---\ntarget: {target}\ndate: {CURRENT_DATE}\ntype: outreach\nstatus: draft\n---\n\n{result}",
        encoding="utf-8"
    )
    log.info(f"Outreach saved: {out_path}")
    return result


def cmd_events() -> str:
    """Generate a SoCal MedTech events calendar and action list."""
    prompt = dedent(f"""
        Generate a prioritised calendar of MedTech and Pharma industry events relevant to
        Latitude MedTech LLC for the next 18 months (from {CURRENT_DATE}).
        Focus: Southern California, regulatory affairs, device industry, career/professional.

        Include for each event:
        - Event name, organiser, location, typical month/date
        - Why it matters for Latitude MedTech (specific audience, opportunity)
        - Recommended role: attend | speak | sponsor | exhibit | table
        - Lead time for action (e.g., "abstract deadline 6 months out")

        Channels in scope:
          MD&M West, BIOMEDevice, Biocom events, RAPS Convergence, AdvaMed MedTech Conference,
          LSX World, FDLI Annual Conference, ASQ Biomedical Division, RAPS SoCal Chapter,
          Biocom San Diego Chapter, UC San Diego Extension events, UCI Merage Health programs,
          FDA regional workshops (CDRH), MassBio (for East Coast reach), J.P. Morgan HC Conference

        Format as a table then a prioritised action list.
        No invented dates — flag "confirm dates" where unknown.
        Label: LATITUDE MEDTECH — EVENTS CALENDAR · {CURRENT_DATE}
    """).strip()

    print("\nGenerating MedTech events calendar...")
    result = llm([{"role": "user", "content": prompt}], max_tokens=4000)

    out_path = MARKETING_DIR / f"events_calendar_{CURRENT_DATE}.md"
    out_path.write_text(
        f"---\ntitle: MedTech Events Calendar\ndate: {CURRENT_DATE}\ntype: events\n---\n\n{result}",
        encoding="utf-8"
    )
    log.info(f"Events calendar saved: {out_path}")
    return result


def cmd_scorecard() -> str:
    """Print a KPI scorecard against marketing targets."""
    with sqlite3.connect(PIPELINE_DB) as conn:
        total     = conn.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
        contacted = conn.execute("SELECT COUNT(*) FROM targets WHERE status != 'identified'").fetchone()[0]
        converted = conn.execute("SELECT COUNT(*) FROM targets WHERE status = 'converted'").fetchone()[0]
        meetings  = conn.execute("SELECT COUNT(*) FROM targets WHERE status = 'in_discussion'").fetchone()[0]
        by_type   = conn.execute("""
            SELECT type, COUNT(*) FROM targets GROUP BY type
        """).fetchall()
        recent    = conn.execute("""
            SELECT description, outcome, logged_at FROM activities
            ORDER BY logged_at DESC LIMIT 10
        """).fetchall()

    lines = [
        f"LATITUDE MEDTECH — MARKETING SCORECARD  ·  {CURRENT_DATE}",
        "=" * 60,
        f"  Total targets identified:    {total:>4}",
        f"  Contacted / in motion:       {contacted:>4}  ({100*contacted//max(total,1)}%)",
        f"  In discussion / meetings:    {meetings:>4}",
        f"  Converted to clients:        {converted:>4}",
        "",
        "  Phase 1A target: 3 paid coaching clients by Day 90",
        "",
        "  Pipeline by channel:",
    ]
    for typ, cnt in by_type:
        lines.append(f"    {typ:<18}  {cnt}")

    if recent:
        lines.append("\n  Recent activity:")
        for desc, outcome, ts in recent:
            lines.append(f"    [{ts[:10]}]  {desc}")
            if outcome:
                lines.append(f"               → {outcome}")

    scorecard = "\n".join(lines)
    print(scorecard)
    return scorecard


def cmd_pipeline() -> str:
    """Print and return the pipeline summary."""
    summary = get_pipeline_summary()
    print(summary)
    return summary


def cmd_learn():
    """Ingest new marketing intelligence into the knowledge base."""
    kb_path = KB_DIR / "marketing"
    kb_path.mkdir(parents=True, exist_ok=True)

    prompt = dedent(f"""
        You are building the marketing knowledge base for Latitude MedTech LLC.

        Generate a comprehensive intelligence brief on:
        1. Top 10 MedTech podcasts by audience size and relevance to RA/QA professionals (2025-2026)
        2. Top 5 SoCal MedTech Biocom-adjacent co-working and event spaces for in-person clinics
        3. Key SoCal MedTech influencers and thought leaders (non-LinkedIn — podcast hosts, newsletter authors, Substack writers, conference organizers)
        4. FDA docket participation guide: how to submit comments as a consulting firm, which active dockets matter for device companies in 2026
        5. Guerilla marketing playbook: 5 tactics that work for boutique MedTech consultancies (with real examples, not generic advice)

        Format as structured markdown knowledge base entries.
        Every claim must have a source (URL, publication name, or "verify: [specific source]").
        Date: {CURRENT_DATE}
    """).strip()

    print("\nIngesting marketing intelligence...")
    result = llm([{"role": "user", "content": prompt}], max_tokens=4000)

    out_path = kb_path / f"marketing_intelligence_{CURRENT_DATE}.md"
    out_path.write_text(result, encoding="utf-8")
    log.info(f"Marketing KB entry saved: {out_path}")
    print(f"Saved: {out_path}")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\nLatitude MedTech — Marketing & Sales Agent")
    print("=" * 50)

    parser = argparse.ArgumentParser(description="Latitude MedTech Marketing Agent")
    parser.add_argument("mode",           nargs="?", default="brief",
                        choices=["brief","learn"], help="Default mode")
    parser.add_argument("--plan",         action="store_true", help="Generate 30-60-90 day plan")
    parser.add_argument("--outreach",     metavar="TARGET",   help="Generate outreach copy for target")
    parser.add_argument("--pipeline",     action="store_true", help="Show pipeline summary")
    parser.add_argument("--events",       action="store_true", help="Events calendar")
    parser.add_argument("--scorecard",    action="store_true", help="KPI scorecard")
    parser.add_argument("--update",       nargs=2, metavar=("TARGET","STATUS"),
                        help="Update target status: --update 'Target Name' contacted")
    args = parser.parse_args()

    init_db()
    seed_pipeline()

    if args.plan:
        print(cmd_plan())
    elif args.outreach:
        print(cmd_outreach(args.outreach))
    elif args.pipeline:
        cmd_pipeline()
    elif args.events:
        print(cmd_events())
    elif args.scorecard:
        cmd_scorecard()
    elif args.update:
        update_target_status(args.update[0], args.update[1])
    elif args.mode == "learn":
        cmd_learn()
    else:
        # Default: weekly brief
        print(cmd_brief())


if __name__ == "__main__":
    main()
