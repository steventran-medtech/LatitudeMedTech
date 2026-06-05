"""
Latitude MedTech — HR Agent
=============================
Tracks the health, learning velocity, and error rate of all other agents.
Acts like a Chief People Officer for the AI firm:

  - GREEN  : Active, learning regularly, low error rate
  - YELLOW : Not learned in 7+ days OR 3+ errors in last 7 days
  - RED    : Not learned in 14+ days OR 5+ errors OR flagged by CAPA

Outputs:
  - Per-agent scorecard saved to ~/Athena/ops/hr/
  - Flags surfaced in the dashboard and via voice
  - Recommendations for which agents need updates / retraining

Usage:
    python hr_agent.py              # full review
    python hr_agent.py --agent rag  # single agent
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

from pathconfig import ENV_FILE, AGENTS_DIR, OPS_DIR, LOGS_DIR
load_dotenv(ENV_FILE)
sys.path.insert(0, str(AGENTS_DIR))

from memory import Memory

HR_DIR  = OPS_DIR / 'hr'
LOG_DIR = LOGS_DIR
HR_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "hr_agent.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("hr_agent")

mem = Memory()

# ── Agent roster ──────────────────────────────────────────────────────────────

AGENTS = {
    "content":          {"label": "Content Agent",          "tier": "Manager",          "required_weekly_learning": 3},
    "briefing":         {"label": "Briefing Agent",          "tier": "Senior Associate", "required_weekly_learning": 5},
    "iso":              {"label": "ISO Coach Agent",         "tier": "Manager",          "required_weekly_learning": 3},
    "coaching":         {"label": "Coaching Brief Agent",    "tier": "Manager",          "required_weekly_learning": 3},
    "fda":              {"label": "FDA Agent",               "tier": "Manager",          "required_weekly_learning": 4},
    "rag":              {"label": "RAG Ingestion Agent",     "tier": "Senior Associate", "required_weekly_learning": 2},
    "consulting":       {"label": "Consulting Agent",        "tier": "Senior Manager",   "required_weekly_learning": 5},
    "ma_intelligence":  {"label": "M&A Intelligence Agent",  "tier": "Senior Manager",   "required_weekly_learning": 5},
    "voice_bridge":     {"label": "Voice Assistant",         "tier": "Associate",        "required_weekly_learning": 1},
}

# ── Flag thresholds ───────────────────────────────────────────────────────────

YELLOW_LEARNING_DAYS  = 7    # no new learning in 7d → yellow
RED_LEARNING_DAYS     = 14   # no new learning in 14d → red
YELLOW_ERROR_COUNT    = 3    # 3 errors in 7d → yellow
RED_ERROR_COUNT       = 5    # 5 errors in 7d → red
CAPA_FLAG_COUNT       = 3    # 3+ CAPA events ever → auto-flag

# ── Scorecard builder ─────────────────────────────────────────────────────────

def _days_since(ts_str):
    """Returns days since timestamp, or None if timestamp is missing."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str)
        return (datetime.now() - dt).days
    except Exception:
        return None


def score_agent(agent_name: str, profile: dict) -> dict:
    now       = datetime.now()
    last_ll   = mem.get_last_learning(agent_name)
    ll_ts     = last_ll["timestamp"] if last_ll else None
    ll_days   = _days_since(ll_ts)
    lr_ts     = mem.get_agent_last_run(agent_name)
    lr_days   = _days_since(lr_ts)
    errors_7d = mem.get_agent_error_count(agent_name, days=7)
    learn_7d  = mem.get_learning_stats(agent=agent_name, days=7)
    items_7d  = learn_7d[0]["items"] if learn_7d else 0
    required  = profile["required_weekly_learning"]
    acc       = mem.get_skill_accumulation(agent_name)   # all-time skill/KB capital

    # ── Determine flag status ─────────────────────────────────────────────────
    flag   = "green"
    reason = []

    if errors_7d >= RED_ERROR_COUNT:
        flag = "red"
        reason.append(f"{errors_7d} errors in last 7 days (threshold: {RED_ERROR_COUNT})")

    # ll_days is None when agent has never learned — treat as RED
    if ll_days is None:
        flag = "red"
        reason.append("No learning activity on record — run agent_learning.py")
    elif ll_days >= RED_LEARNING_DAYS:
        flag = "red"
        reason.append(f"No new learning in {ll_days}d (threshold: {RED_LEARNING_DAYS}d)")

    if flag != "red":
        if errors_7d >= YELLOW_ERROR_COUNT:
            flag = "yellow"
            reason.append(f"{errors_7d} errors in last 7 days (threshold: {YELLOW_ERROR_COUNT})")
        if ll_days is not None and ll_days >= YELLOW_LEARNING_DAYS:
            flag = "yellow"
            reason.append(f"No new learning in {ll_days}d (threshold: {YELLOW_LEARNING_DAYS}d)")
        if items_7d < required:
            if flag == "green":   flag = "yellow"
            reason.append(f"Learning below target: {items_7d}/{required} items this week")

    # CAPA check
    capa_count = mem.conn.execute(
        "SELECT COUNT(*) as n FROM events WHERE agent=? AND action LIKE '%capa%'",
        (agent_name,)
    ).fetchone()["n"]
    if capa_count >= CAPA_FLAG_COUNT:
        if flag == "green": flag = "yellow"
        reason.append(f"{capa_count} CAPA events on record")

    flag_reason = "; ".join(reason) if reason else "All metrics healthy"

    # ── Recommendation ────────────────────────────────────────────────────────
    recs = []
    if flag == "red":
        recs.append("PRIORITY: Immediate review and optimization required.")
        if errors_7d >= RED_ERROR_COUNT:
            recs.append("Run RCA — high error rate indicates systemic prompt or data issue.")
        if ll_days is None or ll_days >= RED_LEARNING_DAYS:
            recs.append("Force a learning run: python agent_learning.py --agent " + agent_name)
    elif flag == "yellow":
        if ll_days is not None and ll_days >= YELLOW_LEARNING_DAYS:
            recs.append("Schedule a learning run within 48 hours.")
        if errors_7d >= YELLOW_ERROR_COUNT:
            recs.append("Review recent error events and update agent system prompt if pattern found.")
        if items_7d < required:
            recs.append(f"Learning velocity low ({items_7d}/{required}/wk) — check source feed availability.")
    else:
        recs.append("Agent healthy. No action required.")

    scorecard = {
        "agent":            agent_name,
        "label":            profile["label"],
        "tier":             profile["tier"],
        "flag":             flag,
        "flag_reason":      flag_reason,
        "recommendations":  recs,
        "metrics": {
            "last_learning":          ll_ts,
            "days_since_learning":    ll_days,   # None when never learned
            "last_learning_item":     last_ll["title"] if last_ll else None,
            "last_run":               lr_ts,
            "days_since_run":         lr_days,   # None when never run
            "errors_7d":              errors_7d,
            "learning_items_7d":      items_7d,
            "learning_target_weekly": required,
            "accumulated_items":      acc["total_items"],
            "accumulated_chunks":     acc["total_chunks"],
            "accumulated_domains":    len(acc["domains"]),
        },
        "evaluated_at": now.isoformat(),
    }

    # Persist to agent_health table
    mem.upsert_agent_health(
        agent_name,
        last_run=lr_ts,
        last_learning=ll_ts,
        error_count_7d=errors_7d,
        learning_7d=items_7d,
        flag_status=flag,
        flag_reason=flag_reason,
    )

    return scorecard


# ── Report writer ─────────────────────────────────────────────────────────────

def write_report(scorecards: list) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = HR_DIR / f"{date_str}_hr_report.md"

    reds    = [s for s in scorecards if s["flag"] == "red"]
    yellows = [s for s in scorecards if s["flag"] == "yellow"]
    greens  = [s for s in scorecards if s["flag"] == "green"]

    lines = [
        f"# HR Agent Report — {date_str}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Status:** {len(reds)} RED · {len(yellows)} YELLOW · {len(greens)} GREEN",
        "",
        "---",
        "",
    ]

    def _section(cards, heading, emoji):
        if not cards:
            return
        lines.append(f"## {emoji} {heading}")
        lines.append("")
        for s in cards:
            m = s["metrics"]
            lines.append(f"### {s['label']} (`{s['agent']}`)")
            lines.append(f"**Tier:** {s['tier']}  |  **Flag:** `{s['flag'].upper()}`")
            lines.append(f"**Reason:** {s['flag_reason']}")
            lines.append("")
            lines.append("**Metrics:**")
            lines.append(f"- Last learning: {m['last_learning_item'] or 'Never'} ({m['days_since_learning'] or '—'}d ago)")
            lines.append(f"- Learning this week: {m['learning_items_7d']} / {m['learning_target_weekly']} target")
            lines.append(f"- Accumulated skill/KB: {m['accumulated_items']} items, "
                         f"{m['accumulated_chunks']} chunks, {m['accumulated_domains']} domains (all-time)")
            lines.append(f"- Errors last 7 days: {m['errors_7d']}")
            lines.append(f"- Last active run: {m['days_since_run'] or '—'}d ago")
            lines.append("")
            lines.append("**Recommendations:**")
            for r in s["recommendations"]:
                lines.append(f"- {r}")
            lines.append("")

    _section(reds,    "Red — Immediate Action Required", "🔴")
    _section(yellows, "Yellow — Attention Needed",        "🟡")
    _section(greens,  "Green — Healthy",                  "🟢")

    lines += [
        "---",
        "",
        "## Summary for Steven",
        "",
        f"Total agents reviewed: **{len(scorecards)}**",
        f"Firm skill/KB capital: **{sum(s['metrics']['accumulated_items'] for s in scorecards)} items**, "
        f"**{sum(s['metrics']['accumulated_chunks'] for s in scorecards)} chunks** accumulated all-time "
        f"(detail in `SKILLS.md`).",
        "",
    ]
    if reds:
        lines.append(f"**ACTION REQUIRED:** {', '.join(s['label'] for s in reds)} need immediate attention.")
    if yellows:
        lines.append(f"**Monitor:** {', '.join(s['label'] for s in yellows)} are below target.")
    if not reds and not yellows:
        lines.append("All agents are healthy. No action required.")

    lines += [
        "",
        "---",
        "",
        "*DISCLAIMER: This report is generated by the Latitude MedTech HR Agent. "
        "Alpha — Steve Review Required.*",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def run_review(targets=None) -> list:
    targets = targets or list(AGENTS.keys())
    scorecards = []

    log.info("=" * 50)
    log.info("  Latitude MedTech — HR Agent Review")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 50)

    for name in targets:
        profile = AGENTS.get(name)
        if not profile:
            log.warning(f"Unknown agent: {name}")
            continue
        card = score_agent(name, profile)
        scorecards.append(card)
        flag_icon = {"green": "✓", "yellow": "!", "red": "✗"}[card["flag"]]
        log.info(f"  [{flag_icon}] {card['label']:<28} {card['flag'].upper():<8} {card['flag_reason'][:50]}")

    report_path = write_report(scorecards)
    log.info(f"\nReport saved: {report_path}")

    # Refresh the living skill/KB profiles so accumulation stays current.
    try:
        from skills_profile import generate as _gen_skills
        _gen_skills()
        log.info("Skill/KB profiles refreshed (knowledge_base/skills/ + SKILLS.md)")
    except Exception as e:
        log.warning(f"Skill profile refresh skipped: {e}")

    reds = [s for s in scorecards if s["flag"] == "red"]
    if reds:
        log.warning(f"\n⚠ RED AGENTS: {', '.join(s['agent'] for s in reds)}")
        log.warning("These agents require immediate review and optimization.")

    return scorecards


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", type=str, default="", help="Single agent to review")
    args = parser.parse_args()
    targets = [args.agent] if args.agent else None
    run_review(targets)


if __name__ == "__main__":
    main()
